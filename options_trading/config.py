"""
Configuration for Options Trading System
期权交易系统配置
"""

import os
from typing import List
from dataclasses import dataclass


@dataclass
class FutuConfig:
    """富途API配置"""
    host: str = "127.0.0.1"  # OpenD地址
    port: int = 11111  # OpenD端口
    trade_env: int = 0  # 0为仿真，1为真实交易
    trade_pwd_md5: str = ""  # 交易密码MD5（真实交易需要）

    # API权限
    enable_realtime_quote: bool = True
    enable_option_quote: bool = True
    enable_trade: bool = True


@dataclass
class TradingConfig:
    """交易配置"""
    # 标的股票列表（美股大盘股）
    symbols: List[str] = None

    # 期权参数
    days_to_expiry_min: int = 30  # 最小到期天数
    days_to_expiry_max: int = 60  # 最大到期天数

    # Delta范围（用于选择期权）
    delta_call_min: float = 0.15
    delta_call_max: float = 0.30
    delta_put_min: float = -0.30
    delta_put_max: float = -0.15

    # 风险参数
    max_position_value: float = 50000  # 单个标的最大持仓价值（美元）
    max_portfolio_value: float = 200000  # 组合最大持仓价值
    max_loss_per_trade: float = 1000  # 单笔交易最大亏损
    profit_target_ratio: float = 0.5  # 利润目标（占最大利润比例）
    stop_loss_ratio: float = 2.0  # 止损比例（占收入保证金比例）

    # 波动率参数
    iv_percentile_min: float = 30  # IV百分位最小值（低于此值不开仓）
    iv_percentile_max: float = 70  # IV百分位最大值（高于此值警惕风险）

    def __post_init__(self):
        if self.symbols is None:
            # 默认标的：美股大盘股
            self.symbols = [
                "SPY",   # 标普500 ETF
                "QQQ",   # 纳斯达克100 ETF
                "IWM",   # 罗素2000 ETF
                "AAPL",  # 苹果
                "MSFT",  # 微软
                "GOOGL", # 谷歌
                "AMZN",  # 亚马逊
                "TSLA",  # 特斯拉
                "NVDA",  # 英伟达
                "META",  # Meta
            ]


@dataclass
class StrategyConfig:
    """策略配置"""
    # 可用策略类型
    strategies: List[str] = None

    # Iron Condor参数
    iron_condor_width: float = 5  # 价差宽度（美元）

    # Butterfly参数
    butterfly_width: float = 5  # 价差宽度

    # Credit Spread参数
    credit_spread_width: float = 5

    def __post_init__(self):
        if self.strategies is None:
            self.strategies = [
                "iron_condor",     # 铁鹰式
                "credit_spread",   # 信用价差
                "butterfly",       # 蝶式价差
            ]


@dataclass
class BacktestConfig:
    """回测配置"""
    start_date: str = "2023-01-01"
    end_date: str = "2024-12-31"
    initial_capital: float = 100000
    commission: float = 0.65  # 每份期权佣金（美元）
    slippage: float = 0.05  # 滑点（美元）


class Config:
    """主配置类"""

    def __init__(self):
        self.futu = FutuConfig()
        self.trading = TradingConfig()
        self.strategy = StrategyConfig()
        self.backtest = BacktestConfig()

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        config = cls()

        # 富途配置
        config.futu.host = os.getenv("FUTU_HOST", "127.0.0.1")
        config.futu.port = int(os.getenv("FUTU_PORT", "11111"))
        config.futu.trade_env = int(os.getenv("FUTU_TRADE_ENV", "0"))
        config.futu.trade_pwd_md5 = os.getenv("FUTU_TRADE_PWD_MD5", "")

        # 交易配置
        if os.getenv("MAX_POSITION_VALUE"):
            config.trading.max_position_value = float(os.getenv("MAX_POSITION_VALUE"))
        if os.getenv("MAX_PORTFOLIO_VALUE"):
            config.trading.max_portfolio_value = float(os.getenv("MAX_PORTFOLIO_VALUE"))

        return config


# 全局配置实例
config = Config.from_env()
