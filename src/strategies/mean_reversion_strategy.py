"""
均值回归策略
基于价格偏离均值的回归特性
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal, StrategyUtils

class MeanReversionStrategy(BaseStrategy):
    """
    均值回归策略
    
    当价格偏离移动平均线超过一定阈值时，
    预期价格会回归到均值，从而产生交易信号
    """
    
    def __init__(self, window: int = 20, threshold: float = 2.0, ma_type: str = 'SMA'):
        """
        初始化均值回归策略
        
        参数:
            window: 移动平均窗口
            threshold: 偏离阈值（标准差倍数）
            ma_type: 移动平均类型 ('SMA' 或 'EMA')
        """
        super().__init__(f"MeanReversion({window},{threshold},{ma_type})")
        self.set_parameters(
            window=window,
            threshold=threshold,
            ma_type=ma_type
        )
    
    def validate_parameters(self) -> bool:
        """验证策略参数"""
        window = self.parameters.get('window', 0)
        threshold = self.parameters.get('threshold', 0)
        ma_type = self.parameters.get('ma_type', '')
        
        if window <= 0:
            print("移动平均窗口必须大于0")
            return False
        
        if threshold <= 0:
            print("偏离阈值必须大于0")
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
    
    def calculate_z_score(self, prices: pd.Series, ma: pd.Series, window: int) -> pd.Series:
        """
        计算Z分数（标准化偏离）
        
        参数:
            prices: 价格序列
            ma: 移动平均序列
            window: 计算标准差的窗口
            
        返回:
            pd.Series: Z分数序列
        """
        # 计算偏离
        deviation = prices - ma
        
        # 计算滚动标准差
        rolling_std = deviation.rolling(window=window).std()
        
        # 避免除零错误
        rolling_std = rolling_std.replace(0, np.finfo(float).eps)
        
        # 计算Z分数
        z_score = deviation / rolling_std
        
        return z_score
    
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
        
        window = self.parameters['window']
        threshold = self.parameters['threshold']
        ma_type = self.parameters['ma_type']
        
        # 需要足够的数据
        if current_index < window * 2:  # 需要额外的数据计算标准差
            return Signal.HOLD
        
        # 获取到当前位置的数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算移动平均
        ma = self.calculate_moving_average(close_prices, window, ma_type)
        
        # 计算Z分数
        z_score = self.calculate_z_score(close_prices, ma, window)
        current_z_score = z_score.iloc[-1]
        
        # 检查是否为有效值
        if pd.isna(current_z_score):
            return Signal.HOLD
        
        # 生成信号
        # 价格过度下跌（负Z分数），预期回归 -> 买入
        if current_z_score <= -threshold:
            return Signal.BUY
        # 价格过度上涨（正Z分数），预期回归 -> 卖出
        elif current_z_score >= threshold:
            return Signal.SELL
        else:
            return Signal.HOLD
    
    def add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        为数据添加均值回归指标
        
        参数:
            data: 原始数据
            
        返回:
            pd.DataFrame: 包含指标的数据
        """
        result = data.copy()
        
        window = self.parameters['window']
        threshold = self.parameters['threshold']
        ma_type = self.parameters['ma_type']
        
        # 计算移动平均
        ma = self.calculate_moving_average(data['Close'], window, ma_type)
        result[f'{ma_type}_{window}'] = ma
        
        # 计算Z分数
        z_score = self.calculate_z_score(data['Close'], ma, window)
        result['Z_Score'] = z_score
        
        # 添加阈值线
        result['Upper_Threshold'] = threshold
        result['Lower_Threshold'] = -threshold
        
        # 计算偏离度
        deviation = data['Close'] - ma
        result['Deviation'] = deviation
        result['Deviation_Pct'] = (deviation / ma) * 100
        
        # 添加信号区域标识
        result['Signal_Zone'] = 'NEUTRAL'
        result.loc[z_score <= -threshold, 'Signal_Zone'] = 'OVERSOLD'
        result.loc[z_score >= threshold, 'Signal_Zone'] = 'OVERBOUGHT'
        
        return result
    
    def get_signal_strength(self, data: pd.DataFrame, current_index: int) -> float:
        """
        获取信号强度
        
        参数:
            data: 价格数据
            current_index: 当前索引
            
        返回:
            float: 信号强度 (-1 到 1)
        """
        window = self.parameters['window']
        threshold = self.parameters['threshold']
        ma_type = self.parameters['ma_type']
        
        if current_index < window * 2:
            return 0.0
        
        # 获取当前数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算移动平均和Z分数
        ma = self.calculate_moving_average(close_prices, window, ma_type)
        z_score = self.calculate_z_score(close_prices, ma, window)
        current_z_score = z_score.iloc[-1]
        
        if pd.isna(current_z_score):
            return 0.0
        
        # 标准化到 -1 到 1 范围
        # Z分数越负，买入信号越强（返回负值）
        # Z分数越正，卖出信号越强（返回正值）
        max_z = 3.0  # 假设最大Z分数为3
        strength = current_z_score / max_z
        
        return max(-1.0, min(1.0, strength))

