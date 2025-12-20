"""
Iron Condor Strategy
铁鹰式策略

策略说明：
- 同时卖出虚值看涨和虚值看跌期权
- 同时买入更虚值的看涨和看跌期权作为保护
- 适合于预期标的价格在一定区间内波动的市场
- 收益来源：时间价值衰减和波动率下降
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from .base import Strategy, Position, Trade, OptionType, OrderSide
from ..pricing.black_scholes import calculate_greeks

logger = logging.getLogger(__name__)


class IronCondorStrategy(Strategy):
    """铁鹰式策略"""

    def __init__(
        self,
        name: str = "IronCondor",
        wing_width: float = 5.0,
        profit_target: float = 0.5,
        stop_loss: float = 2.0,
        min_credit: float = 0.5,
        min_days_to_expiry: int = 30,
        max_days_to_expiry: int = 60,
        target_delta_short_call: float = 0.20,
        target_delta_short_put: float = -0.20
    ):
        """
        初始化铁鹰式策略

        Args:
            name: 策略名称
            wing_width: 翼展宽度（行权价差，美元）
            profit_target: 利润目标（占最大利润比例）
            stop_loss: 止损比例（占收入保证金比例）
            min_credit: 最小收入（每份）
            min_days_to_expiry: 最小到期天数
            max_days_to_expiry: 最大到期天数
            target_delta_short_call: 目标卖出看涨期权Delta
            target_delta_short_put: 目标卖出看跌期权Delta
        """
        super().__init__(name)
        self.wing_width = wing_width
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.min_credit = min_credit
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.target_delta_short_call = target_delta_short_call
        self.target_delta_short_put = target_delta_short_put

    def generate_signals(
        self,
        market_data: Dict,
        **kwargs
    ) -> List[Position]:
        """
        生成铁鹰式交易信号

        Args:
            market_data: 市场数据，包含：
                - symbol: 标的代码
                - current_price: 当前价格
                - option_chain: 期权链数据（DataFrame）
                - iv_percentile: IV百分位
                - risk_free_rate: 无风险利率

        Returns:
            List[Position]: 建议的持仓列表
        """
        symbol = market_data.get("symbol")
        current_price = market_data.get("current_price")
        option_chain = market_data.get("option_chain")
        iv_percentile = market_data.get("iv_percentile", 50)
        risk_free_rate = market_data.get("risk_free_rate", 0.05)

        if option_chain is None or option_chain.empty:
            logger.warning(f"No option chain data for {symbol}")
            return []

        # 检查IV是否在合适的范围
        if iv_percentile < 30:
            logger.info(f"IV percentile too low ({iv_percentile}), skipping {symbol}")
            return []

        # 选择合适的到期日
        suitable_options = self._filter_by_expiry(option_chain)
        if suitable_options.empty:
            logger.warning(f"No suitable expiry dates for {symbol}")
            return []

        # 为每个到期日寻找铁鹰式组合
        positions = []
        for expiry_date in suitable_options['expiry_date'].unique():
            expiry_options = suitable_options[suitable_options['expiry_date'] == expiry_date]

            # 构建铁鹰式
            position = self._build_iron_condor(
                symbol=symbol,
                current_price=current_price,
                options=expiry_options,
                expiry_date=expiry_date,
                risk_free_rate=risk_free_rate
            )

            if position:
                positions.append(position)

        return positions

    def _filter_by_expiry(self, option_chain: pd.DataFrame) -> pd.DataFrame:
        """
        根据到期日过滤期权

        Args:
            option_chain: 期权链数据

        Returns:
            DataFrame: 过滤后的期权数据
        """
        # 假设option_chain包含'days_to_expiry'列
        if 'days_to_expiry' not in option_chain.columns:
            # 如果没有，需要计算
            from datetime import datetime
            today = datetime.now()
            option_chain['days_to_expiry'] = option_chain['expiry_date'].apply(
                lambda x: (datetime.strptime(x, "%Y-%m-%d") - today).days
            )

        return option_chain[
            (option_chain['days_to_expiry'] >= self.min_days_to_expiry) &
            (option_chain['days_to_expiry'] <= self.max_days_to_expiry)
        ]

    def _build_iron_condor(
        self,
        symbol: str,
        current_price: float,
        options: pd.DataFrame,
        expiry_date: str,
        risk_free_rate: float
    ) -> Optional[Position]:
        """
        构建铁鹰式组合

        Args:
            symbol: 标的代码
            current_price: 当前价格
            options: 期权数据
            expiry_date: 到期日
            risk_free_rate: 无风险利率

        Returns:
            Position: 铁鹰式持仓，如果无法构建返回None
        """
        # 分离看涨和看跌期权
        calls = options[options['option_type'] == 'CALL'].copy()
        puts = options[options['option_type'] == 'PUT'].copy()

        if calls.empty or puts.empty:
            return None

        # 寻找合适的卖出看涨期权（OTM，Delta约0.20）
        short_call = self._find_option_by_delta(
            calls,
            current_price,
            self.target_delta_short_call,
            expiry_date,
            risk_free_rate,
            "CALL"
        )

        # 寻找合适的卖出看跌期权（OTM，Delta约-0.20）
        short_put = self._find_option_by_delta(
            puts,
            current_price,
            self.target_delta_short_put,
            expiry_date,
            risk_free_rate,
            "PUT"
        )

        if short_call is None or short_put is None:
            return None

        # 寻找保护性买入看涨期权（更高行权价）
        long_call_strike = short_call['strike'] + self.wing_width
        long_call = calls[calls['strike'] >= long_call_strike].iloc[0] if len(
            calls[calls['strike'] >= long_call_strike]) > 0 else None

        # 寻找保护性买入看跌期权（更低行权价）
        long_put_strike = short_put['strike'] - self.wing_width
        long_put = puts[puts['strike'] <= long_put_strike].iloc[-1] if len(
            puts[puts['strike'] <= long_put_strike]) > 0 else None

        if long_call is None or long_put is None:
            return None

        # 计算净收入
        net_credit = (
            short_call['bid'] +
            short_put['bid'] -
            long_call['ask'] -
            long_put['ask']
        )

        if net_credit < self.min_credit:
            logger.info(f"Net credit too low: {net_credit}")
            return None

        # 创建持仓
        position = Position(symbol=symbol)

        # 添加四条腿
        # 1. 卖出看涨
        position.add_trade(Trade(
            symbol=short_call['option_code'],
            option_type=OptionType.CALL,
            strike=short_call['strike'],
            expiry=expiry_date,
            side=OrderSide.SELL,
            quantity=1,
            price=short_call['bid']
        ))

        # 2. 买入看涨（保护）
        position.add_trade(Trade(
            symbol=long_call['option_code'],
            option_type=OptionType.CALL,
            strike=long_call['strike'],
            expiry=expiry_date,
            side=OrderSide.BUY,
            quantity=1,
            price=long_call['ask']
        ))

        # 3. 卖出看跌
        position.add_trade(Trade(
            symbol=short_put['option_code'],
            option_type=OptionType.PUT,
            strike=short_put['strike'],
            expiry=expiry_date,
            side=OrderSide.SELL,
            quantity=1,
            price=short_put['bid']
        ))

        # 4. 买入看跌（保护）
        position.add_trade(Trade(
            symbol=long_put['option_code'],
            option_type=OptionType.PUT,
            strike=long_put['strike'],
            expiry=expiry_date,
            side=OrderSide.BUY,
            quantity=1,
            price=long_put['ask']
        ))

        logger.info(f"Built Iron Condor for {symbol}, net credit: ${net_credit:.2f}")
        return position

    def _find_option_by_delta(
        self,
        options: pd.DataFrame,
        spot_price: float,
        target_delta: float,
        expiry_date: str,
        risk_free_rate: float,
        option_type: str
    ) -> Optional[pd.Series]:
        """
        根据Delta值寻找期权

        Args:
            options: 期权数据
            spot_price: 现货价格
            target_delta: 目标Delta
            expiry_date: 到期日
            risk_free_rate: 无风险利率
            option_type: 期权类型

        Returns:
            Series: 期权数据，如果没找到返回None
        """
        from datetime import datetime

        # 计算到期时间（年）
        today = datetime.now()
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        time_to_expiry = (expiry - today).days / 365.0

        if time_to_expiry <= 0:
            return None

        # 为每个期权计算Delta
        deltas = []
        for _, option in options.iterrows():
            if 'implied_volatility' in option and pd.notna(option['implied_volatility']):
                iv = option['implied_volatility']
            else:
                iv = 0.3  # 默认IV

            greeks = calculate_greeks(
                S=spot_price,
                K=option['strike'],
                T=time_to_expiry,
                r=risk_free_rate,
                sigma=iv,
                option_type=option_type.lower()
            )
            deltas.append(greeks['delta'])

        options = options.copy()
        options['delta'] = deltas

        # 找到最接近目标Delta的期权
        options['delta_diff'] = np.abs(options['delta'] - target_delta)
        best_option = options.loc[options['delta_diff'].idxmin()]

        return best_option

    def check_exit_conditions(
        self,
        position: Position,
        market_data: Dict
    ) -> bool:
        """
        检查铁鹰式平仓条件

        Args:
            position: 当前持仓
            market_data: 市场数据，包含当前期权价格

        Returns:
            bool: 是否应该平仓
        """
        current_prices = market_data.get("option_prices", {})

        # 计算当前盈亏
        current_pnl = position.get_current_pnl(current_prices)
        max_profit = position.get_max_profit()
        max_loss = position.get_max_loss()

        # 利润目标：达到最大利润的50%
        if current_pnl >= max_profit * self.profit_target:
            logger.info(f"Profit target reached: {current_pnl:.2f} >= {max_profit * self.profit_target:.2f}")
            return True

        # 止损：亏损超过收入的2倍
        if current_pnl <= -abs(max_profit) * self.stop_loss:
            logger.warning(f"Stop loss triggered: {current_pnl:.2f} <= {-abs(max_profit) * self.stop_loss:.2f}")
            return True

        # 到期前几天平仓
        from datetime import datetime
        if position.trades:
            expiry_str = position.trades[0].expiry
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            days_to_expiry = (expiry_date - datetime.now()).days

            if days_to_expiry <= 7:
                logger.info(f"Closing position near expiry: {days_to_expiry} days left")
                return True

        return False
