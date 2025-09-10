"""
RSI策略
基于相对强弱指数(RSI)的均值回归策略
"""

import pandas as pd
import numpy as np
from .base_strategy import BaseStrategy, Signal, StrategyUtils

class RSIStrategy(BaseStrategy):
    """
    RSI策略
    
    当RSI低于超卖阈值时产生买入信号
    当RSI高于超买阈值时产生卖出信号
    """
    
    def __init__(self, rsi_window: int = 14, oversold_threshold: float = 30, overbought_threshold: float = 70):
        """
        初始化RSI策略
        
        参数:
            rsi_window: RSI计算窗口
            oversold_threshold: 超卖阈值
            overbought_threshold: 超买阈值
        """
        super().__init__(f"RSI({rsi_window},{oversold_threshold},{overbought_threshold})")
        self.set_parameters(
            rsi_window=rsi_window,
            oversold_threshold=oversold_threshold,
            overbought_threshold=overbought_threshold
        )
    
    def validate_parameters(self) -> bool:
        """验证策略参数"""
        rsi_window = self.parameters.get('rsi_window', 0)
        oversold = self.parameters.get('oversold_threshold', 0)
        overbought = self.parameters.get('overbought_threshold', 0)
        
        if rsi_window <= 0:
            print("RSI窗口必须大于0")
            return False
        
        if not (0 <= oversold <= 100) or not (0 <= overbought <= 100):
            print("RSI阈值必须在0-100之间")
            return False
        
        if oversold >= overbought:
            print("超卖阈值必须小于超买阈值")
            return False
        
        return True
    
    def calculate_rsi(self, prices: pd.Series, window: int) -> pd.Series:
        """
        计算RSI指标
        
        参数:
            prices: 价格序列
            window: 计算窗口
            
        返回:
            pd.Series: RSI值序列
        """
        # 计算价格变化
        delta = prices.diff()
        
        # 分离涨跌
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        # 计算平均涨跌幅
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        
        # 避免除零错误
        avg_loss = avg_loss.replace(0, np.finfo(float).eps)
        
        # 计算RS和RSI
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
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
        
        rsi_window = self.parameters['rsi_window']
        oversold = self.parameters['oversold_threshold']
        overbought = self.parameters['overbought_threshold']
        
        # 需要足够的数据来计算RSI
        if current_index < rsi_window:
            return Signal.HOLD
        
        # 获取到当前位置的数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算RSI
        rsi = self.calculate_rsi(close_prices, rsi_window)
        current_rsi = rsi.iloc[-1]
        
        # 检查是否为有效值
        if pd.isna(current_rsi):
            return Signal.HOLD
        
        # 生成信号
        if current_rsi <= oversold:
            return Signal.BUY
        elif current_rsi >= overbought:
            return Signal.SELL
        else:
            return Signal.HOLD
    
    def add_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        为数据添加RSI指标
        
        参数:
            data: 原始数据
            
        返回:
            pd.DataFrame: 包含指标的数据
        """
        result = data.copy()
        
        rsi_window = self.parameters['rsi_window']
        oversold = self.parameters['oversold_threshold']
        overbought = self.parameters['overbought_threshold']
        
        # 计算RSI
        rsi = self.calculate_rsi(data['Close'], rsi_window)
        result['RSI'] = rsi
        
        # 添加阈值线（用于可视化）
        result['RSI_Oversold'] = oversold
        result['RSI_Overbought'] = overbought
        
        # 添加RSI状态
        result['RSI_Status'] = 'NEUTRAL'
        result.loc[rsi <= oversold, 'RSI_Status'] = 'OVERSOLD'
        result.loc[rsi >= overbought, 'RSI_Status'] = 'OVERBOUGHT'
        
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
        rsi_window = self.parameters['rsi_window']
        oversold = self.parameters['oversold_threshold']
        overbought = self.parameters['overbought_threshold']
        
        if current_index < rsi_window:
            return 0.0
        
        # 获取当前数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算RSI
        rsi = self.calculate_rsi(close_prices, rsi_window)
        current_rsi = rsi.iloc[-1]
        
        if pd.isna(current_rsi):
            return 0.0
        
        # 计算强度
        if current_rsi <= oversold:
            # 超卖程度：越低强度越大（负值表示看涨）
            strength = -((oversold - current_rsi) / oversold)
        elif current_rsi >= overbought:
            # 超买程度：越高强度越大（正值表示看跌）
            strength = ((current_rsi - overbought) / (100 - overbought))
        else:
            # 中性区域：距离中线50的距离
            strength = (current_rsi - 50) / 50
        
        return max(-1.0, min(1.0, strength))

class RSIDivergenceStrategy(BaseStrategy):
    """
    RSI背离策略
    基于价格和RSI的背离现象
    """
    
    def __init__(self, rsi_window: int = 14, lookback_period: int = 10, min_rsi_change: float = 5):
        """
        初始化RSI背离策略
        
        参数:
            rsi_window: RSI计算窗口
            lookback_period: 背离检测回看期
            min_rsi_change: 最小RSI变化幅度
        """
        super().__init__(f"RSI_Divergence({rsi_window},{lookback_period},{min_rsi_change})")
        self.set_parameters(
            rsi_window=rsi_window,
            lookback_period=lookback_period,
            min_rsi_change=min_rsi_change
        )
    
    def validate_parameters(self) -> bool:
        """验证策略参数"""
        rsi_window = self.parameters.get('rsi_window', 0)
        lookback = self.parameters.get('lookback_period', 0)
        min_change = self.parameters.get('min_rsi_change', 0)
        
        if rsi_window <= 0 or lookback <= 0:
            print("RSI窗口和回看期必须大于0")
            return False
        
        if min_change < 0:
            print("最小RSI变化必须大于等于0")
            return False
        
        return True
    
    def calculate_rsi(self, prices: pd.Series, window: int) -> pd.Series:
        """计算RSI（与基础RSI策略相同）"""
        delta = prices.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=window).mean()
        avg_loss = loss.rolling(window=window).mean()
        avg_loss = avg_loss.replace(0, np.finfo(float).eps)
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def detect_divergence(self, prices: pd.Series, rsi: pd.Series, lookback: int) -> str:
        """
        检测价格和RSI的背离
        
        参数:
            prices: 价格序列
            rsi: RSI序列
            lookback: 回看期
            
        返回:
            str: 背离类型 ('BULLISH', 'BEARISH', 'NONE')
        """
        if len(prices) < lookback or len(rsi) < lookback:
            return 'NONE'
        
        # 获取最近的数据
        recent_prices = prices.iloc[-lookback:]
        recent_rsi = rsi.iloc[-lookback:]
        
        # 检查是否有足够的有效数据
        if recent_rsi.isna().any():
            return 'NONE'
        
        # 价格和RSI的变化
        price_change = recent_prices.iloc[-1] - recent_prices.iloc[0]
        rsi_change = recent_rsi.iloc[-1] - recent_rsi.iloc[0]
        
        min_change = self.parameters['min_rsi_change']
        
        # 看涨背离：价格下跌但RSI上涨
        if price_change < 0 and rsi_change > min_change:
            return 'BULLISH'
        
        # 看跌背离：价格上涨但RSI下跌
        elif price_change > 0 and rsi_change < -min_change:
            return 'BEARISH'
        
        return 'NONE'
    
    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        """
        生成交易信号
        基于RSI背离
        """
        if not StrategyUtils.validate_data(data, ['Close']):
            return Signal.HOLD
        
        rsi_window = self.parameters['rsi_window']
        lookback = self.parameters['lookback_period']
        
        # 需要足够的数据
        min_required = rsi_window + lookback
        if current_index < min_required:
            return Signal.HOLD
        
        # 获取当前数据
        current_data = data.iloc[:current_index + 1]
        close_prices = current_data['Close']
        
        # 计算RSI
        rsi = self.calculate_rsi(close_prices, rsi_window)
        
        # 检测背离
        divergence = self.detect_divergence(close_prices, rsi, lookback)
        
        # 生成信号
        if divergence == 'BULLISH':
            return Signal.BUY
        elif divergence == 'BEARISH':
            return Signal.SELL
        else:
            return Signal.HOLD

# 使用示例和测试
if __name__ == "__main__":
    print("=== RSI策略测试 ===\n")
    
    # 创建测试数据
    import datetime
    dates = pd.date_range(start='2023-01-01', end='2023-12-31', freq='D')
    
    # 生成模拟价格数据（带波动）
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    
    for i in range(1, len(dates)):
        # 添加一些周期性和随机性
        trend = 0.02 * np.sin(i * 0.1)  # 周期性趋势
        random_change = np.random.normal(0, 0.02)  # 随机变化
        change = trend + random_change
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    test_data = pd.DataFrame({
        'Close': prices,
        'High': [p * 1.02 for p in prices],
        'Low': [p * 0.98 for p in prices],
        'Open': [prices[0]] + prices[:-1],
        'Volume': np.random.randint(1000000, 5000000, len(dates))
    }, index=dates)
    
    print(f"测试数据形状: {test_data.shape}")
    print(f"价格范围: {test_data['Close'].min():.2f} - {test_data['Close'].max():.2f}")
    
    # 测试基础RSI策略
    print("\n1. 测试基础RSI策略")
    rsi_strategy = RSIStrategy(rsi_window=14, oversold_threshold=30, overbought_threshold=70)
    
    # 添加指标
    data_with_rsi = rsi_strategy.add_indicators(test_data)
    print(f"添加RSI指标后的列数: {len(data_with_rsi.columns)}")
    
    # 计算RSI统计
    rsi_values = data_with_rsi['RSI'].dropna()
    print(f"RSI范围: {rsi_values.min():.2f} - {rsi_values.max():.2f}")
    print(f"RSI平均值: {rsi_values.mean():.2f}")
    
    # 运行策略
    result = rsi_strategy.run_strategy(test_data)
    
    # 统计信号
    signal_counts = result['Signal'].value_counts()
    print(f"信号统计: {signal_counts.to_dict()}")
    
    # RSI状态统计
    rsi_status_counts = data_with_rsi['RSI_Status'].value_counts()
    print(f"RSI状态统计: {rsi_status_counts.to_dict()}")
    
    # 策略统计
    stats = rsi_strategy.get_strategy_stats()
    print("\n策略统计:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 测试RSI背离策略
    print("\n2. 测试RSI背离策略")
    divergence_strategy = RSIDivergenceStrategy(rsi_window=14, lookback_period=10, min_rsi_change=5)
    
    result_div = divergence_strategy.run_strategy(test_data)
    signal_counts_div = result_div['Signal'].value_counts()
    print(f"背离策略信号统计: {signal_counts_div.to_dict()}")
    
    stats_div = divergence_strategy.get_strategy_stats()
    print(f"背离策略 - 信号生成率: {(stats_div['buy_signals'] + stats_div['sell_signals']) / stats_div['total_signals'] * 100:.2f}%")
    
    print("\n=== RSI策略测试完成 ===")