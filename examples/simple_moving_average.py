"""
简单移动平均策略示例
展示经典的移动平均交叉策略

这个示例演示：
1. 移动平均线的计算
2. 金叉死叉信号的识别
3. 策略回测和评估
4. 可视化结果展示
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import random
import math
from datetime import datetime, timedelta

def generate_trending_data(days=252, trend_strength=0.1):
    """
    生成带趋势的股票数据
    
    参数:
        days: 生成天数
        trend_strength: 趋势强度
    """
    print(f"生成 {days} 天的趋势性股票数据...")
    
    random.seed(42)
    
    # 基础参数
    start_price = 100.0
    start_date = datetime(2023, 1, 1)
    
    data = []
    current_price = start_price
    
    for i in range(days):
        # 计算日期（跳过周末）
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() >= 5:
            continue
        
        # 添加趋势分量
        trend_factor = 1 + (trend_strength * i / days)
        
        # 添加随机波动
        random_factor = 1 + random.gauss(0, 0.02)  # 2%日波动
        
        # 计算新价格
        current_price = start_price * trend_factor * random_factor
        
        # 生成OHLC数据
        open_price = data[-1]['close'] if data else current_price
        high = current_price * (1 + abs(random.gauss(0, 0.01)))
        low = current_price * (1 - abs(random.gauss(0, 0.01)))
        volume = random.randint(1000000, 5000000)
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(current_price, 2),
            'volume': volume
        })
    
    print(f"生成了 {len(data)} 天的数据")
    print(f"价格从 ${data[0]['close']} 到 ${data[-1]['close']}")
    print(f"总趋势: {((data[-1]['close'] / data[0]['close']) - 1) * 100:.2f}%")
    
    return data

def calculate_moving_averages(prices, short_window=5, long_window=20):
    """
    计算移动平均线
    
    参数:
        prices: 价格列表
        short_window: 短期窗口
        long_window: 长期窗口
    
    返回:
        tuple: (短期移动平均, 长期移动平均)
    """
    short_ma = []
    long_ma = []
    
    for i in range(len(prices)):
        # 短期移动平均
        if i >= short_window - 1:
            short_avg = sum(prices[i-short_window+1:i+1]) / short_window
            short_ma.append(round(short_avg, 2))
        else:
            short_ma.append(None)
        
        # 长期移动平均
        if i >= long_window - 1:
            long_avg = sum(prices[i-long_window+1:i+1]) / long_window
            long_ma.append(round(long_avg, 2))
        else:
            long_ma.append(None)
    
    return short_ma, long_ma

def generate_trading_signals(data, short_ma, long_ma):
    """
    生成交易信号
    
    参数:
        data: 股票数据
        short_ma: 短期移动平均
        long_ma: 长期移动平均
    
    返回:
        list: 交易信号列表
    """
    signals = []
    position = 0  # 0: 无持仓, 1: 多头, -1: 空头
    
    for i in range(1, len(data)):
        # 需要两条移动平均线都有值
        if short_ma[i] is None or long_ma[i] is None:
            continue
        if short_ma[i-1] is None or long_ma[i-1] is None:
            continue
        
        # 当前和前一日的移动平均
        curr_short = short_ma[i]
        curr_long = long_ma[i]
        prev_short = short_ma[i-1]
        prev_long = long_ma[i-1]
        
        current_price = data[i]['close']
        signal_type = None
        
        # 金叉：短线上穿长线
        if prev_short <= prev_long and curr_short > curr_long and position <= 0:
            signal_type = 'BUY'
            position = 1
        
        # 死叉：短线下穿长线
        elif prev_short >= prev_long and curr_short < curr_long and position >= 0:
            signal_type = 'SELL' 
            position = -1
        
        if signal_type:
            signals.append({
                'date': data[i]['date'],
                'price': current_price,
                'signal': signal_type,
                'short_ma': curr_short,
                'long_ma': curr_long,
                'index': i
            })
    
    return signals

def backtest_strategy(data, signals):
    """
    回测移动平均策略
    
    参数:
        data: 股票数据
        signals: 交易信号
    
    返回:
        dict: 回测结果
    """
    print("\n=== 策略回测 ===")
    
    if len(signals) < 2:
        print("交易信号不足，无法进行回测")
        return {}
    
    # 计算交易收益
    trades = []
    entry_price = None
    entry_date = None
    
    for signal in signals:
        if signal['signal'] == 'BUY':
            entry_price = signal['price']
            entry_date = signal['date']
        elif signal['signal'] == 'SELL' and entry_price is not None:
            # 计算这次交易的收益
            exit_price = signal['price']
            exit_date = signal['date']
            trade_return = (exit_price - entry_price) / entry_price
            
            trades.append({
                'entry_date': entry_date,
                'entry_price': entry_price,
                'exit_date': exit_date,
                'exit_price': exit_price,
                'return': trade_return,
                'return_pct': trade_return * 100
            })
            
            entry_price = None
            entry_date = None
    
    if not trades:
        print("没有完整的交易周期")
        return {}
    
    # 计算策略统计
    returns = [trade['return'] for trade in trades]
    total_return = sum(returns)
    avg_return = total_return / len(returns)
    winning_trades = [r for r in returns if r > 0]
    losing_trades = [r for r in returns if r < 0]
    
    win_rate = len(winning_trades) / len(returns)
    avg_win = sum(winning_trades) / len(winning_trades) if winning_trades else 0
    avg_loss = sum(losing_trades) / len(losing_trades) if losing_trades else 0
    
    # 计算买入持有收益
    buy_hold_return = (data[-1]['close'] - data[0]['close']) / data[0]['close']
    
    # 显示结果
    print(f"回测期间: {data[0]['date']} 至 {data[-1]['date']}")
    print(f"总交易次数: {len(signals)}")
    print(f"完整交易周期: {len(trades)}")
    print(f"策略总收益: {total_return * 100:.2f}%")
    print(f"买入持有收益: {buy_hold_return * 100:.2f}%")
    print(f"超额收益: {(total_return - buy_hold_return) * 100:.2f}%")
    print(f"胜率: {win_rate * 100:.1f}%")
    print(f"平均盈利: {avg_win * 100:.2f}%")
    print(f"平均亏损: {avg_loss * 100:.2f}%")
    
    if avg_loss != 0:
        profit_loss_ratio = abs(avg_win / avg_loss)
        print(f"盈亏比: {profit_loss_ratio:.2f}")
    
    return {
        'total_return': total_return,
        'buy_hold_return': buy_hold_return,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'trades': trades,
        'num_trades': len(trades)
    }

def show_trade_details(trades, max_show=10):
    """显示交易明细"""
    print(f"\n=== 交易明细 (显示前{min(max_show, len(trades))}笔) ===")
    print("进场日期    | 进场价格 | 出场日期    | 出场价格 | 收益率")
    print("-" * 55)
    
    for i, trade in enumerate(trades[:max_show]):
        print(f"{trade['entry_date']} | ${trade['entry_price']:8.2f} | "
              f"{trade['exit_date']} | ${trade['exit_price']:8.2f} | "
              f"{trade['return_pct']:+6.2f}%")

def analyze_parameter_sensitivity(data):
    """参数敏感性分析"""
    print("\n=== 参数敏感性分析 ===")
    
    prices = [item['close'] for item in data]
    parameter_sets = [
        (3, 10), (5, 15), (5, 20), (10, 30), (20, 50)
    ]
    
    results = []
    
    for short_window, long_window in parameter_sets:
        short_ma, long_ma = calculate_moving_averages(prices, short_window, long_window)
        signals = generate_trading_signals(data, short_ma, long_ma)
        
        if len(signals) >= 2:
            backtest_result = backtest_strategy(data, signals)
            if backtest_result:
                results.append({
                    'params': f"({short_window},{long_window})",
                    'total_return': backtest_result['total_return'] * 100,
                    'win_rate': backtest_result['win_rate'] * 100,
                    'num_trades': backtest_result['num_trades']
                })
    
    if results:
        print("参数组合     | 总收益率 | 胜率   | 交易次数")
        print("-" * 40)
        for result in results:
            print(f"{result['params']:12} | {result['total_return']:+7.2f}% | "
                  f"{result['win_rate']:5.1f}% | {result['num_trades']:8}")

def create_simple_chart(data, short_ma, long_ma, signals):
    """创建简单的文本图表"""
    print("\n=== 价格走势图 (最近30天) ===")
    
    # 获取最近30天的数据
    recent_days = min(30, len(data))
    start_idx = len(data) - recent_days
    
    print("日期       | 价格    | 短MA   | 长MA   | 信号")
    print("-" * 50)
    
    for i in range(start_idx, len(data)):
        date = data[i]['date']
        price = data[i]['close']
        short_val = short_ma[i] if short_ma[i] else "N/A"
        long_val = long_ma[i] if long_ma[i] else "N/A"
        
        # 查找是否有信号
        signal_text = ""
        for signal in signals:
            if signal['index'] == i:
                signal_text = f"📈{signal['signal']}" if signal['signal'] == 'BUY' else f"📉{signal['signal']}"
                break
        
        print(f"{date} | ${price:7.2f} | {short_val!s:6} | {long_val!s:6} | {signal_text}")

def main():
    """主函数"""
    print("简单移动平均策略示例")
    print("=" * 50)
    
    # 1. 生成数据
    stock_data = generate_trending_data(days=180, trend_strength=0.15)
    
    # 2. 设置策略参数
    short_window = 5   # 5日移动平均
    long_window = 20   # 20日移动平均
    
    print(f"\n策略参数: 短期MA={short_window}日, 长期MA={long_window}日")
    
    # 3. 计算移动平均
    prices = [item['close'] for item in stock_data]
    short_ma, long_ma = calculate_moving_averages(prices, short_window, long_window)
    
    # 4. 生成交易信号
    signals = generate_trading_signals(stock_data, short_ma, long_ma)
    
    print(f"\n生成了 {len(signals)} 个交易信号:")
    for signal in signals[:10]:  # 显示前10个信号
        print(f"  {signal['date']}: {signal['signal']} @ ${signal['price']:.2f}")
    if len(signals) > 10:
        print(f"  ... 还有 {len(signals) - 10} 个信号")
    
    # 5. 策略回测
    backtest_result = backtest_strategy(stock_data, signals)
    
    # 6. 显示交易明细
    if backtest_result and 'trades' in backtest_result:
        show_trade_details(backtest_result['trades'])
    
    # 7. 参数敏感性分析
    analyze_parameter_sensitivity(stock_data)
    
    # 8. 简单图表
    create_simple_chart(stock_data, short_ma, long_ma, signals)
    
    # 9. 学习总结
    print("\n" + "=" * 50)
    print("学习总结")
    print("=" * 50)
    print("移动平均策略的核心概念:")
    print("1. 金叉 (Golden Cross): 短期MA上穿长期MA → 买入信号")
    print("2. 死叉 (Death Cross): 短期MA下穿长期MA → 卖出信号")
    print("3. 趋势跟踪: 适合有明确趋势的市场")
    print("4. 参数敏感性: 不同参数组合会产生不同结果")
    print("\n策略优缺点:")
    print("✅ 优点: 逻辑简单、易于理解、适合趋势市场")
    print("❌ 缺点: 滞后性、震荡市场容易产生假信号")
    print("\n改进方向:")
    print("- 添加成交量确认")
    print("- 结合其他技术指标")
    print("- 添加止损止盈机制")
    print("- 考虑交易成本")

if __name__ == "__main__":
    main()