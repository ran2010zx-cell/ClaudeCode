"""
期权定价测试示例
"""

import sys
sys.path.append('..')

from pricing.black_scholes import BlackScholesModel, calculate_greeks, calculate_option_price
from pricing.implied_volatility import ImpliedVolatilityCalculator
import numpy as np


def test_option_pricing():
    """测试期权定价"""
    print("=" * 60)
    print("期权定价测试")
    print("=" * 60)

    # 参数
    S = 450  # 标的价格
    K = 455  # 行权价
    T = 45 / 365  # 45天到期
    r = 0.05  # 无风险利率5%
    sigma = 0.20  # 波动率20%

    # 计算看涨期权价格
    call_price = calculate_option_price(S, K, T, r, sigma, "call")
    print(f"\n看涨期权价格:")
    print(f"  标的价格: ${S}")
    print(f"  行权价: ${K}")
    print(f"  到期时间: {int(T*365)}天")
    print(f"  波动率: {sigma*100}%")
    print(f"  期权价格: ${call_price:.2f}")

    # 计算看跌期权价格
    put_price = calculate_option_price(S, K, T, r, sigma, "put")
    print(f"\n看跌期权价格:")
    print(f"  期权价格: ${put_price:.2f}")

    # 验证Put-Call Parity
    pcp_left = call_price - put_price
    pcp_right = S - K * np.exp(-r * T)
    print(f"\nPut-Call Parity验证:")
    print(f"  C - P = {pcp_left:.2f}")
    print(f"  S - K*e^(-rT) = {pcp_right:.2f}")
    print(f"  差异: {abs(pcp_left - pcp_right):.6f}")


def test_greeks():
    """测试Greeks计算"""
    print("\n" + "=" * 60)
    print("Greeks计算测试")
    print("=" * 60)

    S = 450
    K = 455
    T = 45 / 365
    r = 0.05
    sigma = 0.20

    # 计算看涨期权Greeks
    call_greeks = calculate_greeks(S, K, T, r, sigma, "call")
    print(f"\n看涨期权Greeks:")
    print(f"  Delta: {call_greeks['delta']:.4f}")
    print(f"  Gamma: {call_greeks['gamma']:.4f}")
    print(f"  Theta: {call_greeks['theta']:.4f} (per day)")
    print(f"  Vega: {call_greeks['vega']:.4f}")
    print(f"  Rho: {call_greeks['rho']:.4f}")

    # 计算看跌期权Greeks
    put_greeks = calculate_greeks(S, K, T, r, sigma, "put")
    print(f"\n看跌期权Greeks:")
    print(f"  Delta: {put_greeks['delta']:.4f}")
    print(f"  Gamma: {put_greeks['gamma']:.4f}")
    print(f"  Theta: {put_greeks['theta']:.4f} (per day)")
    print(f"  Vega: {put_greeks['vega']:.4f}")
    print(f"  Rho: {put_greeks['rho']:.4f}")


def test_implied_volatility():
    """测试隐含波动率计算"""
    print("\n" + "=" * 60)
    print("隐含波动率计算测试")
    print("=" * 60)

    S = 450
    K = 455
    T = 45 / 365
    r = 0.05
    sigma_true = 0.25  # 真实波动率

    # 先计算理论价格
    market_price = calculate_option_price(S, K, T, r, sigma_true, "call")
    print(f"\n给定市场价格: ${market_price:.2f}")
    print(f"真实波动率: {sigma_true*100}%")

    # 反推隐含波动率
    iv = ImpliedVolatilityCalculator.calculate_iv(
        market_price, S, K, T, r, "call"
    )

    if iv:
        print(f"计算得到的IV: {iv*100:.2f}%")
        print(f"误差: {abs(iv - sigma_true)*100:.4f}%")
    else:
        print("IV计算失败")


def test_iron_condor_pricing():
    """测试Iron Condor定价"""
    print("\n" + "=" * 60)
    print("Iron Condor策略定价")
    print("=" * 60)

    S = 450
    T = 45 / 365
    r = 0.05
    sigma = 0.20

    # Iron Condor腿
    short_call_strike = 460
    long_call_strike = 465
    short_put_strike = 440
    long_put_strike = 435

    # 计算每条腿的价格
    short_call_price = calculate_option_price(S, short_call_strike, T, r, sigma, "call")
    long_call_price = calculate_option_price(S, long_call_strike, T, r, sigma, "call")
    short_put_price = calculate_option_price(S, short_put_strike, T, r, sigma, "put")
    long_put_price = calculate_option_price(S, long_put_strike, T, r, sigma, "put")

    print(f"\n标的价格: ${S}")
    print(f"\nCall Side:")
    print(f"  卖出 {short_call_strike} Call @ ${short_call_price:.2f}")
    print(f"  买入 {long_call_strike} Call @ ${long_call_price:.2f}")

    print(f"\nPut Side:")
    print(f"  卖出 {short_put_strike} Put @ ${short_put_price:.2f}")
    print(f"  买入 {long_put_strike} Put @ ${long_put_price:.2f}")

    # 计算净收入
    net_credit = (short_call_price + short_put_price - long_call_price - long_put_price) * 100
    max_loss = 5 * 100 - net_credit  # 价差宽度 * 100 - 净收入

    print(f"\n策略分析:")
    print(f"  净收入: ${net_credit:.2f}")
    print(f"  最大损失: ${max_loss:.2f}")
    print(f"  风险收益比: 1:{net_credit/max_loss:.2f}")
    print(f"  盈亏平衡点: ${short_put_strike - net_credit/100:.2f} - ${short_call_strike + net_credit/100:.2f}")


if __name__ == "__main__":
    test_option_pricing()
    test_greeks()
    test_implied_volatility()
    test_iron_condor_pricing()

    print("\n" + "=" * 60)
    print("所有测试完成!")
    print("=" * 60)
