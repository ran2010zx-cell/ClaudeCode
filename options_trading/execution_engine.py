"""
Execution Engine
交易执行引擎
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

from .strategies.base import Strategy, Position, Trade, OrderSide
from .futu_api.client import FutuClient
from .risk_management import RiskManager
from .config import Config

logger = logging.getLogger(__name__)


class ExecutionEngine:
    """交易执行引擎"""

    def __init__(
        self,
        futu_client: FutuClient,
        strategies: List[Strategy],
        risk_manager: RiskManager,
        config: Config
    ):
        """
        初始化执行引擎

        Args:
            futu_client: 富途客户端
            strategies: 策略列表
            risk_manager: 风险管理器
            config: 配置
        """
        self.futu_client = futu_client
        self.strategies = strategies
        self.risk_manager = risk_manager
        self.config = config
        self.active_positions: List[Position] = []

    def run_cycle(self):
        """
        运行一个交易周期
        """
        logger.info("=" * 50)
        logger.info("Starting trading cycle")
        logger.info("=" * 50)

        # 1. 获取账户信息
        account_info = self.futu_client.get_account_info()
        if not account_info:
            logger.error("Failed to get account info")
            return

        account_value = account_info.get('total_assets', 0)
        logger.info(f"Account value: ${account_value:,.2f}")

        # 2. 检查现有持仓是否需要平仓
        self._check_exit_positions()

        # 3. 为每个标的生成新的交易信号
        for symbol in self.config.trading.symbols:
            self._process_symbol(symbol, account_value)

        # 4. 检查组合风险
        if not self.risk_manager.check_portfolio_risk(self.active_positions, account_value):
            logger.warning("Portfolio risk check failed, skipping new positions")

        logger.info(f"Cycle completed. Active positions: {len(self.active_positions)}")

    def _check_exit_positions(self):
        """检查并平仓符合条件的持仓"""
        logger.info("Checking exit conditions for active positions")

        positions_to_close = []

        for position in self.active_positions:
            if position.status != "open":
                continue

            # 获取当前期权价格
            option_codes = [trade.symbol for trade in position.trades]
            option_prices = self._get_option_prices(option_codes)

            if not option_prices:
                continue

            market_data = {
                "option_prices": option_prices
            }

            # 检查每个策略的平仓条件
            for strategy in self.strategies:
                if strategy.check_exit_conditions(position, market_data):
                    logger.info(f"Exit condition met for position in {position.symbol}")
                    positions_to_close.append(position)
                    break

        # 执行平仓
        for position in positions_to_close:
            self._close_position(position)

    def _process_symbol(self, symbol: str, account_value: float):
        """
        处理单个标的

        Args:
            symbol: 标的代码
            account_value: 账户价值
        """
        logger.info(f"Processing {symbol}")

        # 获取市场数据
        market_data = self._get_market_data(symbol)
        if not market_data:
            logger.warning(f"Failed to get market data for {symbol}")
            return

        # 检查是否已有该标的的持仓
        existing_positions = [p for p in self.active_positions if p.symbol == symbol and p.status == "open"]
        if len(existing_positions) >= 2:
            logger.info(f"Already have {len(existing_positions)} positions in {symbol}, skipping")
            return

        # 运行每个策略
        for strategy in self.strategies:
            try:
                # 生成信号
                new_positions = strategy.generate_signals(market_data)

                for position in new_positions:
                    # 风险检查
                    if not self.risk_manager.check_position_risk(position, account_value):
                        logger.warning(f"Position risk check failed for {symbol}")
                        continue

                    # 执行开仓
                    if self._open_position(position):
                        self.active_positions.append(position)
                        logger.info(f"Opened new position in {symbol}")
                        break  # 每个标的只开一个仓位

            except Exception as e:
                logger.error(f"Error running strategy {strategy.name} for {symbol}: {e}")

    def _get_market_data(self, symbol: str) -> Optional[Dict]:
        """
        获取市场数据

        Args:
            symbol: 标的代码

        Returns:
            Dict: 市场数据
        """
        try:
            # 获取当前价格
            snapshot = self.futu_client.get_market_snapshot([symbol])
            if snapshot is None or snapshot.empty:
                return None

            current_price = snapshot.iloc[0]['last_price']

            # 获取期权链（这里需要实现期权链获取逻辑）
            # 暂时返回None，实际使用时需要完善
            option_chain = None  # TODO: 实现期权链获取

            # 计算IV百分位（需要历史数据）
            iv_percentile = 50  # TODO: 实现IV百分位计算

            return {
                "symbol": symbol,
                "current_price": current_price,
                "option_chain": option_chain,
                "iv_percentile": iv_percentile,
                "risk_free_rate": 0.05
            }

        except Exception as e:
            logger.error(f"Error getting market data for {symbol}: {e}")
            return None

    def _get_option_prices(self, option_codes: List[str]) -> Dict[str, float]:
        """
        获取期权价格

        Args:
            option_codes: 期权代码列表

        Returns:
            Dict: 期权价格字典
        """
        try:
            snapshot = self.futu_client.get_market_snapshot(option_codes)
            if snapshot is None or snapshot.empty:
                return {}

            prices = {}
            for _, row in snapshot.iterrows():
                code = row['code']
                # 使用bid和ask的中间价
                mid_price = (row.get('bid_price', 0) + row.get('ask_price', 0)) / 2
                prices[code] = mid_price

            return prices

        except Exception as e:
            logger.error(f"Error getting option prices: {e}")
            return {}

    def _open_position(self, position: Position) -> bool:
        """
        开仓

        Args:
            position: 持仓

        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"Opening position for {position.symbol}")

            # 执行每条交易
            for trade in position.trades:
                side = "BUY" if trade.side == OrderSide.BUY else "SELL"
                logger.info(
                    f"  {side} {trade.quantity} {trade.option_type.value} "
                    f"${trade.strike} @ ${trade.price:.2f}"
                )

                # 实际下单（这里需要完善）
                # order = self.futu_client.place_order(
                #     symbol=trade.symbol,
                #     quantity=trade.quantity,
                #     price=trade.price,
                #     side=side
                # )

            position.status = "open"
            position.entry_time = datetime.now()

            return True

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return False

    def _close_position(self, position: Position) -> bool:
        """
        平仓

        Args:
            position: 持仓

        Returns:
            bool: 是否成功
        """
        try:
            logger.info(f"Closing position for {position.symbol}")

            # 执行反向交易
            for trade in position.trades:
                # 反向操作
                opposite_side = "SELL" if trade.side == OrderSide.BUY else "BUY"
                logger.info(
                    f"  {opposite_side} {trade.quantity} {trade.option_type.value} "
                    f"${trade.strike}"
                )

                # 实际下单平仓
                # order = self.futu_client.place_order(
                #     symbol=trade.symbol,
                #     quantity=trade.quantity,
                #     price=0,  # 市价
                #     side=opposite_side
                # )

            position.close_position()
            logger.info(f"Position closed for {position.symbol}")

            return True

        except Exception as e:
            logger.error(f"Error closing position: {e}")
            return False

    def get_portfolio_summary(self) -> Dict:
        """
        获取组合摘要

        Returns:
            Dict: 组合摘要
        """
        open_positions = [p for p in self.active_positions if p.status == "open"]
        closed_positions = [p for p in self.active_positions if p.status == "closed"]

        total_credit = sum(p.get_total_credit() for p in open_positions)

        return {
            "open_positions": len(open_positions),
            "closed_positions": len(closed_positions),
            "total_credit": total_credit,
            "symbols": list(set(p.symbol for p in open_positions))
        }
