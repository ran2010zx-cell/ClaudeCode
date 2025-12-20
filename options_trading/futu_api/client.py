"""
Futu API Client
富途API客户端封装
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
import pandas as pd

try:
    from futu import OpenQuoteContext, OpenUSTradeContext, TrdEnv, TrdMarket
    from futu import RET_OK, RET_ERROR
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False
    logging.warning("Futu OpenAPI not installed. Install with: pip install futu-api")

from ..config import FutuConfig

logger = logging.getLogger(__name__)


class FutuClient:
    """富途API客户端"""

    def __init__(self, config: FutuConfig):
        """
        初始化富途客户端

        Args:
            config: 富途配置
        """
        if not FUTU_AVAILABLE:
            raise ImportError("Futu OpenAPI is required. Install with: pip install futu-api")

        self.config = config
        self.quote_ctx: Optional[OpenQuoteContext] = None
        self.trade_ctx: Optional[OpenUSTradeContext] = None
        self._connected = False

    def connect(self) -> bool:
        """
        连接到富途OpenD

        Returns:
            bool: 连接是否成功
        """
        try:
            # 连接行情上下文
            if self.config.enable_realtime_quote or self.config.enable_option_quote:
                self.quote_ctx = OpenQuoteContext(
                    host=self.config.host,
                    port=self.config.port
                )
                logger.info(f"Connected to Futu OpenD quote service at {self.config.host}:{self.config.port}")

            # 连接交易上下文
            if self.config.enable_trade:
                trade_env = TrdEnv.SIMULATE if self.config.trade_env == 0 else TrdEnv.REAL
                self.trade_ctx = OpenUSTradeContext(
                    host=self.config.host,
                    port=self.config.port
                )
                self.trade_ctx.set_trd_env(trade_env)

                env_name = "Simulation" if self.config.trade_env == 0 else "Real"
                logger.info(f"Connected to Futu OpenD trade service ({env_name} environment)")

            self._connected = True
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Futu OpenD: {e}")
            return False

    def disconnect(self):
        """断开连接"""
        try:
            if self.quote_ctx:
                self.quote_ctx.close()
                logger.info("Disconnected from quote service")

            if self.trade_ctx:
                self.trade_ctx.close()
                logger.info("Disconnected from trade service")

            self._connected = False

        except Exception as e:
            logger.error(f"Error disconnecting: {e}")

    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected

    def get_market_snapshot(self, symbols: List[str]) -> Optional[pd.DataFrame]:
        """
        获取市场快照

        Args:
            symbols: 股票代码列表

        Returns:
            DataFrame: 市场快照数据
        """
        if not self.quote_ctx:
            logger.error("Quote context not initialized")
            return None

        try:
            # 将symbols转换为富途格式（US.XXX）
            futu_symbols = [f"US.{s}" if not s.startswith("US.") else s for s in symbols]

            ret, data = self.quote_ctx.get_market_snapshot(futu_symbols)
            if ret == RET_OK:
                return data
            else:
                logger.error(f"Failed to get market snapshot: {data}")
                return None

        except Exception as e:
            logger.error(f"Error getting market snapshot: {e}")
            return None

    def get_history_kline(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        ktype: str = "K_DAY"
    ) -> Optional[pd.DataFrame]:
        """
        获取历史K线数据

        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            ktype: K线类型

        Returns:
            DataFrame: K线数据
        """
        if not self.quote_ctx:
            logger.error("Quote context not initialized")
            return None

        try:
            futu_symbol = f"US.{symbol}" if not symbol.startswith("US.") else symbol

            ret, data = self.quote_ctx.request_history_kline(
                code=futu_symbol,
                start=start_date,
                end=end_date,
                ktype=ktype,
                max_count=1000
            )

            if ret == RET_OK:
                return data
            else:
                logger.error(f"Failed to get history kline: {data}")
                return None

        except Exception as e:
            logger.error(f"Error getting history kline: {e}")
            return None

    def get_account_info(self) -> Optional[Dict]:
        """
        获取账户信息

        Returns:
            Dict: 账户信息
        """
        if not self.trade_ctx:
            logger.error("Trade context not initialized")
            return None

        try:
            ret, data = self.trade_ctx.accinfo_query()
            if ret == RET_OK:
                return data.to_dict('records')[0] if not data.empty else {}
            else:
                logger.error(f"Failed to get account info: {data}")
                return None

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None

    def get_positions(self) -> Optional[pd.DataFrame]:
        """
        获取持仓信息

        Returns:
            DataFrame: 持仓数据
        """
        if not self.trade_ctx:
            logger.error("Trade context not initialized")
            return None

        try:
            ret, data = self.trade_ctx.position_list_query()
            if ret == RET_OK:
                return data
            else:
                logger.error(f"Failed to get positions: {data}")
                return None

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return None

    def place_order(
        self,
        symbol: str,
        quantity: int,
        price: float,
        order_type: str = "LIMIT",
        side: str = "BUY"
    ) -> Optional[Dict]:
        """
        下单

        Args:
            symbol: 股票/期权代码
            quantity: 数量
            price: 价格
            order_type: 订单类型
            side: 买卖方向

        Returns:
            Dict: 订单信息
        """
        if not self.trade_ctx:
            logger.error("Trade context not initialized")
            return None

        try:
            futu_symbol = f"US.{symbol}" if not symbol.startswith("US.") else symbol

            # 这里需要根据实际需求实现下单逻辑
            # 富途API的下单需要更详细的参数设置
            logger.info(f"Placing order: {side} {quantity} {futu_symbol} @ {price}")

            # TODO: 实现实际下单逻辑
            return {
                "symbol": futu_symbol,
                "quantity": quantity,
                "price": price,
                "side": side,
                "status": "pending"
            }

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
