"""
Option Chain Fetcher
期权链数据获取
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import pandas as pd

try:
    from futu import RET_OK
    FUTU_AVAILABLE = True
except ImportError:
    FUTU_AVAILABLE = False

from .client import FutuClient

logger = logging.getLogger(__name__)


class OptionChainFetcher:
    """期权链数据获取器"""

    def __init__(self, client: FutuClient):
        """
        初始化期权链获取器

        Args:
            client: 富途客户端
        """
        self.client = client

    def get_option_chain(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """
        获取期权链数据

        Args:
            symbol: 标的股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)

        Returns:
            DataFrame: 期权链数据
        """
        if not self.client.quote_ctx:
            logger.error("Quote context not initialized")
            return None

        try:
            futu_symbol = f"US.{symbol}" if not symbol.startswith("US.") else symbol

            # 获取期权到期日列表
            ret, data = self.client.quote_ctx.get_option_expiration_date(futu_symbol)
            if ret != RET_OK:
                logger.error(f"Failed to get option expiration dates: {data}")
                return None

            expiration_dates = data['strike_time'].tolist()

            # 过滤到期日
            if start_date or end_date:
                expiration_dates = self._filter_expiration_dates(
                    expiration_dates,
                    start_date,
                    end_date
                )

            # 获取每个到期日的期权链
            all_options = []
            for exp_date in expiration_dates:
                options = self._get_option_chain_by_expiry(futu_symbol, exp_date)
                if options is not None and not options.empty:
                    all_options.append(options)

            if not all_options:
                logger.warning(f"No option data found for {symbol}")
                return None

            # 合并所有期权数据
            result = pd.concat(all_options, ignore_index=True)
            return result

        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return None

    def _get_option_chain_by_expiry(
        self,
        symbol: str,
        expiry_date: str
    ) -> Optional[pd.DataFrame]:
        """
        获取指定到期日的期权链

        Args:
            symbol: 标的股票代码（富途格式）
            expiry_date: 到期日

        Returns:
            DataFrame: 期权数据
        """
        try:
            ret, data = self.client.quote_ctx.get_option_chain(
                code=symbol,
                start=expiry_date,
                end=expiry_date
            )

            if ret == RET_OK:
                return data
            else:
                logger.warning(f"Failed to get option chain for {expiry_date}: {data}")
                return None

        except Exception as e:
            logger.error(f"Error getting option chain for {expiry_date}: {e}")
            return None

    def _filter_expiration_dates(
        self,
        dates: List[str],
        start_date: Optional[str],
        end_date: Optional[str]
    ) -> List[str]:
        """
        过滤到期日

        Args:
            dates: 到期日列表
            start_date: 开始日期
            end_date: 结束日期

        Returns:
            List[str]: 过滤后的到期日列表
        """
        filtered = []

        for date_str in dates:
            date = datetime.strptime(date_str, "%Y-%m-%d")

            if start_date:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                if date < start:
                    continue

            if end_date:
                end = datetime.strptime(end_date, "%Y-%m-%d")
                if date > end:
                    continue

            filtered.append(date_str)

        return filtered

    def get_option_quotes(self, option_codes: List[str]) -> Optional[pd.DataFrame]:
        """
        获取期权实时报价

        Args:
            option_codes: 期权代码列表

        Returns:
            DataFrame: 期权报价数据
        """
        if not self.client.quote_ctx:
            logger.error("Quote context not initialized")
            return None

        try:
            ret, data = self.client.quote_ctx.get_market_snapshot(option_codes)
            if ret == RET_OK:
                return data
            else:
                logger.error(f"Failed to get option quotes: {data}")
                return None

        except Exception as e:
            logger.error(f"Error getting option quotes: {e}")
            return None

    def find_options_by_delta(
        self,
        symbol: str,
        target_delta: float,
        option_type: str,
        days_to_expiry_min: int = 30,
        days_to_expiry_max: int = 60
    ) -> Optional[pd.DataFrame]:
        """
        根据Delta值查找期权

        Args:
            symbol: 标的股票代码
            target_delta: 目标Delta值
            option_type: 期权类型 ("CALL" or "PUT")
            days_to_expiry_min: 最小到期天数
            days_to_expiry_max: 最大到期天数

        Returns:
            DataFrame: 符合条件的期权
        """
        # 计算日期范围
        today = datetime.now()
        start_date = (today + timedelta(days=days_to_expiry_min)).strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=days_to_expiry_max)).strftime("%Y-%m-%d")

        # 获取期权链
        option_chain = self.get_option_chain(symbol, start_date, end_date)

        if option_chain is None or option_chain.empty:
            return None

        # 过滤期权类型
        if option_type.upper() == "CALL":
            options = option_chain[option_chain['option_type'] == 'CALL']
        else:
            options = option_chain[option_chain['option_type'] == 'PUT']

        # 这里需要根据实际的期权定价模型计算Delta
        # 暂时返回所有符合到期日范围的期权
        # TODO: 实现Delta计算和筛选

        return options
