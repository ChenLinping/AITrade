"""
移动平均策略
基于短期和长期移动平均线的交叉信号
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal, StrategyUtils

class MovingAverageStrategy(BaseStrategy):
    """
    移动平均策略
    
    当短期移动平均线上穿长期移动平均线时产生买入信号
    当短期移动平均线下穿长期移动平均线时产生卖出信号
    """
    
    def __init__(self, short_window: int = 5, long_window: int = 20, ma_type: str = 'SMA'):
        """
        初始化移动平均策略
        
        参数:
            short_window: 短期移动平均窗口
            long_window: 长期移动平均窗口
            ma_type: 移动平均类型 ('SMA' 或 'EMA')
        """
        super().__init__(f"MovingAverage({short_window},{long_window},{ma_type})")
        self.set_parameters(
            short_window=short_window,
            long_window=long_window,
            ma_type=ma_type
        )
    
    def validate_parameters(self) -> bool:
        """验证策略参数"""
        short_window = self.parameters.get('short_window', 0)
        long_window = self.parameters.get('long_window', 0)
        ma_type = self.parameters.get('ma_type', '')
        
        if short_window <= 0 or long_window <= 0:
            print("移动平均窗口必须大于0")
            return False
        
        if short_window >= long_window:
            print("短期窗口必须小于长期窗口")
            return False
        
        if ma_type not in ['SMA', 'EMA']:
            print("移动平均类型必须是 'SMA' 或 'EMA'")
            return False
        
        return True
    
    def calculate_moving_average(self, data: pd.Series, window: int, ma_type: str) -> pd.Series:
        """
        计算移动平均
        
        参数:
            data: 价格数据
            window: 窗口大小
            ma_type: 移动平均类型
            
        返回:
            pd.Series: 移动平均值
        """
        if ma_type == 'SMA':
            return data.rolling(window=window).mean()
        elif ma_type == 'EMA':
            return data.ewm(span=window).mean()
        else:
            raise ValueError(f"不支持的移动平均类型: {ma_type}")
    
    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        """
        生成交易信号
        
        参数:
            data: 价格数据
            current_index: 当前索引
            
        返回:
            Signal: 交易信号
        """
        # 检查数据有效性
        if not StrategyUtils.validate_data(data, ['Close']):
            return Signal.HOLD
        
        short_window = self.parameters['short_window']
        long_window = self.parameters['long_window']
        ma_type = self.parameters['ma_type']
        
        # 需要足够的数据来计算长期移动平均
        if current_index < long_window - 1:
            return Signal.HOLD
        
        # 获取到当前位置的数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算移动平均
        short_ma = self.calculate_moving_average(close_prices, short_window, ma_type)
        long_ma = self.calculate_moving_average(close_prices, long_window, ma_type)
        
        # 当前值
        current_short_ma = short_ma.iloc[-1]
        current_long_ma = long_ma.iloc[-1]
        
        # 前一个值（用于判断穿越）
        if len(short_ma) < 2 or len(long_ma) < 2:
            return Signal.HOLD
        
        prev_short_ma = short_ma.iloc[-2]
        prev_long_ma = long_ma.iloc[-2]
        
        # 判断金叉和死叉
        # 金叉：短线上穿长线
        if (prev_short_ma <= prev_long_ma and current_short_ma > current_long_ma):
            return Signal.BUY
        
        # 死叉：短线下穿长线
        elif (prev_short_ma >= prev_long_ma and current_short_ma < current_long_ma):
            return Signal.SELL
        
        return Signal.HOLD
    
    def add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        为数据添加移动平均指标
        
        参数:
            data: 原始数据
            
        返回:
            pd.DataFrame: 包含指标的数据
        """
        result = data.copy()
        
        short_window = self.parameters['short_window']
        long_window = self.parameters['long_window']
        ma_type = self.parameters['ma_type']
        
        # 计算移动平均
        short_ma = self.calculate_moving_average(data['Close'], short_window, ma_type)
        long_ma = self.calculate_moving_average(data['Close'], long_window, ma_type)
        
        # 添加到数据中
        result[f'{ma_type}_{short_window}'] = short_ma
        result[f'{ma_type}_{long_window}'] = long_ma
        
        # 计算移动平均的差值和比率
        result['MA_Diff'] = short_ma - long_ma
        result['MA_Ratio'] = short_ma / long_ma
        
        return result
    
    def get_signal_strength(self, data: pd.DataFrame, current_index: int) -> float:
        """
        获取信号强度
        
        参数:
            data: 价格数据
            current_index: 当前索引
            
        返回:
            float: 信号强度 (-1 到 1，正值表示看涨，负值表示看跌)
        """
        short_window = self.parameters['short_window']
        long_window = self.parameters['long_window']
        ma_type = self.parameters['ma_type']
        
        if current_index < long_window - 1:
            return 0.0
        
        # 获取当前数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算移动平均
        short_ma = self.calculate_moving_average(close_prices, short_window, ma_type)
        long_ma = self.calculate_moving_average(close_prices, long_window, ma_type)
        
        current_short_ma = short_ma.iloc[-1]
        current_long_ma = long_ma.iloc[-1]
        
        # 计算强度：(短期MA - 长期MA) / 长期MA
        strength = (current_short_ma - current_long_ma) / current_long_ma
        
        # 限制在 -1 到 1 之间
        return max(-1.0, min(1.0, strength * 10))  # 乘以10增加敏感度

