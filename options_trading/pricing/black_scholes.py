"""
Black-Scholes Option Pricing Model
Black-Scholes期权定价模型
"""

import numpy as np
from scipy.stats import norm
from typing import Dict, Tuple
from dataclasses import dataclass


@dataclass
class Greeks:
    """期权Greeks"""
    delta: float  # Delta: 期权价格对标的价格的一阶导数
    gamma: float  # Gamma: Delta对标的价格的一阶导数
    theta: float  # Theta: 期权价格对时间的导数
    vega: float   # Vega: 期权价格对波动率的导数
    rho: float    # Rho: 期权价格对利率的导数


class BlackScholesModel:
    """Black-Scholes期权定价模型"""

    @staticmethod
    def calculate_d1_d2(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> Tuple[float, float]:
        """
        计算d1和d2

        Args:
            S: 标的资产当前价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率

        Returns:
            Tuple[float, float]: (d1, d2)
        """
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        return d1, d2

    @staticmethod
    def call_price(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        计算欧式看涨期权价格

        Args:
            S: 标的资产当前价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率

        Returns:
            float: 期权价格
        """
        if T <= 0:
            return max(S - K, 0)

        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma)

        call = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return call

    @staticmethod
    def put_price(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float
    ) -> float:
        """
        计算欧式看跌期权价格

        Args:
            S: 标的资产当前价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率

        Returns:
            float: 期权价格
        """
        if T <= 0:
            return max(K - S, 0)

        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma)

        put = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
        return put

    @staticmethod
    def calculate_greeks(
        S: float,
        K: float,
        T: float,
        r: float,
        sigma: float,
        option_type: str = "call"
    ) -> Greeks:
        """
        计算期权Greeks

        Args:
            S: 标的资产当前价格
            K: 行权价
            T: 到期时间（年）
            r: 无风险利率
            sigma: 波动率
            option_type: 期权类型 ("call" or "put")

        Returns:
            Greeks: Greeks对象
        """
        if T <= 0:
            return Greeks(
                delta=1.0 if option_type.lower() == "call" and S > K else 0.0,
                gamma=0.0,
                theta=0.0,
                vega=0.0,
                rho=0.0
            )

        d1, d2 = BlackScholesModel.calculate_d1_d2(S, K, T, r, sigma)

        # Delta
        if option_type.lower() == "call":
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1

        # Gamma (相同对于看涨和看跌)
        gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))

        # Vega (相同对于看涨和看跌)
        vega = S * norm.pdf(d1) * np.sqrt(T) / 100  # 除以100转换为百分比

        # Theta
        if option_type.lower() == "call":
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                - r * K * np.exp(-r * T) * norm.cdf(d2)
            ) / 365  # 转换为每天
        else:
            theta = (
                -S * norm.pdf(d1) * sigma / (2 * np.sqrt(T))
                + r * K * np.exp(-r * T) * norm.cdf(-d2)
            ) / 365  # 转换为每天

        # Rho
        if option_type.lower() == "call":
            rho = K * T * np.exp(-r * T) * norm.cdf(d2) / 100  # 除以100转换为百分比
        else:
            rho = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100

        return Greeks(
            delta=delta,
            gamma=gamma,
            theta=theta,
            vega=vega,
            rho=rho
        )


def calculate_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call"
) -> Dict[str, float]:
    """
    计算期权Greeks（便捷函数）

    Args:
        S: 标的资产当前价格
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 波动率
        option_type: 期权类型 ("call" or "put")

    Returns:
        Dict[str, float]: Greeks字典
    """
    greeks = BlackScholesModel.calculate_greeks(S, K, T, r, sigma, option_type)

    return {
        "delta": greeks.delta,
        "gamma": greeks.gamma,
        "theta": greeks.theta,
        "vega": greeks.vega,
        "rho": greeks.rho
    }


def calculate_option_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call"
) -> float:
    """
    计算期权价格（便捷函数）

    Args:
        S: 标的资产当前价格
        K: 行权价
        T: 到期时间（年）
        r: 无风险利率
        sigma: 波动率
        option_type: 期权类型 ("call" or "put")

    Returns:
        float: 期权价格
    """
    if option_type.lower() == "call":
        return BlackScholesModel.call_price(S, K, T, r, sigma)
    else:
        return BlackScholesModel.put_price(S, K, T, r, sigma)
