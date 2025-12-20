"""
Base Strategy Classes
策略基类
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum


class OptionType(Enum):
    """期权类型"""
    CALL = "CALL"
    PUT = "PUT"


class OrderSide(Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Trade:
    """单笔交易"""
    symbol: str  # 期权代码
    option_type: OptionType  # 期权类型
    strike: float  # 行权价
    expiry: str  # 到期日
    side: OrderSide  # 买卖方向
    quantity: int  # 数量
    price: float  # 价格
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if isinstance(self.option_type, str):
            self.option_type = OptionType(self.option_type)
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)


@dataclass
class Position:
    """持仓"""
    symbol: str  # 标的代码
    trades: List[Trade] = field(default_factory=list)  # 交易列表
    entry_time: datetime = field(default_factory=datetime.now)
    exit_time: Optional[datetime] = None
    status: str = "open"  # open, closed

    def add_trade(self, trade: Trade):
        """添加交易"""
        self.trades.append(trade)

    def get_total_credit(self) -> float:
        """
        计算总收入（期权卖出收到的权利金）

        Returns:
            float: 总收入
        """
        credit = 0.0
        for trade in self.trades:
            if trade.side == OrderSide.SELL:
                credit += trade.price * trade.quantity * 100  # 每份期权代表100股
            else:
                credit -= trade.price * trade.quantity * 100
        return credit

    def get_max_loss(self) -> float:
        """
        计算最大损失

        Returns:
            float: 最大损失
        """
        # 由子类实现具体策略的最大损失计算
        return 0.0

    def get_max_profit(self) -> float:
        """
        计算最大利润

        Returns:
            float: 最大利润
        """
        # 一般情况下，最大利润等于收到的净权利金
        return self.get_total_credit()

    def get_current_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        计算当前盈亏

        Args:
            current_prices: 当前期权价格字典 {symbol: price}

        Returns:
            float: 当前盈亏
        """
        pnl = 0.0
        for trade in self.trades:
            current_price = current_prices.get(trade.symbol, trade.price)
            if trade.side == OrderSide.SELL:
                # 卖出的期权，价格下跌是盈利
                pnl += (trade.price - current_price) * trade.quantity * 100
            else:
                # 买入的期权，价格上涨是盈利
                pnl += (current_price - trade.price) * trade.quantity * 100
        return pnl

    def close_position(self):
        """平仓"""
        self.status = "closed"
        self.exit_time = datetime.now()


class Strategy(ABC):
    """策略基类"""

    def __init__(self, name: str):
        """
        初始化策略

        Args:
            name: 策略名称
        """
        self.name = name
        self.positions: List[Position] = []

    @abstractmethod
    def generate_signals(
        self,
        market_data: Dict,
        **kwargs
    ) -> List[Position]:
        """
        生成交易信号

        Args:
            market_data: 市场数据
            **kwargs: 其他参数

        Returns:
            List[Position]: 建议的持仓列表
        """
        pass

    @abstractmethod
    def check_exit_conditions(
        self,
        position: Position,
        market_data: Dict
    ) -> bool:
        """
        检查平仓条件

        Args:
            position: 当前持仓
            market_data: 市场数据

        Returns:
            bool: 是否应该平仓
        """
        pass

    def add_position(self, position: Position):
        """
        添加持仓

        Args:
            position: 持仓
        """
        self.positions.append(position)

    def get_open_positions(self) -> List[Position]:
        """
        获取所有开仓持仓

        Returns:
            List[Position]: 开仓持仓列表
        """
        return [p for p in self.positions if p.status == "open"]

    def get_closed_positions(self) -> List[Position]:
        """
        获取所有已平仓持仓

        Returns:
            List[Position]: 已平仓持仓列表
        """
        return [p for p in self.positions if p.status == "closed"]

    def get_total_pnl(self, current_prices: Dict[str, float]) -> float:
        """
        计算总盈亏

        Args:
            current_prices: 当前期权价格字典

        Returns:
            float: 总盈亏
        """
        total_pnl = 0.0
        for position in self.positions:
            total_pnl += position.get_current_pnl(current_prices)
        return total_pnl
