"""
Risk Management Module
风险管理模块
"""

import logging
from typing import Dict, List
import numpy as np

from .strategies.base import Position
from .config import TradingConfig

logger = logging.getLogger(__name__)


class RiskManager:
    """风险管理器"""

    def __init__(self, config: TradingConfig):
        """
        初始化风险管理器

        Args:
            config: 交易配置
        """
        self.config = config

    def check_position_risk(
        self,
        position: Position,
        account_value: float
    ) -> bool:
        """
        检查单个持仓风险

        Args:
            position: 持仓
            account_value: 账户价值

        Returns:
            bool: 是否通过风险检查
        """
        # 检查最大损失
        max_loss = self._calculate_max_loss(position)

        if max_loss > self.config.max_loss_per_trade:
            logger.warning(
                f"Position max loss ${max_loss:.2f} exceeds limit ${self.config.max_loss_per_trade:.2f}"
            )
            return False

        # 检查占用资金比例
        position_value = abs(max_loss)
        if position_value > self.config.max_position_value:
            logger.warning(
                f"Position value ${position_value:.2f} exceeds limit ${self.config.max_position_value:.2f}"
            )
            return False

        # 检查占账户比例
        position_ratio = position_value / account_value if account_value > 0 else 1.0
        if position_ratio > 0.1:  # 单个持仓不超过账户的10%
            logger.warning(
                f"Position ratio {position_ratio:.2%} exceeds 10% of account"
            )
            return False

        return True

    def check_portfolio_risk(
        self,
        positions: List[Position],
        account_value: float
    ) -> bool:
        """
        检查组合风险

        Args:
            positions: 持仓列表
            account_value: 账户价值

        Returns:
            bool: 是否通过风险检查
        """
        # 计算总持仓价值
        total_position_value = sum(
            abs(self._calculate_max_loss(p)) for p in positions
        )

        if total_position_value > self.config.max_portfolio_value:
            logger.warning(
                f"Portfolio value ${total_position_value:.2f} exceeds limit ${self.config.max_portfolio_value:.2f}"
            )
            return False

        # 检查占账户比例
        portfolio_ratio = total_position_value / account_value if account_value > 0 else 1.0
        if portfolio_ratio > 0.5:  # 总持仓不超过账户的50%
            logger.warning(
                f"Portfolio ratio {portfolio_ratio:.2%} exceeds 50% of account"
            )
            return False

        # 检查集中度风险（单一标的）
        if not self._check_concentration_risk(positions):
            return False

        return True

    def _check_concentration_risk(self, positions: List[Position]) -> bool:
        """
        检查集中度风险

        Args:
            positions: 持仓列表

        Returns:
            bool: 是否通过集中度检查
        """
        symbol_counts = {}
        for position in positions:
            symbol = position.symbol
            symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

        # 单一标的持仓数量不超过总数的30%
        max_count = max(symbol_counts.values()) if symbol_counts else 0
        total_count = len(positions)

        if total_count > 0 and max_count / total_count > 0.3:
            logger.warning(
                f"Concentration risk: {max_count}/{total_count} positions in single symbol"
            )
            return False

        return True

    def _calculate_max_loss(self, position: Position) -> float:
        """
        计算最大损失

        Args:
            position: 持仓

        Returns:
            float: 最大损失
        """
        # 对于信用价差和铁鹰式，最大损失是价差宽度减去收到的权利金
        from .strategies.base import OrderSide

        # 计算所有买入和卖出的行权价
        buy_strikes = []
        sell_strikes = []

        for trade in position.trades:
            if trade.side == OrderSide.BUY:
                buy_strikes.append(trade.strike)
            else:
                sell_strikes.append(trade.strike)

        # 计算最大价差
        if buy_strikes and sell_strikes:
            max_spread = max(
                abs(max(buy_strikes) - max(sell_strikes)),
                abs(min(buy_strikes) - min(sell_strikes))
            )
        else:
            max_spread = 0

        # 最大损失 = 价差 * 100 - 收到的权利金
        net_credit = position.get_total_credit()
        max_loss = max_spread * 100 - net_credit

        return max(max_loss, 0)

    def calculate_portfolio_greeks(
        self,
        positions: List[Position],
        current_prices: Dict[str, float],
        greeks_data: Dict[str, Dict]
    ) -> Dict[str, float]:
        """
        计算组合Greeks

        Args:
            positions: 持仓列表
            current_prices: 当前价格
            greeks_data: Greeks数据 {option_code: {delta, gamma, theta, vega}}

        Returns:
            Dict: 组合Greeks
        """
        total_delta = 0.0
        total_gamma = 0.0
        total_theta = 0.0
        total_vega = 0.0

        for position in positions:
            for trade in position.trades:
                option_greeks = greeks_data.get(trade.symbol, {})

                # 根据买卖方向调整符号
                multiplier = 1 if trade.side.value == "BUY" else -1

                total_delta += option_greeks.get('delta', 0) * multiplier * trade.quantity
                total_gamma += option_greeks.get('gamma', 0) * multiplier * trade.quantity
                total_theta += option_greeks.get('theta', 0) * multiplier * trade.quantity
                total_vega += option_greeks.get('vega', 0) * multiplier * trade.quantity

        return {
            'delta': total_delta,
            'gamma': total_gamma,
            'theta': total_theta,
            'vega': total_vega
        }

    def should_rebalance(
        self,
        portfolio_greeks: Dict[str, float]
    ) -> bool:
        """
        判断是否需要再平衡

        Args:
            portfolio_greeks: 组合Greeks

        Returns:
            bool: 是否需要再平衡
        """
        # Delta中性策略：Delta绝对值不应过大
        if abs(portfolio_greeks.get('delta', 0)) > 100:
            logger.info("Portfolio delta too high, rebalancing needed")
            return True

        # Gamma风险控制
        if abs(portfolio_greeks.get('gamma', 0)) > 50:
            logger.info("Portfolio gamma too high, rebalancing needed")
            return True

        return False
