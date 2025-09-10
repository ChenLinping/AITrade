"""
基础数据获取示例
演示如何获取和处理股票数据

这个示例展示：
1. 使用yfinance获取真实股票数据
2. 数据的基本处理和分析
3. 简单的数据可视化
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

def create_sample_data_without_libs():
    """
    不依赖外部库创建示例数据
    适合初学者理解数据结构
    """
    print("=== 创建示例股票数据 ===")
    
    import random
    from datetime import datetime, timedelta
    
    # 设置随机种子
    random.seed(42)
    
    # 生成日期序列
    start_date = datetime(2023, 1, 1)
    dates = []
    for i in range(100):  # 100个交易日
        current_date = start_date + timedelta(days=i)
        # 跳过周末
        if current_date.weekday() < 5:
            dates.append(current_date.strftime('%Y-%m-%d'))
    
    # 生成价格数据
    base_price = 100.0
    prices = []
    
    for i in range(len(dates)):
        # 模拟价格波动
        change_percent = random.uniform(-0.03, 0.03)  # ±3%的日波动
        if i == 0:
            price = base_price
        else:
            price = prices[-1] * (1 + change_percent)
        prices.append(round(price, 2))
    
    # 创建数据字典
    stock_data = []
    for i, date in enumerate(dates):
        price = prices[i]
        stock_data.append({
            'date': date,
            'open': round(price * random.uniform(0.995, 1.005), 2),
            'high': round(price * random.uniform(1.0, 1.02), 2),
            'low': round(price * random.uniform(0.98, 1.0), 2),
            'close': price,
            'volume': random.randint(1000000, 10000000)
        })
    
    return stock_data

def analyze_basic_data(data):
    """分析基础数据统计"""
    print("\n=== 基础数据分析 ===")
    
    if not data:
        print("没有数据可分析")
        return
    
    prices = [item['close'] for item in data]
    volumes = [item['volume'] for item in data]
    
    print(f"数据期间: {data[0]['date']} 到 {data[-1]['date']}")
    print(f"交易天数: {len(data)}")
    print(f"价格统计:")
    print(f"  起始价格: ${prices[0]:.2f}")
    print(f"  结束价格: ${prices[-1]:.2f}")
    print(f"  最高价格: ${max(prices):.2f}")
    print(f"  最低价格: ${min(prices):.2f}")
    print(f"  平均价格: ${sum(prices)/len(prices):.2f}")
    print(f"  总收益率: {((prices[-1] / prices[0]) - 1) * 100:.2f}%")
    
    print(f"成交量统计:")
    print(f"  平均成交量: {sum(volumes)//len(volumes):,}")
    print(f"  最大成交量: {max(volumes):,}")
    print(f"  最小成交量: {min(volumes):,}")

def calculate_technical_indicators_simple(data):
    """计算简单技术指标"""
    print("\n=== 技术指标计算 ===")
    
    prices = [item['close'] for item in data]
    
    # 5日移动平均
    ma5 = []
    for i in range(len(prices)):
        if i >= 4:  # 需要5个数据点
            avg = sum(prices[i-4:i+1]) / 5
            ma5.append(round(avg, 2))
        else:
            ma5.append(None)
    
    # 20日移动平均
    ma20 = []
    for i in range(len(prices)):
        if i >= 19:  # 需要20个数据点
            avg = sum(prices[i-19:i+1]) / 20
            ma20.append(round(avg, 2))
        else:
            ma20.append(None)
    
    # 计算日收益率
    daily_returns = []
    for i in range(1, len(prices)):
        ret = (prices[i] - prices[i-1]) / prices[i-1]
        daily_returns.append(round(ret * 100, 3))
    
    # 显示最近的指标
    print("最近10日数据和指标:")
    print("日期       | 收盘价  | 5日MA   | 20日MA  | 日收益率%")
    print("-" * 55)
    
    for i in range(max(0, len(data)-10), len(data)):
        date = data[i]['date']
        price = prices[i]
        ma5_val = ma5[i] if ma5[i] else "N/A"
        ma20_val = ma20[i] if ma20[i] else "N/A"
        
        if i > 0:
            ret = daily_returns[i-1]
            ret_str = f"{ret:+.2f}%"
        else:
            ret_str = "N/A"
        
        print(f"{date} | ${price:7.2f} | {ma5_val!s:7} | {ma20_val!s:7} | {ret_str:8}")
    
    return {
        'ma5': ma5,
        'ma20': ma20,
        'daily_returns': daily_returns
    }

def simple_trading_signals(data, indicators):
    """生成简单交易信号"""
    print("\n=== 交易信号生成 ===")
    
    ma5 = indicators['ma5']
    ma20 = indicators['ma20']
    prices = [item['close'] for item in data]
    
    signals = []
    for i in range(len(data)):
        if ma5[i] and ma20[i] and i > 0:
            # 前一日的移动平均
            prev_ma5 = ma5[i-1] if ma5[i-1] else ma5[i]
            prev_ma20 = ma20[i-1] if ma20[i-1] else ma20[i]
            
            # 当前移动平均
            curr_ma5 = ma5[i]
            curr_ma20 = ma20[i]
            
            # 金叉信号：5日线上穿20日线
            if prev_ma5 <= prev_ma20 and curr_ma5 > curr_ma20:
                signals.append({
                    'date': data[i]['date'],
                    'price': prices[i],
                    'signal': 'BUY',
                    'reason': '5日线上穿20日线（金叉）'
                })
            # 死叉信号：5日线下穿20日线
            elif prev_ma5 >= prev_ma20 and curr_ma5 < curr_ma20:
                signals.append({
                    'date': data[i]['date'],
                    'price': prices[i],
                    'signal': 'SELL',
                    'reason': '5日线下穿20日线（死叉）'
                })
    
    print(f"共生成 {len(signals)} 个交易信号:")
    for signal in signals:
        print(f"  {signal['date']}: {signal['signal']:4} @ ${signal['price']:.2f} - {signal['reason']}")
    
    return signals

def try_with_real_data():
    """尝试使用真实数据（需要yfinance库）"""
    print("\n=== 尝试获取真实股票数据 ===")
    
    try:
        import yfinance as yf
        import pandas as pd
        
        print("正在获取苹果公司(AAPL)最近3个月的数据...")
        
        # 获取数据
        ticker = yf.Ticker("AAPL")
        data = ticker.history(period="3mo")
        
        if not data.empty:
            print(f"成功获取 {len(data)} 条真实数据！")
            print("\n最近5日数据:")
            print(data[['Open', 'High', 'Low', 'Close', 'Volume']].tail())
            
            # 计算简单统计
            close_prices = data['Close']
            print(f"\n价格统计:")
            print(f"  期间: {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}")
            print(f"  起始价格: ${close_prices.iloc[0]:.2f}")
            print(f"  结束价格: ${close_prices.iloc[-1]:.2f}")
            print(f"  最高价格: ${close_prices.max():.2f}")
            print(f"  最低价格: ${close_prices.min():.2f}")
            print(f"  总收益率: {((close_prices.iloc[-1] / close_prices.iloc[0]) - 1) * 100:.2f}%")
            
            return True
        else:
            print("获取数据失败，使用示例数据代替")
            return False
            
    except ImportError:
        print("yfinance库未安装，使用示例数据")
        print("要获取真实数据，请安装: pip install yfinance pandas")
        return False
    except Exception as e:
        print(f"获取真实数据时出错: {e}")
        print("使用示例数据代替")
        return False

def export_data_to_csv(data, filename="sample_stock_data.csv"):
    """导出数据到CSV文件"""
    print(f"\n=== 导出数据到 {filename} ===")
    
    try:
        # 手动创建CSV内容
        csv_content = ["date,open,high,low,close,volume"]
        
        for item in data:
            line = f"{item['date']},{item['open']},{item['high']},{item['low']},{item['close']},{item['volume']}"
            csv_content.append(line)
        
        # 写入文件
        file_path = os.path.join(os.path.dirname(__file__), filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(csv_content))
        
        print(f"数据已保存到: {file_path}")
        print(f"您可以用Excel或其他工具打开查看")
        
    except Exception as e:
        print(f"导出数据时出错: {e}")

def main():
    """主函数"""
    print("欢迎使用基础数据获取示例！")
    print("="*50)
    
    # 1. 尝试获取真实数据
    real_data_success = try_with_real_data()
    
    # 2. 如果真实数据获取失败，使用示例数据
    if not real_data_success:
        print("\n使用示例数据进行演示...")
        stock_data = create_sample_data_without_libs()
        
        # 3. 分析数据
        analyze_basic_data(stock_data)
        
        # 4. 计算技术指标
        indicators = calculate_technical_indicators_simple(stock_data)
        
        # 5. 生成交易信号
        signals = simple_trading_signals(stock_data, indicators)
        
        # 6. 导出数据
        export_data_to_csv(stock_data)
    
    # 7. 学习建议
    print("\n" + "="*50)
    print("学习建议")
    print("="*50)
    print("1. 理解数据结构：观察股票数据的OHLCV格式")
    print("2. 技术指标计算：理解移动平均线的计算方法")
    print("3. 信号生成逻辑：学习金叉死叉的判断条件")
    print("4. 数据处理：练习处理和分析时间序列数据")
    print("5. 安装真实数据库：pip install yfinance pandas matplotlib")
    print("\n下一步：")
    print("- 运行 examples/simple_start.py 学习完整策略")
    print("- 尝试修改移动平均参数，观察信号变化")
    print("- 学习更多技术指标（RSI、MACD等）")

if __name__ == "__main__":
    main()