class MovingAverageCrossoverStrategy(BaseStrategy):
    """
    多重移动平均交叉策略
    使用多条移动平均线的组合信号
    """
    
    def __init__(self, windows: list = [5, 10, 20], ma_type: str = 'SMA'):
        """
        初始化多重移动平均策略
        
        参数:
            windows: 移动平均窗口列表（按升序排列）
            ma_type: 移动平均类型
        """
        super().__init__(f"MultiMA({','.join(map(str, windows))},{ma_type})")
        self.set_parameters(
            windows=sorted(windows),
            ma_type=ma_type
        )
    
    def validate_parameters(self) -> bool:
        """验证策略参数"""
        windows = self.parameters.get('windows', [])
        ma_type = self.parameters.get('ma_type', '')
        
        if len(windows) < 2:
            print("至少需要2条移动平均线")
            return False
        
        if any(w <= 0 for w in windows):
            print("所有窗口必须大于0")
            return False
        
        if windows != sorted(windows):
            print("窗口必须按升序排列")
            return False
        
        if ma_type not in ['SMA', 'EMA']:
            print("移动平均类型必须是 'SMA' 或 'EMA'")
            return False
        
        return True
    
    def calculate_moving_average(self, data: pd.Series, window: int, ma_type: str) -> pd.Series:
        """计算移动平均（与基础策略相同）"""
        if ma_type == 'SMA':
            return data.rolling(window=window).mean()
        elif ma_type == 'EMA':
            return data.ewm(span=window).mean()
        else:
            raise ValueError(f"不支持的移动平均类型: {ma_type}")
    
    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        """
        生成交易信号
        基于多条移动平均线的排列顺序
        """
        if not StrategyUtils.validate_data(data, ['Close']):
            return Signal.HOLD
        
        windows = self.parameters['windows']
        ma_type = self.parameters['ma_type']
        max_window = max(windows)
        
        if current_index < max_window - 1:
            return Signal.HOLD
        
        # 获取当前数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算所有移动平均
        mas = {}
        for window in windows:
            ma = self.calculate_moving_average(close_prices, window, ma_type)
            mas[window] = ma.iloc[-1]
        
        # 检查移动平均线的排列
        ma_values = [mas[w] for w in windows]
        
        # 多头排列：短期 > 中期 > 长期
        is_bullish = all(ma_values[i] >= ma_values[i+1] for i in range(len(ma_values)-1))
        
        # 空头排列：短期 < 中期 < 长期
        is_bearish = all(ma_values[i] <= ma_values[i+1] for i in range(len(ma_values)-1))
        
        if is_bullish:
            return Signal.BUY
        elif is_bearish:
            return Signal.SELL
        else:
            return Signal.HOLD

# 使用示例和测试
if __name__ == "__main__":
    print("=== 移动平均策略测试 ===\n")
    
    # 创建测试数据
    import datetime
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # 生成模拟价格数据（带趋势和噪音）
    np.random.seed(42)
    trend = np.linspace(100, 150, len(dates))
    noise = np.random.normal(0, 2, len(dates))
    prices = trend + noise
    
    test_data = pd.DataFrame({
        'Close': prices,
        'High': prices * 1.02,
        'Low': prices * 0.98,
        'Open': np.roll(prices, 1),
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)
    
    test_data['Open'].iloc[0] = test_data['Close'].iloc[0]
    
    print(f"测试数据形状: {test_data.shape}")
    print(f"价格范围: {test_data['Close'].min():.2f} - {test_data['Close'].max():.2f}")
    
    # 测试基础移动平均策略
    print("\n1. 测试基础移动平均策略")
    ma_strategy = MovingAverageStrategy(short_window=5, long_window=20, ma_type='SMA')
    
    # 添加指标
    data_with_indicators = ma_strategy.add_indicators(test_data)
    print(f"添加指标后的列数: {len(data_with_indicators.columns)}")
    
    # 运行策略
    result = ma_strategy.run_strategy(test_data)
    
    # 统计信号
    signal_counts = result['Signal'].value_counts()
    print(f"信号统计: {signal_counts.to_dict()}")
    
    # 策略统计
    stats = ma_strategy.get_strategy_stats()
    print("\n策略统计:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 测试多重移动平均策略
    print("\n2. 测试多重移动平均策略")
    multi_ma_strategy = MovingAverageCrossoverStrategy(windows=[5, 10, 20], ma_type='EMA')
    
    result_multi = multi_ma_strategy.run_strategy(test_data)
    signal_counts_multi = result_multi['Signal'].value_counts()
    print(f"多重MA信号统计: {signal_counts_multi.to_dict()}")
    
    stats_multi = multi_ma_strategy.get_strategy_stats()
    print(f"多重MA策略 - 买入信号比例: {stats_multi['buy_signal_rate']:.2f}%")
    
    print("\n=== 移动平均策略测试完成 ===")