class BollingerBandsMeanReversionStrategy(BaseStrategy):
    """
    布林带均值回归策略
    基于布林带的均值回归特性
    """
    
    def __init__(self, window: int = 20, std_multiplier: float = 2.0):
        """
        初始化布林带均值回归策略
        
        参数:
            window: 移动平均窗口
            std_multiplier: 标准差倍数
        """
        super().__init__(f"BBMeanReversion({window},{std_multiplier})")
        self.set_parameters(
            window=window,
            std_multiplier=std_multiplier
        )
    
    def validate_parameters(self) -> bool:
        """验证策略参数"""
        window = self.parameters.get('window', 0)
        std_multiplier = self.parameters.get('std_multiplier', 0)
        
        if window <= 0:
            print("移动平均窗口必须大于0")
            return False
        
        if std_multiplier <= 0:
            print("标准差倍数必须大于0")
            return False
        
        return True
    
    def calculate_bollinger_bands(self, prices: pd.Series, window: int, std_multiplier: float) -> dict:
        """
        计算布林带
        
        参数:
            prices: 价格序列
            window: 移动平均窗口
            std_multiplier: 标准差倍数
            
        返回:
            dict: 包含上轨、中轨、下轨的字典
        """
        # 计算移动平均（中轨）
        middle_band = prices.rolling(window=window).mean()
        
        # 计算标准差
        rolling_std = prices.rolling(window=window).std()
        
        # 计算上下轨
        upper_band = middle_band + (rolling_std * std_multiplier)
        lower_band = middle_band - (rolling_std * std_multiplier)
        
        return {
            'upper': upper_band,
            'middle': middle_band,
            'lower': lower_band
        }
    
    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        """
        生成交易信号
        基于布林带的突破和回归
        """
        if not StrategyUtils.validate_data(data, ['Close']):
            return Signal.HOLD
        
        window = self.parameters['window']
        std_multiplier = self.parameters['std_multiplier']
        
        if current_index < window:
            return Signal.HOLD
        
        # 获取当前数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算布林带
        bb = self.calculate_bollinger_bands(close_prices, window, std_multiplier)
        
        current_price = close_prices.iloc[-1]
        current_upper = bb['upper'].iloc[-1]
        current_lower = bb['lower'].iloc[-1]
        current_middle = bb['middle'].iloc[-1]
        
        # 检查是否为有效值
        if pd.isna(current_upper) or pd.isna(current_lower):
            return Signal.HOLD
        
        # 生成信号
        # 价格触及下轨 -> 买入（预期回归中轨）
        if current_price <= current_lower:
            return Signal.BUY
        # 价格触及上轨 -> 卖出（预期回归中轨）
        elif current_price >= current_upper:
            return Signal.SELL
        else:
            return Signal.HOLD
    
    def add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """添加布林带指标"""
        result = data.copy()
        
        window = self.parameters['window']
        std_multiplier = self.parameters['std_multiplier']
        
        # 计算布林带
        bb = self.calculate_bollinger_bands(data['Close'], window, std_multiplier)
        
        result['BB_Upper'] = bb['upper']
        result['BB_Middle'] = bb['middle']
        result['BB_Lower'] = bb['lower']
        
        # 计算布林带宽度（衡量波动性）
        result['BB_Width'] = (bb['upper'] - bb['lower']) / bb['middle']
        
        # 计算%B指标（价格在布林带中的相对位置）
        result['Percent_B'] = (data['Close'] - bb['lower']) / (bb['upper'] - bb['lower'])
        
        # 添加位置标识
        result['BB_Position'] = 'MIDDLE'
        result.loc[data['Close'] <= bb['lower'], 'BB_Position'] = 'BELOW_LOWER'
        result.loc[data['Close'] >= bb['upper'], 'BB_Position'] = 'ABOVE_UPPER'
        
        return result

