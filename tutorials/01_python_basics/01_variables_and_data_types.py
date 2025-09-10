"""
Python基础教程 1: 变量和数据类型
适合量化交易的Python基础知识
"""

# 1. 变量定义和基本数据类型
print("=== Python基础：变量和数据类型 ===\n")

# 数字类型 - 在量化交易中用于价格、数量、比率等
stock_price = 100.50  # 浮点数 - 股票价格
shares = 100          # 整数 - 股票数量
commission_rate = 0.001  # 浮点数 - 手续费率

print(f"股票价格: ${stock_price}")
print(f"股票数量: {shares} 股")
print(f"手续费率: {commission_rate * 100}%")

# 字符串类型 - 用于股票代码、策略名称等
stock_symbol = "AAPL"  # 股票代码
strategy_name = "移动平均策略"  # 策略名称

print(f"\n正在分析股票: {stock_symbol}")
print(f"使用策略: {strategy_name}")

# 布尔类型 - 用于交易信号、条件判断
is_bull_market = True   # 是否牛市
should_buy = False      # 是否应该买入

print(f"\n当前是牛市: {is_bull_market}")
print(f"建议买入: {should_buy}")

# 列表类型 - 用于存储多个股票、价格序列等
stock_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]  # 股票组合
daily_prices = [150.0, 152.5, 149.8, 153.2, 155.1]  # 每日价格

print(f"\n投资组合: {stock_symbols}")
print(f"最近5日价格: {daily_prices}")

# 字典类型 - 用于存储股票信息
stock_info = {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "price": 150.25,
    "volume": 1000000,
    "market_cap": "2.5T"
}

print(f"\n股票信息:")
for key, value in stock_info.items():
    print(f"  {key}: {value}")

# 2. 基本运算 - 量化交易中的常用计算
print("\n=== 基本运算示例 ===")

# 投资收益计算
initial_investment = 10000  # 初始投资额
current_value = 12500       # 当前价值
profit = current_value - initial_investment
profit_rate = (profit / initial_investment) * 100

print(f"初始投资: ${initial_investment}")
print(f"当前价值: ${current_value}")
print(f"盈利金额: ${profit}")
print(f"收益率: {profit_rate:.2f}%")

# 手续费计算
trade_amount = 5000  # 交易金额
commission = trade_amount * commission_rate
net_amount = trade_amount - commission

print(f"\n交易金额: ${trade_amount}")
print(f"手续费: ${commission:.2f}")
print(f"净交易额: ${net_amount:.2f}")

# 3. 条件判断 - 交易决策逻辑
print("\n=== 条件判断示例 ===")

current_price = 155.0
buy_threshold = 150.0
sell_threshold = 160.0

# 简单的交易信号判断
if current_price < buy_threshold:
    signal = "买入"
    reason = f"价格低于买入阈值 ${buy_threshold}"
elif current_price > sell_threshold:
    signal = "卖出"
    reason = f"价格高于卖出阈值 ${sell_threshold}"
else:
    signal = "持有"
    reason = "价格在正常范围内"

print(f"当前价格: ${current_price}")
print(f"交易信号: {signal}")
print(f"判断理由: {reason}")

# 4. 循环 - 处理时间序列数据
print("\n=== 循环处理数据示例 ===")

# 计算移动平均
prices = [100, 102, 101, 103, 105, 104, 106, 108, 107, 109]
window = 3  # 3日移动平均

print(f"原始价格序列: {prices}")
print(f"{window}日移动平均:")

moving_averages = []
for i in range(len(prices) - window + 1):
    window_prices = prices[i:i + window]
    ma = sum(window_prices) / len(window_prices)
    moving_averages.append(round(ma, 2))
    print(f"  第{i+window}日: {ma:.2f} (基于 {window_prices})")

# 5. 函数定义 - 可重用的计算逻辑
print("\n=== 函数定义示例 ===")

def calculate_return(start_price, end_price):
    """计算投资收益率"""
    return ((end_price - start_price) / start_price) * 100

def calculate_moving_average(prices, window):
    """计算移动平均线"""
    if len(prices) < window:
        return None
    return sum(prices[-window:]) / window

def generate_signal(current_price, ma_short, ma_long):
    """生成交易信号"""
    if ma_short > ma_long and current_price > ma_short:
        return "强买入"
    elif ma_short > ma_long:
        return "买入"
    elif ma_short < ma_long and current_price < ma_short:
        return "强卖出"
    elif ma_short < ma_long:
        return "卖出"
    else:
        return "观望"

# 使用函数
start_price = 100
end_price = 120
return_rate = calculate_return(start_price, end_price)
print(f"从 ${start_price} 到 ${end_price} 的收益率: {return_rate:.2f}%")

# 计算不同周期的移动平均
recent_prices = [105, 106, 107, 108, 109, 110, 111]
ma_5 = calculate_moving_average(recent_prices, 5)
ma_10 = calculate_moving_average(recent_prices, 10)

print(f"5日移动平均: {ma_5:.2f}")
if ma_10:
    print(f"10日移动平均: {ma_10:.2f}")
else:
    print("数据不足，无法计算10日移动平均")

# 生成交易信号
signal = generate_signal(111, ma_5, 105)  # 假设长期均线为105
print(f"交易信号: {signal}")

print("\n=== 学习总结 ===")
print("1. 掌握了Python基本数据类型在量化交易中的应用")
print("2. 学会了基本运算和条件判断")
print("3. 了解了如何使用循环处理价格数据")
print("4. 学会了定义函数来封装交易逻辑")
print("\n下一步：学习数据分析库 pandas 和 numpy 的使用！")