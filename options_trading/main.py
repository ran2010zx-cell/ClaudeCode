"""
Options Trading System - Main Entry Point
期权交易系统主程序
"""

import logging
import time
from datetime import datetime
import argparse

from .config import Config
from .futu_api.client import FutuClient
from .strategies import IronCondorStrategy, CreditSpreadStrategy, ButterflyStrategy
from .risk_management import RiskManager
from .execution_engine import ExecutionEngine

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('options_trading.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_strategies(config: Config):
    """
    设置交易策略

    Args:
        config: 配置对象

    Returns:
        List[Strategy]: 策略列表
    """
    strategies = []

    if "iron_condor" in config.strategy.strategies:
        strategies.append(IronCondorStrategy(
            wing_width=config.strategy.iron_condor_width,
            min_days_to_expiry=config.trading.days_to_expiry_min,
            max_days_to_expiry=config.trading.days_to_expiry_max
        ))
        logger.info("Added Iron Condor strategy")

    if "credit_spread" in config.strategy.strategies:
        # Bull Put Spread
        strategies.append(CreditSpreadStrategy(
            name="BullPutSpread",
            spread_width=config.strategy.credit_spread_width,
            spread_type="put",
            min_days_to_expiry=config.trading.days_to_expiry_min,
            max_days_to_expiry=config.trading.days_to_expiry_max
        ))
        # Bear Call Spread
        strategies.append(CreditSpreadStrategy(
            name="BearCallSpread",
            spread_width=config.strategy.credit_spread_width,
            spread_type="call",
            min_days_to_expiry=config.trading.days_to_expiry_min,
            max_days_to_expiry=config.trading.days_to_expiry_max
        ))
        logger.info("Added Credit Spread strategies")

    if "butterfly" in config.strategy.strategies:
        strategies.append(ButterflyStrategy(
            wing_width=config.strategy.butterfly_width,
            min_days_to_expiry=config.trading.days_to_expiry_min,
            max_days_to_expiry=config.trading.days_to_expiry_max
        ))
        logger.info("Added Butterfly strategy")

    return strategies


def main():
    """主程序"""
    parser = argparse.ArgumentParser(description="Options Trading System")
    parser.add_argument(
        '--mode',
        choices=['live', 'paper'],
        default='paper',
        help='Trading mode: live or paper (default: paper)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=3600,
        help='Trading cycle interval in seconds (default: 3600)'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Run only once and exit'
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Options Trading System Starting")
    logger.info("=" * 60)

    # 加载配置
    config = Config.from_env()

    # 设置交易环境
    if args.mode == 'live':
        config.futu.trade_env = 1
        logger.warning("Running in LIVE trading mode!")
    else:
        config.futu.trade_env = 0
        logger.info("Running in PAPER trading mode")

    # 初始化富途客户端
    futu_client = FutuClient(config.futu)

    try:
        # 连接到富途OpenD
        if not futu_client.connect():
            logger.error("Failed to connect to Futu OpenD. Please ensure OpenD is running.")
            return

        logger.info("Successfully connected to Futu OpenD")

        # 设置策略
        strategies = setup_strategies(config)
        if not strategies:
            logger.error("No strategies configured")
            return

        logger.info(f"Loaded {len(strategies)} strategies: {[s.name for s in strategies]}")

        # 初始化风险管理器
        risk_manager = RiskManager(config.trading)
        logger.info("Risk manager initialized")

        # 初始化执行引擎
        engine = ExecutionEngine(
            futu_client=futu_client,
            strategies=strategies,
            risk_manager=risk_manager,
            config=config
        )
        logger.info("Execution engine initialized")

        # 运行交易循环
        if args.once:
            logger.info("Running single cycle")
            engine.run_cycle()
            summary = engine.get_portfolio_summary()
            logger.info(f"Portfolio summary: {summary}")
        else:
            logger.info(f"Starting trading loop (interval: {args.interval}s)")
            cycle_count = 0

            while True:
                try:
                    cycle_count += 1
                    logger.info(f"\n{'=' * 60}")
                    logger.info(f"Cycle #{cycle_count} - {datetime.now()}")
                    logger.info(f"{'=' * 60}")

                    # 运行交易周期
                    engine.run_cycle()

                    # 显示组合摘要
                    summary = engine.get_portfolio_summary()
                    logger.info(f"\nPortfolio Summary:")
                    logger.info(f"  Open positions: {summary['open_positions']}")
                    logger.info(f"  Closed positions: {summary['closed_positions']}")
                    logger.info(f"  Total credit: ${summary['total_credit']:,.2f}")
                    logger.info(f"  Active symbols: {', '.join(summary['symbols'])}")

                    # 等待下一个周期
                    logger.info(f"\nWaiting {args.interval}s until next cycle...")
                    time.sleep(args.interval)

                except KeyboardInterrupt:
                    logger.info("\nReceived interrupt signal, shutting down...")
                    break
                except Exception as e:
                    logger.error(f"Error in trading cycle: {e}", exc_info=True)
                    logger.info(f"Waiting {args.interval}s before retry...")
                    time.sleep(args.interval)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

    finally:
        # 断开连接
        futu_client.disconnect()
        logger.info("Disconnected from Futu OpenD")
        logger.info("System shutdown complete")


if __name__ == "__main__":
    main()
