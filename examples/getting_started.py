"""
入门示例：第一个量化交易程序
展示如何使用AITrade项目的基本功能

这个示例将教您：
1. 如何获取股票数据
2. 如何计算技术指标
3. 如何应用交易策略
4. 如何分析策略结果
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# 导入我们创建的模块（注意：实际运行需要安装相应的库）
try:
    from src.data.data_fetcher import DataFetcher, TechnicalIndicators, DataAnalyzer
    from src.strategies.moving_average_strategy import MovingAverageStrategy
    from src.strategies.rsi_strategy import RSIStrategy
    modules_available = True
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("这是正常的，因为某些依赖库可能尚未安装")
    print("请先运行: pip install -r requirements.txt")
    modules_available = False

def create_sample_data():
    """创建示例数据用于演示"""
    print("创建示例股票数据...")
    
    # 创建日期范围
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    dates = dates[dates.weekday < 5]  # 只保留工作日
    
    # 生成模拟股票价格（带趋势和波动）
    np.random.seed(42)
    
    # 基础价格和趋势
    base_price = 100
    trend = np.linspace(0, 0.5, len(dates))  # 50%的年度涨幅趋势
    
    # 添加波动性
    volatility = 0.02  # 2%的日波动率
    daily_returns = np.random.normal(0, volatility, len(dates))
    
    # 计算价格序列
    prices = [base_price]
    for i in range(1, len(dates)):
        trend_factor = 1 + trend[i] / 252  # 日化趋势
        random_factor = 1 + daily_returns[i]
        new_price = prices[-1] * trend_factor * random_factor
        prices.append(new_price)
    
    # 创建OHLCV数据
    data = pd.DataFrame({
        'Date': dates,
        'Open': np.roll(prices, 1),  # 前一日收盘价作为开盘价
        'High': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
        'Low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
        'Close': prices,
        'Volume': np.random.randint(1000000, 10000000, len(dates))
    })
    
    data['Open'].iloc[0] = data['Close'].iloc[0]  # 修正第一天的开盘价
    data.set_index('Date', inplace=True)
    
    print(f"生成了 {len(data)} 天的股票数据")
    print(f"价格范围: ${data['Close'].min():.2f} - ${data['Close'].max():.2f}")
    print(f"总收益: {((data['Close'].iloc[-1] / data['Close'].iloc[0]) - 1) * 100:.2f}%")
    
    return data

def analyze_basic_statistics(data):
    """分析基础统计信息"""
    print("\n" + "="*50)
    print("基础统计分析")
    print("="*50)
    
    close_prices = data['Close']
    daily_returns = close_prices.pct_change().dropna()
    
    print(f"数据期间: {data.index[0].strftime('%Y-%m-%d')} 到 {data.index[-1].strftime('%Y-%m-%d')}")
    print(f"交易天数: {len(data)}")
    print(f"起始价格: ${close_prices.iloc[0]:.2f}")
    print(f"结束价格: ${close_prices.iloc[-1]:.2f}")
    print(f"最高价格: ${close_prices.max():.2f}")
    print(f"最低价格: ${close_prices.min():.2f}")
    print(f"平均价格: ${close_prices.mean():.2f}")
    
    print(f"\n收益率统计:")
    print(f"总收益率: {((close_prices.iloc[-1] / close_prices.iloc[0]) - 1) * 100:.2f}%")
    print(f"平均日收益率: {daily_returns.mean() * 100:.3f}%")
    print(f"收益率标准差: {daily_returns.std() * 100:.3f}%")
    print(f"年化波动率: {daily_returns.std() * np.sqrt(252) * 100:.2f}%")
    print(f"最大单日涨幅: {daily_returns.max() * 100:.2f}%")
    print(f"最大单日跌幅: {daily_returns.min() * 100:.2f}%")
    
    # 计算正负收益天数
    positive_days = (daily_returns > 0).sum()
    negative_days = (daily_returns < 0).sum()
    print(f"上涨天数: {positive_days} ({positive_days/len(daily_returns)*100:.1f}%)")
    print(f"下跌天数: {negative_days} ({negative_days/len(daily_returns)*100:.1f}%)")

def add_technical_indicators(data):
    """添加技术指标"""
    print("\n" + "="*50)
    print("计算技术指标")
    print("="*50)
    
    df = data.copy()
    close_prices = df['Close']
    
    # 移动平均线
    df['SMA_5'] = close_prices.rolling(5).mean()
    df['SMA_20'] = close_prices.rolling(20).mean()
    df['SMA_50'] = close_prices.rolling(50).mean()
    
    # 指数移动平均
    df['EMA_12'] = close_prices.ewm(span=12).mean()
    df['EMA_26'] = close_prices.ewm(span=26).mean()
    
    # RSI
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    df['MACD'] = df['EMA_12'] - df['EMA_26']
    df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # 布林带
    df['BB_Middle'] = close_prices.rolling(20).mean()
    bb_std = close_prices.rolling(20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    print("已添加以下技术指标:")
    print("- 简单移动平均线 (SMA): 5日, 20日, 50日")
    print("- 指数移动平均线 (EMA): 12日, 26日")
    print("- 相对强弱指数 (RSI): 14日")
    print("- MACD指标: 12-26-9")
    print("- 布林带: 20日±2标准差")
    
    return df

def test_moving_average_strategy(data):
    """测试移动平均策略"""
    print("\n" + "="*50)
    print("移动平均策略测试")
    print("="*50)
    
    # 简单的移动平均策略实现
    df = data.copy()
    
    # 计算5日和20日移动平均
    short_ma = df['Close'].rolling(5).mean()
    long_ma = df['Close'].rolling(20).mean()
    
    # 生成交易信号
    signals = []
    position = 0  # 0: 无持仓, 1: 持多, -1: 持空
    
    for i in range(len(df)):
        if i < 20:  # 需要足够的数据计算20日均线
            signals.append(0)
            continue
            
        current_short = short_ma.iloc[i]
        current_long = long_ma.iloc[i]
        prev_short = short_ma.iloc[i-1]
        prev_long = long_ma.iloc[i-1]
        
        # 金叉：短线上穿长线 -> 买入
        if prev_short <= prev_long and current_short > current_long and position <= 0:
            signals.append(1)  # 买入信号
            position = 1
        # 死叉：短线下穿长线 -> 卖出
        elif prev_short >= prev_long and current_short < current_long and position >= 0:
            signals.append(-1)  # 卖出信号
            position = -1
        else:
            signals.append(0)  # 持有
    
    df['Signal'] = signals
    df['Position'] = pd.Series(signals).fillna(method='ffill').fillna(0)
    
    # 计算策略收益
    df['Strategy_Return'] = df['Signal'].shift(1) * df['Close'].pct_change()
    df['Cumulative_Strategy_Return'] = (1 + df['Strategy_Return']).cumprod()
    df['Cumulative_Market_Return'] = (1 + df['Close'].pct_change()).cumprod()
    
    # 统计结果
    buy_signals = (df['Signal'] == 1).sum()
    sell_signals = (df['Signal'] == -1).sum()
    total_trades = buy_signals + sell_signals
    
    strategy_total_return = df['Cumulative_Strategy_Return'].iloc[-1] - 1
    market_total_return = df['Cumulative_Market_Return'].iloc[-1] - 1
    
    print(f"策略名称: 移动平均交叉策略 (5日 vs 20日)")
    print(f"总交易次数: {total_trades}")
    print(f"买入信号: {buy_signals}")
    print(f"卖出信号: {sell_signals}")
    print(f"策略总收益: {strategy_total_return * 100:.2f}%")
    print(f"市场总收益: {market_total_return * 100:.2f}%")
    print(f"超额收益: {(strategy_total_return - market_total_return) * 100:.2f}%")
    
    if len(df['Strategy_Return'].dropna()) > 0:
        strategy_volatility = df['Strategy_Return'].std() * np.sqrt(252)
        sharpe_ratio = df['Strategy_Return'].mean() / df['Strategy_Return'].std() * np.sqrt(252)
        print(f"策略年化波动率: {strategy_volatility * 100:.2f}%")
        print(f"夏普比率: {sharpe_ratio:.3f}")
    
    return df

def test_rsi_strategy(data):
    """测试RSI策略"""
    print("\n" + "="*50)
    print("RSI均值回归策略测试")
    print("="*50)
    
    df = data.copy()
    
    # 计算RSI
    delta = df['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    df['RSI'] = rsi
    
    # RSI策略参数
    oversold_threshold = 30
    overbought_threshold = 70
    
    # 生成交易信号
    signals = []
    position = 0
    
    for i in range(len(df)):
        if i < 14:  # 需要足够数据计算RSI
            signals.append(0)
            continue
            
        current_rsi = rsi.iloc[i]
        
        if pd.isna(current_rsi):
            signals.append(0)
            continue
        
        # RSI超卖 -> 买入
        if current_rsi <= oversold_threshold and position <= 0:
            signals.append(1)
            position = 1
        # RSI超买 -> 卖出
        elif current_rsi >= overbought_threshold and position >= 0:
            signals.append(-1)
            position = -1
        else:
            signals.append(0)
    
    df['RSI_Signal'] = signals
    df['RSI_Position'] = pd.Series(signals).fillna(method='ffill').fillna(0)
    
    # 计算策略收益
    df['RSI_Strategy_Return'] = df['RSI_Signal'].shift(1) * df['Close'].pct_change()
    df['RSI_Cumulative_Return'] = (1 + df['RSI_Strategy_Return']).cumprod()
    
    # 统计RSI分布
    rsi_data = df['RSI'].dropna()
    oversold_days = (rsi_data <= oversold_threshold).sum()
    overbought_days = (rsi_data >= overbought_threshold).sum()
    
    buy_signals = (df['RSI_Signal'] == 1).sum()
    sell_signals = (df['RSI_Signal'] == -1).sum()
    
    rsi_total_return = df['RSI_Cumulative_Return'].iloc[-1] - 1
    
    print(f"策略名称: RSI均值回归策略 (超卖≤{oversold_threshold}, 超买≥{overbought_threshold})")
    print(f"RSI统计:")
    print(f"  平均RSI: {rsi_data.mean():.2f}")
    print(f"  RSI范围: {rsi_data.min():.2f} - {rsi_data.max():.2f}")
    print(f"  超卖天数: {oversold_days} ({oversold_days/len(rsi_data)*100:.1f}%)")
    print(f"  超买天数: {overbought_days} ({overbought_days/len(rsi_data)*100:.1f}%)")
    
    print(f"交易统计:")
    print(f"  买入信号: {buy_signals}")
    print(f"  卖出信号: {sell_signals}")
    print(f"  策略总收益: {rsi_total_return * 100:.2f}%")
    
    return df

def create_visualization(data):
    """创建可视化图表"""
    print("\n" + "="*50)
    print("生成可视化图表")
    print("="*50)
    
    try:
        # 创建子图
        fig, axes = plt.subplots(3, 1, figsize=(12, 10))
        fig.suptitle('量化交易策略分析', fontsize=16)
        
        # 图1: 价格和移动平均线
        axes[0].plot(data.index, data['Close'], label='收盘价', linewidth=1)
        if 'SMA_5' in data.columns:
            axes[0].plot(data.index, data['SMA_5'], label='5日均线', alpha=0.7)
        if 'SMA_20' in data.columns:
            axes[0].plot(data.index, data['SMA_20'], label='20日均线', alpha=0.7)
        
        # 添加买卖信号点
        if 'Signal' in data.columns:
            buy_signals = data[data['Signal'] == 1]
            sell_signals = data[data['Signal'] == -1]
            
            if len(buy_signals) > 0:
                axes[0].scatter(buy_signals.index, buy_signals['Close'], 
                              color='green', marker='^', s=100, label='买入信号', alpha=0.7)
            if len(sell_signals) > 0:
                axes[0].scatter(sell_signals.index, sell_signals['Close'], 
                              color='red', marker='v', s=100, label='卖出信号', alpha=0.7)
        
        axes[0].set_title('股价走势与交易信号')
        axes[0].set_ylabel('价格 ($)')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # 图2: RSI指标
        if 'RSI' in data.columns:
            axes[1].plot(data.index, data['RSI'], label='RSI', color='purple')
            axes[1].axhline(y=70, color='r', linestyle='--', alpha=0.7, label='超买线(70)')
            axes[1].axhline(y=30, color='g', linestyle='--', alpha=0.7, label='超卖线(30)')
            axes[1].axhline(y=50, color='gray', linestyle='-', alpha=0.5, label='中位线(50)')
            axes[1].set_title('RSI相对强弱指数')
            axes[1].set_ylabel('RSI值')
            axes[1].set_ylim(0, 100)
            axes[1].legend()
            axes[1].grid(True, alpha=0.3)
        
        # 图3: 累积收益比较
        if 'Cumulative_Market_Return' in data.columns:
            axes[2].plot(data.index, (data['Cumulative_Market_Return'] - 1) * 100, 
                        label='买入持有策略', linewidth=2)
        
        if 'Cumulative_Strategy_Return' in data.columns:
            axes[2].plot(data.index, (data['Cumulative_Strategy_Return'] - 1) * 100, 
                        label='移动平均策略', linewidth=2)
        
        if 'RSI_Cumulative_Return' in data.columns:
            axes[2].plot(data.index, (data['RSI_Cumulative_Return'] - 1) * 100, 
                        label='RSI策略', linewidth=2)
        
        axes[2].set_title('策略收益比较')
        axes[2].set_xlabel('日期')
        axes[2].set_ylabel('累积收益率 (%)')
        axes[2].legend()
        axes[2].grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # 保存图表
        chart_path = os.path.join(project_root, 'examples', 'strategy_analysis.png')
        plt.savefig(chart_path, dpi=300, bbox_inches='tight')
        print(f"图表已保存到: {chart_path}")
        
        # 显示图表（如果在支持的环境中）
        try:
            plt.show()
        except:
            print("无法显示图表（可能在无GUI环境中运行）")
            
    except Exception as e:
        print(f"创建图表时出错: {e}")
        print("可能需要安装matplotlib: pip install matplotlib")

def main():
    """主函数"""
    print("欢迎使用 AITrade 量化交易学习项目！")
    print("="*60)
    
    # 检查模块可用性
    if not modules_available:
        print("注意：某些高级功能需要安装额外的库")
        print("运行以下命令安装所有依赖：")
        print("pip install -r requirements.txt")
        print("\n继续使用基础功能进行演示...\n")
    
    # 1. 创建或获取数据
    print("步骤1: 获取股票数据")
    stock_data = create_sample_data()
    
    # 2. 基础统计分析
    analyze_basic_statistics(stock_data)
    
    # 3. 添加技术指标
    print("\n步骤2: 计算技术指标")
    data_with_indicators = add_technical_indicators(stock_data)
    
    # 4. 测试移动平均策略
    print("\n步骤3: 测试交易策略")
    data_with_ma_strategy = test_moving_average_strategy(data_with_indicators)
    
    # 5. 测试RSI策略
    final_data = test_rsi_strategy(data_with_ma_strategy)
    
    # 6. 创建可视化图表
    print("\n步骤4: 创建分析图表")
    create_visualization(final_data)
    
    # 7. 输出学习建议
    print("\n" + "="*60)
    print("学习建议")
    print("="*60)
    print("1. 理解代码：仔细阅读每个函数的实现，理解量化交易的基本概念")
    print("2. 修改参数：尝试调整策略参数，观察对结果的影响")
    print("3. 添加策略：基于现有框架，实现自己的交易策略")
    print("4. 风险管理：学习如何添加止损、止盈和仓位管理")
    print("5. 回测优化：了解回测的局限性，避免过度拟合")
    print("6. 实盘准备：在实际投资前，进行充分的纸上交易测试")
    
    print("\n下一步：")
    print("- 阅读 tutorials/ 目录下的详细教程")
    print("- 探索 src/ 目录下的高级功能模块")
    print("- 运行其他示例了解更多策略")
    print("- 开始构建您自己的量化交易系统！")
    
    print(f"\n数据已保存，您可以在Python中继续分析：")
    print("import pandas as pd")
    print("data = pd.read_csv('stock_data.csv')")
    
    # 保存数据供后续分析
    output_path = os.path.join(project_root, 'examples', 'sample_stock_data.csv')
    final_data.to_csv(output_path)
    print(f"示例数据已保存到: {output_path}")

if __name__ == "__main__":
    main()