# 使用示例和测试
if __name__ == "__main__":
    print("=== 均值回归策略测试 ===\n")
    
    # 创建测试数据 - 模拟均值回归特性
    import datetime
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # 生成具有均值回归特性的价格数据
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    mean_price = base_price
    
    for i in range(1, len(dates)):
        # 均值回归模型：价格有回归到长期均值的趋势
        current_price = prices[-1]
        mean_reversion_force = 0.05 * (mean_price - current_price) / mean_price
        random_shock = np.random.normal(0, 0.02)
        
        change = mean_reversion_force + random_shock
        new_price = current_price * (1 + change)
        prices.append(new_price)
        
        # 缓慢调整长期均值
        mean_price += np.random.normal(0, 0.001)
    
    test_data = pd.DataFrame({
        'Close': prices,
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Open': [prices[0]] + prices[:-1],
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)
    
    print(f"测试数据形状: {test_data.shape}")
    print(f"价格范围: {test_data['Close'].min():.2f} - {test_data['Close'].max():.2f}")
    
    # 测试基础均值回归策略
    print("\n1. 测试基础均值回归策略")
    mr_strategy = MeanReversionStrategy(window=20, threshold=1.5, ma_type='SMA')
    
    # 添加指标
    data_with_mr = mr_strategy.add_indicators(test_data)
    print(f"添加均值回归指标后的列数: {len(data_with_mr.columns)}")
    
    # 分析Z分数分布
    z_scores = data_with_mr['Z_Score'].dropna()
    print(f"Z分数范围: {z_scores.min():.2f} - {z_scores.max():.2f}")
    print(f"Z分数标准差: {z_scores.std():.2f}")
    
    # 运行策略
    result = mr_strategy.run_strategy(test_data)
    
    # 统计信号
    signal_counts = result['Signal'].value_counts()
    print(f"信号统计: {signal_counts.to_dict()}")
    
    # 信号区域统计
    zone_counts = data_with_mr['Signal_Zone'].value_counts()
    print(f"信号区域统计: {zone_counts.to_dict()}")
    
    # 策略统计
    stats = mr_strategy.get_strategy_stats()
    print("\n策略统计:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 测试布林带均值回归策略
    print("\n2. 测试布林带均值回归策略")
    bb_strategy = BollingerBandsMeanReversionStrategy(window=20, std_multiplier=2.0)
    
    # 添加布林带指标
    data_with_bb = bb_strategy.add_indicators(test_data)
    
    # 分析%B指标
    percent_b = data_with_bb['Percent_B'].dropna()
    print(f"%B指标范围: {percent_b.min():.2f} - {percent_b.max():.2f}")
    print(f"%B指标平均值: {percent_b.mean():.2f}")
    
    # 运行布林带策略
    result_bb = bb_strategy.run_strategy(test_data)
    signal_counts_bb = result_bb['Signal'].value_counts()
    print(f"布林带策略信号统计: {signal_counts_bb.to_dict()}")
    
    # 布林带位置统计
    bb_position_counts = data_with_bb['BB_Position'].value_counts()
    print(f"布林带位置统计: {bb_position_counts.to_dict()}")
    
    stats_bb = bb_strategy.get_strategy_stats()
    print(f"布林带策略 - 信号生成率: {(stats_bb['buy_signals'] + stats_bb['sell_signals']) / stats_bb['total_signals'] * 100:.2f}%")
    
    print("\n=== 均值回归策略测试完成 ===")