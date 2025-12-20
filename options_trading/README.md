# 期权交易系统 (Options Trading System)

基于富途API的美股期权波动率套利自动化交易系统。

## 📋 目录

- [系统简介](#系统简介)
- [核心功能](#核心功能)
- [策略介绍](#策略介绍)
- [系统架构](#系统架构)
- [安装指南](#安装指南)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [风险提示](#风险提示)

## 🎯 系统简介

这是一个专业的期权交易系统，通过波动率套利策略在美股大盘股期权市场中稳定获利。系统支持多种经典期权策略，包括：

- **Iron Condor（铁鹰式）** - 双边卖出虚值期权，获取时间价值
- **Credit Spread（信用价差）** - 单边价差策略
- **Butterfly（蝶式价差）** - 精确定价策略

## ✨ 核心功能

### 1. 多策略支持
- ✅ Iron Condor（铁鹰式）
- ✅ Bull Put Spread（牛市看跌价差）
- ✅ Bear Call Spread（熊市看涨价差）
- ✅ Butterfly Spread（蝶式价差）

### 2. 智能风险管理
- ✅ 单笔交易最大损失控制
- ✅ 组合总持仓限制
- ✅ 集中度风险控制
- ✅ Greeks实时监控
- ✅ 自动止盈止损

### 3. 期权定价引擎
- ✅ Black-Scholes模型
- ✅ Greeks计算（Delta, Gamma, Theta, Vega, Rho）
- ✅ 隐含波动率计算
- ✅ 历史波动率分析

### 4. 富途API集成
- ✅ 实时行情获取
- ✅ 期权链数据
- ✅ 账户管理
- ✅ 自动下单（支持仿真和实盘）

## 📊 策略介绍

### Iron Condor（铁鹰式）

**适用场景：** 低波动率市场，预期标的在一定区间内波动

**收益特点：**
- 最大收益：收到的净权利金
- 最大损失：价差宽度 - 净权利金
- 盈亏平衡点：卖出行权价 ± 净权利金

**策略构成：**
```
卖出虚值Call（Delta ≈ 0.20）
买入更虚值Call（保护）
卖出虚值Put（Delta ≈ -0.20）
买入更虚值Put（保护）
```

**示例：**
```
标的: SPY @ $450
卖出 455 Call @ $2.00
买入 460 Call @ $0.80
卖出 445 Put @ $2.00
买入 440 Put @ $0.80

净收入：$240（每份）
最大风险：$260（每份）
风险收益比：1:0.92
```

### Credit Spread（信用价差）

**适用场景：** 有方向性判断时使用

**Bull Put Spread（看涨）：**
- 卖出虚值Put
- 买入更虚值Put（保护）
- 预期标的上涨或持平

**Bear Call Spread（看跌）：**
- 卖出虚值Call
- 买入更虚值Call（保护）
- 预期标的下跌或持平

### Butterfly Spread（蝶式价差）

**适用场景：** 预期标的在到期时接近特定价格

**策略构成：**
```
买入1个低行权价期权
卖出2个ATM期权
买入1个高行权价期权
```

## 🏗️ 系统架构

```
options_trading/
├── __init__.py
├── config.py                    # 配置管理
├── main.py                      # 主程序入口
├── execution_engine.py          # 交易执行引擎
├── risk_management.py           # 风险管理
│
├── futu_api/                    # 富途API集成
│   ├── __init__.py
│   ├── client.py               # API客户端
│   ├── option_chain.py         # 期权链数据
│   └── data_fetcher.py         # 数据获取
│
├── pricing/                     # 期权定价
│   ├── __init__.py
│   ├── black_scholes.py        # BS模型
│   └── implied_volatility.py   # 隐含波动率
│
└── strategies/                  # 交易策略
    ├── __init__.py
    ├── base.py                 # 策略基类
    ├── iron_condor.py          # 铁鹰式
    ├── credit_spread.py        # 信用价差
    └── butterfly.py            # 蝶式价差
```

## 🚀 安装指南

### 1. 系统要求

- Python 3.8+
- 富途牛牛客户端 + OpenD
- 富途证券账户（港股/美股）

### 2. 安装步骤

```bash
# 1. 克隆或下载项目
cd ClaudeCode/options_trading

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑.env文件，填写富途API配置

# 4. 确保富途OpenD正在运行
# 打开富途牛牛 -> 设置 -> API -> 启动OpenD
```

### 3. 安装富途OpenD

1. 下载富途牛牛客户端：https://www.futunn.com/download
2. 登录账户
3. 开启API功能：设置 → API → 开启OpenD
4. 默认端口：11111

## 🎮 快速开始

### 1. 纸上交易（推荐先用仿真）

```bash
python run_options_trading.py --mode paper --once
```

### 2. 连续运行（每小时检查一次）

```bash
python run_options_trading.py --mode paper --interval 3600
```

### 3. 实盘交易（谨慎！）

```bash
python run_options_trading.py --mode live --interval 3600
```

### 参数说明

- `--mode`: 交易模式
  - `paper`: 纸上交易（仿真）
  - `live`: 实盘交易
- `--interval`: 交易周期间隔（秒），默认3600（1小时）
- `--once`: 只运行一次就退出

## ⚙️ 配置说明

### 环境变量配置 (.env)

```bash
# 富途API配置
FUTU_HOST=127.0.0.1          # OpenD地址
FUTU_PORT=11111              # OpenD端口
FUTU_TRADE_ENV=0             # 0=仿真, 1=真实
FUTU_TRADE_PWD_MD5=          # 交易密码MD5（真实交易需要）

# 风险控制
MAX_POSITION_VALUE=50000     # 单标的最大持仓（美元）
MAX_PORTFOLIO_VALUE=200000   # 组合最大持仓（美元）
```

### 代码配置 (config.py)

```python
# 交易标的（可自定义）
symbols = [
    "SPY",   # 标普500 ETF
    "QQQ",   # 纳斯达克100 ETF
    "IWM",   # 罗素2000 ETF
    "AAPL",  # 苹果
    "MSFT",  # 微软
    # ... 更多
]

# 期权参数
days_to_expiry_min = 30      # 最小到期天数
days_to_expiry_max = 60      # 最大到期天数

# Delta范围
delta_call_min = 0.15
delta_call_max = 0.30
delta_put_min = -0.30
delta_put_max = -0.15

# 风险参数
max_loss_per_trade = 1000    # 单笔最大亏损
profit_target_ratio = 0.5    # 利润目标（50%）
stop_loss_ratio = 2.0        # 止损比例

# 波动率筛选
iv_percentile_min = 30       # IV百分位最小值
iv_percentile_max = 70       # IV百分位最大值
```

## 📈 使用流程

### 典型交易流程

1. **系统启动**
   - 连接富途OpenD
   - 加载策略配置
   - 初始化风险管理

2. **扫描市场**
   - 遍历配置的标的列表
   - 获取实时行情和期权链
   - 计算IV百分位

3. **生成信号**
   - 每个策略独立分析
   - 筛选符合条件的期权
   - 构建策略组合

4. **风险检查**
   - 单笔交易风险检查
   - 组合风险检查
   - 集中度检查

5. **执行交易**
   - 通过富途API下单
   - 记录持仓信息
   - 监控仓位状态

6. **持仓管理**
   - 实时监控盈亏
   - 检查平仓条件
   - 自动止盈止损

## 🔒 风险控制

### 多层风险防护

1. **单笔交易限制**
   - 最大损失：$1,000
   - 最大持仓：$50,000

2. **组合限制**
   - 总持仓：$200,000
   - 持仓占账户比例：50%

3. **集中度控制**
   - 单一标的持仓数量 ≤ 30%
   - 每个标的最多2个仓位

4. **Greeks监控**
   - Delta中性：|Delta| < 100
   - Gamma控制：|Gamma| < 50

5. **自动止盈止损**
   - 利润目标：达到最大利润的50%
   - 止损：亏损超过收入的2倍

## ⚠️ 风险提示

**重要警告：期权交易具有高风险，可能导致全部本金损失！**

1. **市场风险**
   - 突发事件可能导致巨大波动
   - 黑天鹅事件风险
   - 流动性风险

2. **策略风险**
   - 波动率突然上升
   - 标的价格大幅波动
   - 隐含波动率偏斜

3. **技术风险**
   - API连接中断
   - 系统故障
   - 数据延迟

4. **使用建议**
   - ✅ 从仿真账户开始
   - ✅ 小资金测试
   - ✅ 严格遵守风险限制
   - ✅ 持续监控系统
   - ❌ 不要过度交易
   - ❌ 不要孤注一掷

## 📚 学习资源

### 推荐阅读

1. **期权基础**
   - 《Options as a Strategic Investment》
   - 《Option Volatility and Pricing》

2. **策略研究**
   - TastyTrade研究
   - CBOE白皮书

3. **风险管理**
   - 《Dynamic Hedging》
   - 《Risk Management and Financial Institutions》

### 在线资源

- [富途API文档](https://openapi.futunn.com/)
- [CBOE期权学院](https://www.cboe.com/education/)
- [TastyTrade](https://www.tastytrade.com/)

## 🛠️ 故障排查

### 常见问题

**Q1: 无法连接富途OpenD**
```
A: 检查：
1. 富途牛牛是否正在运行
2. OpenD是否已启动
3. 端口11111是否被占用
4. 防火墙设置
```

**Q2: 没有生成交易信号**
```
A: 检查：
1. IV百分位是否在范围内（30-70）
2. 期权链数据是否正常
3. 到期日范围是否合适（30-60天）
4. 查看日志详细信息
```

**Q3: 风险检查失败**
```
A: 检查：
1. 单笔交易最大损失限制
2. 账户资金是否充足
3. 是否超过组合限制
4. 查看风险管理日志
```

## 📞 支持与反馈

如有问题或建议，欢迎：
- 提交Issue
- 发起Pull Request
- 分享使用经验

## 📄 免责声明

本系统仅供学习和研究使用。使用本系统进行实盘交易的所有风险由使用者自行承担。作者不对任何交易损失负责。

**期权交易有风险，入市需谨慎！**

---

**祝交易顺利！ 📈**
