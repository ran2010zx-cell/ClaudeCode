"""
Implied Volatility Calculator
隐含波动率计算器
"""

import numpy as np
from scipy.optimize import brentq, minimize_scalar
from typing import Optional
import logging

from .black_scholes import BlackScholesModel

logger = logging.getLogger(__name__)


class ImpliedVolatilityCalculator:
    """隐含波动率计算器"""

    @staticmethod
    def calculate_iv(
        market_price: float,
        S: float,
        K: float,
        T: float,
        r: float,
        option_type: str = "call",
        method: str = "brent"
    ) -> Optional[float]:
        """
        计算隐含波动率

        Args:
            market_price: 期权市场价格
            S: 标的资产当前价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            option_type: 期权类型 ("call" or "put")
            method: 求解方法 ("brent" or "newton")

        Returns:
            float: 隐含波动率，如果计算失败返回None
        """
        if T <= 0:
            return None

        # 检查价格是否合理
        if option_type.lower() == "call":
            intrinsic_value = max(S - K, 0)
            max_value = S
        else:
            intrinsic_value = max(K - S, 0)
            max_value = K * np.exp(-r * T)

        if market_price < intrinsic_value or market_price > max_value:
            logger.warning(f"Market price {market_price} out of valid range [{intrinsic_value}, {max_value}]")
            return None

        # 定义目标函数
        def objective(sigma):
            if option_type.lower() == "call":
                theoretical_price = BlackScholesModel.call_price(S, K, T, r, sigma)
            else:
                theoretical_price = BlackScholesModel.put_price(S, K, T, r, sigma)
            return theoretical_price - market_price

        try:
            if method == "brent":
                # 使用Brent方法求解
                iv = brentq(objective, 0.001, 5.0, maxiter=100)
            else:
                # 使用最小化方法
                def objective_squared(sigma):
                    return objective(sigma) ** 2

                result = minimize_scalar(
                    objective_squared,
                    bounds=(0.001, 5.0),
                    method='bounded'
                )
                iv = result.x

            return iv

        except Exception as e:
            logger.error(f"Failed to calculate IV: {e}")
            return None

    @staticmethod
    def calculate_iv_batch(
        market_prices: np.ndarray,
        S: float,
        K: np.ndarray,
        T: np.ndarray,
        r: float,
        option_types: np.ndarray
    ) -> np.ndarray:
        """
        批量计算隐含波动率

        Args:
            market_prices: 期权市场价格数组
            S: 标的资产当前价格
            K: 行权价数组
            T: 到期时间数组（年）
            r: 无风险利率
            option_types: 期权类型数组 ("call" or "put")

        Returns:
            np.ndarray: 隐含波动率数组
        """
        n = len(market_prices)
        ivs = np.zeros(n)

        for i in range(n):
            iv = ImpliedVolatilityCalculator.calculate_iv(
                market_prices[i],
                S,
                K[i],
                T[i],
                r,
                option_types[i]
            )
            ivs[i] = iv if iv is not None else np.nan

        return ivs

    @staticmethod
    def calculate_iv_surface(
        market_prices: np.ndarray,
        S: float,
        strikes: np.ndarray,
        expiries: np.ndarray,
        r: float,
        option_type: str = "call"
    ) -> np.ndarray:
        """
        计算隐含波动率曲面

        Args:
            market_prices: 期权市场价格矩阵 (strikes x expiries)
            S: 标的资产当前价格
            strikes: 行权价数组
            expiries: 到期时间数组（年）
            r: 无风险利率
            option_type: 期权类型

        Returns:
            np.ndarray: 隐含波动率曲面 (strikes x expiries)
        """
        n_strikes = len(strikes)
        n_expiries = len(expiries)

        iv_surface = np.zeros((n_strikes, n_expiries))

        for i in range(n_strikes):
            for j in range(n_expiries):
                iv = ImpliedVolatilityCalculator.calculate_iv(
                    market_prices[i, j],
                    S,
                    strikes[i],
                    expiries[j],
                    r,
                    option_type
                )
                iv_surface[i, j] = iv if iv is not None else np.nan

        return iv_surface


def calculate_historical_volatility(
    prices: np.ndarray,
    window: int = 30,
    annualization_factor: float = 252
) -> float:
    """
    计算历史波动率

    Args:
        prices: 价格序列
        window: 计算窗口（天）
        annualization_factor: 年化因子（交易日数）

    Returns:
        float: 历史波动率
    """
    if len(prices) < window + 1:
        raise ValueError(f"Need at least {window + 1} prices")

    # 计算对数收益率
    log_returns = np.diff(np.log(prices[-window-1:]))

    # 计算标准差并年化
    volatility = np.std(log_returns) * np.sqrt(annualization_factor)

    return volatility


def calculate_realized_volatility(
    prices: np.ndarray,
    annualization_factor: float = 252
) -> float:
    """
    计算已实现波动率

    Args:
        prices: 价格序列
        annualization_factor: 年化因子（交易日数）

    Returns:
        float: 已实现波动率
    """
    # 计算对数收益率
    log_returns = np.diff(np.log(prices))

    # 计算平方收益率的和
    squared_returns = log_returns ** 2
    realized_var = np.sum(squared_returns)

    # 年化并开方得到波动率
    realized_vol = np.sqrt(realized_var * annualization_factor / len(log_returns))

    return realized_vol
