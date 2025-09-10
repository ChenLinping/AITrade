"""
简单入门示例：不依赖外部库的量化交易入门
展示量化交易的核心概念

这个示例只使用Python标准库，适合初学者理解基本概念
"""

import math
import random
from datetime import datetime, timedelta

def generate_sample_data(days=252):
    """
    生成示例股票数据
    
    参数:
        days: 生成的天数（默认252天，约一年的交易日）
        
    返回:
        list: 包含日期和价格的字典列表
    """
    print(f"生成 {days} 天的示例股票数据...")
    
    # 设置随机种子以获得可重复的结果
    random.seed(42)
    
    # 初始参数
    start_date = datetime(2023, 1, 1)
    start_price = 100.0
    annual_return = 0.08  # 8%年收益率
    annual_volatility = 0.20  # 20%年波动率
    
    # 日化参数
    daily_return = annual_return / 252
    daily_volatility = annual_volatility / math.sqrt(252)
    
    data = []
    current_price = start_price
    
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        
        # 跳过周末（简化处理）
        if current_date.weekday() >= 5:
            continue
        
        # 计算当日价格变化
        # 使用几何布朗运动模型
        random_factor = random.gauss(0, 1)  # 标准正态分布随机数
        price_change = daily_return + daily_volatility * random_factor
        
        # 更新价格
        current_price = current_price * (1 + price_change)
        
        # 生成OHLC数据（简化）
        high = current_price * (1 + abs(random.gauss(0, 0.01)))
        low = current_price * (1 - abs(random.gauss(0, 0.01)))
        open_price = data[-1]['close'] if data else current_price
        volume = random.randint(1000000, 10000000)
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(current_price, 2),
            'volume': volume
        })
    
    print(f"生成了 {len(data)} 天的数据")
    print(f"起始价格: ${data[0]['close']}")
    print(f"结束价格: ${data[-1]['close']}")
    print(f"总收益: {((data[-1]['close'] / data[0]['close']) - 1) * 100:.2f}%")
    
    return data

def calculate_moving_average(prices, window):
    """
    计算移动平均线
    
    参数:
        prices: 价格列表
        window: 移动平均窗口
        
    返回:
        list: 移动平均值列表
    """
    if len(prices) < window:
        return []
    
    moving_averages = []
    for i in range(window - 1, len(prices)):
        window_prices = prices[i - window + 1:i + 1]
        ma = sum(window_prices) / len(window_prices)
        moving_averages.append(round(ma, 2))
    
    return moving_averages

def calculate_rsi(prices, window=14):
    """
    计算RSI指标
    
    参数:
        prices: 价格列表
        window: RSI计算窗口
        
    返回:
        list: RSI值列表
    """
    if len(prices) < window + 1:
        return []
    
    # 计算价格变化
    price_changes = []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        price_changes.append(change)
    
    rsi_values = []
    
    for i in range(window - 1, len(price_changes)):
        # 获取窗口内的价格变化
        window_changes = price_changes[i - window + 1:i + 1]
        
        # 分离涨跌
        gains = [change if change > 0 else 0 for change in window_changes]
        losses = [-change if change < 0 else 0 for change in window_changes]
        
        # 计算平均涨跌幅
        avg_gain = sum(gains) / len(gains)
        avg_loss = sum(losses) / len(losses)
        
        # 避免除零
        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
        
        rsi_values.append(round(rsi, 2))
    
    return rsi_values

