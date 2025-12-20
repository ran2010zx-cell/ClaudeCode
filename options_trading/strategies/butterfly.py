"""
Butterfly Spread Strategy
蝶式价差策略

策略说明：
- 买入1个低行权价期权
- 卖出2个中间行权价期权
- 买入1个高行权价期权
- 适合预期标的价格在到期时接近中间行权价
"""

import logging
from typing import Dict, List, Optional
import pandas as pd

from .base import Strategy, Position, Trade, OptionType, OrderSide

logger = logging.getLogger(__name__)


class ButterflyStrategy(Strategy):
    """蝶式价差策略"""

    def __init__(
        self,
        name: str = "Butterfly",
        wing_width: float = 5.0,
        max_cost: float = 2.0,
        profit_target: float = 0.7,
        stop_loss: float = 0.5,
        min_days_to_expiry: int = 30,
        max_days_to_expiry: int = 60,
        option_type: str = "call"
    ):
        """
        初始化蝶式价差策略

        Args:
            name: 策略名称
            wing_width: 翼展宽度
            max_cost: 最大成本
            profit_target: 利润目标比例
            stop_loss: 止损比例
            min_days_to_expiry: 最小到期天数
            max_days_to_expiry: 最大到期天数
            option_type: 期权类型（"call"或"put"）
        """
        super().__init__(name)
        self.wing_width = wing_width
        self.max_cost = max_cost
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.min_days_to_expiry = min_days_to_expiry
        self.max_days_to_expiry = max_days_to_expiry
        self.option_type = option_type.upper()

    def generate_signals(
        self,
        market_data: Dict,
        **kwargs
    ) -> List[Position]:
        """生成蝶式价差交易信号"""
        symbol = market_data.get("symbol")
        current_price = market_data.get("current_price")
        option_chain = market_data.get("option_chain")

        if option_chain is None or option_chain.empty:
            return []

        suitable_options = self._filter_by_expiry(option_chain)
        if suitable_options.empty:
            return []

        positions = []
        for expiry_date in suitable_options['expiry_date'].unique():
            expiry_options = suitable_options[suitable_options['expiry_date'] == expiry_date]

            position = self._build_butterfly(
                symbol=symbol,
                current_price=current_price,
                options=expiry_options,
                expiry_date=expiry_date
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

    def _build_butterfly(
        self,
        symbol: str,
        current_price: float,
        options: pd.DataFrame,
        expiry_date: str
    ) -> Optional[Position]:
        """构建蝶式价差组合"""
        type_options = options[options['option_type'] == self.option_type].copy()
        type_options = type_options.sort_values('strike')

        if len(type_options) < 3:
            return None

        # 找到ATM期权作为中间行权价
        type_options['strike_diff'] = abs(type_options['strike'] - current_price)
        atm_idx = type_options['strike_diff'].idxmin()
        atm_option = type_options.loc[atm_idx]

        # 找到低行权价期权
        lower_strike = atm_option['strike'] - self.wing_width
        lower_options = type_options[type_options['strike'] <= lower_strike]
        if lower_options.empty:
            return None
        lower_option = lower_options.iloc[-1]

        # 找到高行权价期权
        upper_strike = atm_option['strike'] + self.wing_width
        upper_options = type_options[type_options['strike'] >= upper_strike]
        if upper_options.empty:
            return None
        upper_option = upper_options.iloc[0]

        # 计算成本
        cost = (
            lower_option['ask'] +
            upper_option['ask'] -
            2 * atm_option['bid']
        )

        if cost > self.max_cost or cost <= 0:
            return None

        # 创建持仓
        position = Position(symbol=symbol)

        # 买入低行权价
        position.add_trade(Trade(
            symbol=lower_option['option_code'],
            option_type=OptionType(self.option_type),
            strike=lower_option['strike'],
            expiry=expiry_date,
            side=OrderSide.BUY,
            quantity=1,
            price=lower_option['ask']
        ))

        # 卖出ATM（2份）
        position.add_trade(Trade(
            symbol=atm_option['option_code'],
            option_type=OptionType(self.option_type),
            strike=atm_option['strike'],
            expiry=expiry_date,
            side=OrderSide.SELL,
            quantity=2,
            price=atm_option['bid']
        ))

        # 买入高行权价
        position.add_trade(Trade(
            symbol=upper_option['option_code'],
            option_type=OptionType(self.option_type),
            strike=upper_option['strike'],
            expiry=expiry_date,
            side=OrderSide.BUY,
            quantity=1,
            price=upper_option['ask']
        ))

        logger.info(f"Built Butterfly for {symbol}, cost: ${cost:.2f}")
        return position

    def check_exit_conditions(
        self,
        position: Position,
        market_data: Dict
    ) -> bool:
        """检查平仓条件"""
        current_prices = market_data.get("option_prices", {})
        current_pnl = position.get_current_pnl(current_prices)

        # 计算初始成本
        initial_cost = abs(position.get_total_credit())

        # 利润目标
        max_profit = self.wing_width * 100 - initial_cost
        if current_pnl >= max_profit * self.profit_target:
            return True

        # 止损
        if current_pnl <= -initial_cost * self.stop_loss:
            return True

        # 接近到期
        from datetime import datetime
        if position.trades:
            expiry_date = datetime.strptime(position.trades[0].expiry, "%Y-%m-%d")
            days_to_expiry = (expiry_date - datetime.now()).days
            if days_to_expiry <= 7:
                return True

        return False
