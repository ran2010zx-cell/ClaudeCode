"""
Credit Spread Strategy
信用价差策略

策略说明：
- 卖出虚值期权，同时买入更虚值的期权作为保护
- 可以是看涨价差（Bull Put Spread）或看跌价差（Bear Call Spread）
- 收益来源：时间价值衰减和波动率下降
- 风险有限，收益也有限
"""

import logging
from typing import Dict, List, Optional
import pandas as pd
import numpy as np

from .base import Strategy, Position, Trade, OptionType, OrderSide
from ..pricing.black_scholes import calculate_greeks

logger = logging.getLogger(__name__)


class CreditSpreadStrategy(Strategy):
    """信用价差策略"""

    def __init__(
        self,
        name: str = "CreditSpread",
        spread_width: float = 5.0,
        profit_target: float = 0.5,
        stop_loss: float = 2.0,
        min_credit: float = 0.3,
        min_days_to_expiry: int = 30,
        max_days_to_expiry: int = 60,
        target_delta: float = 0.20,
        spread_type: str = "put"  # "put" for bull put spread, "call" for bear call spread
    ):
        """
        初始化信用价差策略

        Args:
            name: 策略名称
            spread_width: 价差宽度（行权价差）
            profit_target: 利润目标（占最大利润比例）
            stop_loss: 止损比例
            min_credit: 最小收入（每份）
            min_days_to_expiry: 最小到期天数
            max_days_to_expiry: 最大到期天数
            target_delta: 目标Delta（卖出期权）
            spread_type: 价差类型（"put"或"call"）
        """
        super().__init__(name)
        self.spread_width = spread_width
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.min_credit = min_credit
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.target_delta = target_delta
        self.spread_type = spread_type.lower()

    def generate_signals(
        self,
        market_data: Dict,
        **kwargs
    ) -> List[Position]:
        """
        生成信用价差交易信号

        Args:
            market_data: 市场数据

        Returns:
            List[Position]: 建议的持仓列表
        """
        symbol = market_data.get("symbol")
        current_price = market_data.get("current_price")
        option_chain = market_data.get("option_chain")
        risk_free_rate = market_data.get("risk_free_rate", 0.05)

        if option_chain is None or option_chain.empty:
            logger.warning(f"No option chain data for {symbol}")
            return []

        # 过滤到期日
        suitable_options = self._filter_by_expiry(option_chain)
        if suitable_options.empty:
            return []

        positions = []
        for expiry_date in suitable_options['expiry_date'].unique():
            expiry_options = suitable_options[suitable_options['expiry_date'] == expiry_date]

            position = self._build_credit_spread(
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
        """过滤到期日"""
        from datetime import datetime

        if 'days_to_expiry' not in option_chain.columns:
            today = datetime.now()
            option_chain['days_to_expiry'] = option_chain['expiry_date'].apply(
                lambda x: (datetime.strptime(x, "%Y-%m-%d") - today).days
            )

        return option_chain[
            (option_chain['days_to_expiry'] >= self.min_days_to_expiry) &
            (option_chain['days_to_expiry'] <= self.max_days_to_expiry)
        ]

    def _build_credit_spread(
        self,
        symbol: str,
        current_price: float,
        options: pd.DataFrame,
        expiry_date: str,
        risk_free_rate: float
    ) -> Optional[Position]:
        """
        构建信用价差组合

        Args:
            symbol: 标的代码
            current_price: 当前价格
            options: 期权数据
            expiry_date: 到期日
            risk_free_rate: 无风险利率

        Returns:
            Position: 信用价差持仓
        """
        if self.spread_type == "put":
            option_type = "PUT"
            target_delta = -abs(self.target_delta)  # Put的Delta是负数
        else:
            option_type = "CALL"
            target_delta = abs(self.target_delta)  # Call的Delta是正数

        # 筛选对应类型的期权
        type_options = options[options['option_type'] == option_type].copy()

        if type_options.empty:
            return None

        # 找到卖出期权
        short_option = self._find_option_by_delta(
            type_options,
            current_price,
            target_delta,
            expiry_date,
            risk_free_rate,
            option_type
        )

        if short_option is None:
            return None

        # 找到买入期权（保护）
        if self.spread_type == "put":
            # Bull Put Spread: 买入更低行权价的Put
            long_strike = short_option['strike'] - self.spread_width
            long_option = type_options[type_options['strike'] <= long_strike].iloc[-1] if len(
                type_options[type_options['strike'] <= long_strike]) > 0 else None
        else:
            # Bear Call Spread: 买入更高行权价的Call
            long_strike = short_option['strike'] + self.spread_width
            long_option = type_options[type_options['strike'] >= long_strike].iloc[0] if len(
                type_options[type_options['strike'] >= long_strike]) > 0 else None

        if long_option is None:
            return None

        # 计算净收入
        net_credit = short_option['bid'] - long_option['ask']

        if net_credit < self.min_credit:
            logger.info(f"Net credit too low: {net_credit}")
            return None

        # 创建持仓
        position = Position(symbol=symbol)

        # 卖出期权
        position.add_trade(Trade(
            symbol=short_option['option_code'],
            option_type=OptionType(option_type),
            strike=short_option['strike'],
            expiry=expiry_date,
            side=OrderSide.SELL,
            quantity=1,
            price=short_option['bid']
        ))

        # 买入期权（保护）
        position.add_trade(Trade(
            symbol=long_option['option_code'],
            option_type=OptionType(option_type),
            strike=long_option['strike'],
            expiry=expiry_date,
            side=OrderSide.BUY,
            quantity=1,
            price=long_option['ask']
        ))

        spread_name = "Bull Put" if self.spread_type == "put" else "Bear Call"
        logger.info(f"Built {spread_name} Spread for {symbol}, net credit: ${net_credit:.2f}")

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
        """根据Delta寻找期权"""
        from datetime import datetime

        today = datetime.now()
        expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
        time_to_expiry = (expiry - today).days / 365.0

        if time_to_expiry <= 0:
            return None

        deltas = []
        for _, option in options.iterrows():
            iv = option.get('implied_volatility', 0.3)
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
        options['delta_diff'] = np.abs(options['delta'] - target_delta)

        return options.loc[options['delta_diff'].idxmin()]

    def check_exit_conditions(
        self,
        position: Position,
        market_data: Dict
    ) -> bool:
        """检查平仓条件"""
        current_prices = market_data.get("option_prices", {})
        current_pnl = position.get_current_pnl(current_prices)
        max_profit = position.get_max_profit()

        # 利润目标
        if current_pnl >= max_profit * self.profit_target:
            return True

        # 止损
        if current_pnl <= -abs(max_profit) * self.stop_loss:
            return True

        # 接近到期
        from datetime import datetime
        if position.trades:
            expiry_date = datetime.strptime(position.trades[0].expiry, "%Y-%m-%d")
            days_to_expiry = (expiry_date - datetime.now()).days
            if days_to_expiry <= 7:
                return True

        return False