def moving_average_strategy(data, short_window=5, long_window=20):
    """
    移动平均交叉策略
    
    参数:
        data: 股票数据
        short_window: 短期移动平均窗口
        long_window: 长期移动平均窗口
        
    返回:
        dict: 包含信号和结果的字典
    """
    print(f"\n{'='*50}")
    print(f"移动平均策略 (短期{short_window}日 vs 长期{long_window}日)")
    print(f"{'='*50}")
    
    prices = [item['close'] for item in data]
    
    if len(prices) < long_window:
        print("数据不足，无法计算移动平均线")
        return {}
    
    # 计算移动平均线
    short_ma = calculate_moving_average(prices, short_window)
    long_ma = calculate_moving_average(prices, long_window)
    
    if not short_ma or not long_ma:
        print("数据不足，无法计算移动平均线")
        return {}
    
    # 生成交易信号
    signals = []
    position = 0  # 0: 无持仓, 1: 多头, -1: 空头
    trades = []
    
    # 从能够计算所有指标的位置开始
    for i in range(len(data)):
        # 计算当前的移动平均值
        if i < long_window - 1:
            continue  # 数据不足，跳过
            
        # 获取对应的移动平均值的索引
        short_ma_idx = i - short_window + 1
        long_ma_idx = i - long_window + 1
        
        if short_ma_idx < 0 or long_ma_idx < 0:
            continue
            
        current_short_ma = short_ma[short_ma_idx]
        current_long_ma = long_ma[long_ma_idx]
        current_price = prices[i]
        
        # 需要前一天的数据来判断交叉
        if i == long_window - 1:  # 第一个可用数据点
            signals.append('HOLD')
            continue
            
        prev_short_ma = short_ma[short_ma_idx - 1]
        prev_long_ma = long_ma[long_ma_idx - 1]
        
        # 金叉：短线上穿长线
        if prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma and position != 1:
            signals.append('BUY')
            position = 1
            trades.append({
                'date': data[i]['date'],
                'action': 'BUY',
                'price': current_price,
                'short_ma': current_short_ma,
                'long_ma': current_long_ma
            })
        
        # 死叉：短线下穿长线
        elif prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma and position != -1:
            signals.append('SELL')
            position = -1
            trades.append({
                'date': data[i]['date'],
                'action': 'SELL',
                'price': current_price,
                'short_ma': current_short_ma,
                'long_ma': current_long_ma
            })
        
        else:
            signals.append('HOLD')
    
    # 计算策略收益
    if len(trades) >= 2:
        returns = []
        for i in range(1, len(trades)):
            if trades[i-1]['action'] == 'BUY' and trades[i]['action'] == 'SELL':
                buy_price = trades[i-1]['price']
                sell_price = trades[i]['price']
                trade_return = (sell_price - buy_price) / buy_price
                returns.append(trade_return)
        
        if returns:
            total_return = sum(returns)
            avg_return = total_return / len(returns)
            win_rate = len([r for r in returns if r > 0]) / len(returns)
            
            print(f"交易统计:")
            print(f"  总交易次数: {len(trades)}")
            print(f"  完整交易对: {len(returns)}")
            print(f"  平均每笔收益: {avg_return * 100:.2f}%")
            print(f"  总收益: {total_return * 100:.2f}%")
            print(f"  胜率: {win_rate * 100:.1f}%")
        else:
            print("没有完整的交易对")
    else:
        print("交易信号不足")
    
    # 显示最近的交易信号
    print(f"\n最近5次交易信号:")
    for trade in trades[-5:]:
        print(f"  {trade['date']}: {trade['action']} @ ${trade['price']:.2f}")
    
    return {
        'signals': signals,
        'trades': trades,
        'short_ma': short_ma,
        'long_ma': long_ma
    }

def rsi_strategy(data, rsi_window=14, oversold=30, overbought=70):
    """
    RSI均值回归策略
    
    参数:
        data: 股票数据
        rsi_window: RSI计算窗口
        oversold: 超卖阈值
        overbought: 超买阈值
        
    返回:
        dict: 包含信号和结果的字典
    """
    print(f"\n{'='*50}")
    print(f"RSI策略 (周期{rsi_window}日, 超卖≤{oversold}, 超买≥{overbought})")
    print(f"{'='*50}")
    
    prices = [item['close'] for item in data]
    rsi_values = calculate_rsi(prices, rsi_window)
    
    if not rsi_values:
        print("数据不足，无法计算RSI")
        return {}
    
    # 生成交易信号
    signals = []
    trades = []
    position = 0
    
    for i, rsi in enumerate(rsi_values):
        data_index = i + rsi_window  # 对应到原始数据的索引
        current_price = prices[data_index]
        
        if rsi <= oversold and position != 1:
            signals.append('BUY')
            position = 1
            trades.append({
                'date': data[data_index]['date'],
                'action': 'BUY',
                'price': current_price,
                'rsi': rsi
            })
        elif rsi >= overbought and position != -1:
            signals.append('SELL')
            position = -1
            trades.append({
                'date': data[data_index]['date'],
                'action': 'SELL',
                'price': current_price,
                'rsi': rsi
            })
        else:
            signals.append('HOLD')
    
    # RSI统计
    avg_rsi = sum(rsi_values) / len(rsi_values)
    max_rsi = max(rsi_values)
    min_rsi = min(rsi_values)
    oversold_count = len([r for r in rsi_values if r <= oversold])
    overbought_count = len([r for r in rsi_values if r >= overbought])
    
    print(f"RSI统计:")
    print(f"  平均RSI: {avg_rsi:.2f}")
    print(f"  RSI范围: {min_rsi:.2f} - {max_rsi:.2f}")
    print(f"  超卖次数: {oversold_count} ({oversold_count/len(rsi_values)*100:.1f}%)")
    print(f"  超买次数: {overbought_count} ({overbought_count/len(rsi_values)*100:.1f}%)")
    print(f"  总交易信号: {len(trades)}")
    
    # 显示最近的交易信号
    print(f"\n最近5次交易信号:")
    for trade in trades[-5:]:
        print(f"  {trade['date']}: {trade['action']} @ ${trade['price']:.2f} (RSI: {trade['rsi']:.1f})")
    
    return {
        'signals': signals,
        'trades': trades,
        'rsi_values': rsi_values
    }

def analyze_performance(data, strategy_results):
    """
    分析策略表现
    
    参数:
        data: 原始股票数据
        strategy_results: 策略结果字典
    """
    print(f"\n{'='*50}")
    print("综合表现分析")
    print(f"{'='*50}")
    
    prices = [item['close'] for item in data]
    start_price = prices[0]
    end_price = prices[-1]
    market_return = (end_price - start_price) / start_price
    
    print(f"市场表现:")
    print(f"  期间: {data[0]['date']} 至 {data[-1]['date']}")
    print(f"  起始价格: ${start_price:.2f}")
    print(f"  结束价格: ${end_price:.2f}")
    print(f"  买入持有收益: {market_return * 100:.2f}%")
    
    # 计算日收益率
    daily_returns = []
    for i in range(1, len(prices)):
        daily_return = (prices[i] - prices[i-1]) / prices[i-1]
        daily_returns.append(daily_return)
    
    # 计算波动率
    if daily_returns:
        avg_daily_return = sum(daily_returns) / len(daily_returns)
        variance = sum([(r - avg_daily_return) ** 2 for r in daily_returns]) / len(daily_returns)
        volatility = math.sqrt(variance * 252)  # 年化波动率
        
        print(f"  年化波动率: {volatility * 100:.2f}%")
        
        # 计算最大回撤
        cumulative_returns = [1]
        for daily_return in daily_returns:
            cumulative_returns.append(cumulative_returns[-1] * (1 + daily_return))
        
        max_value = cumulative_returns[0]
        max_drawdown = 0
        
        for value in cumulative_returns:
            if value > max_value:
                max_value = value
            else:
                drawdown = (max_value - value) / max_value
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
        
        print(f"  最大回撤: {max_drawdown * 100:.2f}%")

def main():
    """主函数"""
    print("欢迎使用 AITrade 量化交易入门示例！")
    print("="*60)
    print("这个示例将向您展示量化交易的基本概念：")
    print("1. 股票数据的生成和处理")
    print("2. 技术指标的计算")
    print("3. 交易策略的实现")
    print("4. 策略表现的分析")
    print("="*60)
    
    # 1. 生成示例数据
    print("\n步骤1: 生成股票数据")
    stock_data = generate_sample_data(days=300)
    
    # 2. 分析市场表现
    print("\n步骤2: 分析市场基本情况")
    analyze_performance(stock_data, {})
    
    # 3. 测试移动平均策略
    print("\n步骤3: 测试移动平均策略")
    ma_results = moving_average_strategy(stock_data, short_window=5, long_window=20)
    
    # 4. 测试RSI策略
    print("\n步骤4: 测试RSI策略")
    rsi_results = rsi_strategy(stock_data, rsi_window=14, oversold=30, overbought=70)
    
    # 5. 学习建议
    print(f"\n{'='*60}")
    print("学习建议和下一步")
    print(f"{'='*60}")
    print("恭喜！您已经完成了第一个量化交易程序。")
    print()
    print("关键概念回顾:")
    print("1. 移动平均策略：利用短期和长期趋势的交叉信号")
    print("2. RSI策略：利用超买超卖情况的均值回归特性")
    print("3. 回测：用历史数据验证策略的有效性")
    print()
    print("接下来您可以：")
    print("1. 修改策略参数，观察对结果的影响")
    print("2. 尝试组合多个策略的信号")
    print("3. 添加止损止盈机制")
    print("4. 学习更多技术指标（MACD、布林带等）")
    print("5. 了解风险管理和仓位控制")
    print()
    print("学习路径：")
    print("- 完成 tutorials/01_python_basics/ 中的Python基础教程")
    print("- 安装pandas等库：pip install -r requirements.txt")
    print("- 运行 examples/getting_started.py 体验完整功能")
    print("- 阅读金融和量化交易相关书籍")
    print()
    print("重要提醒：")
    print("⚠️  本示例仅用于学习目的，实际投资前请：")
    print("   - 充分理解策略原理和风险")
    print("   - 进行更全面的回测和验证")
    print("   - 考虑交易成本和滑点")
    print("   - 制定合理的风险管理策略")
    print("   - 从小金额开始实盘测试")

if __name__ == "__main__":
    main()