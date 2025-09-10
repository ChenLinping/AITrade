"""
基础策略类
所有策略的基类，定义策略接口
"""

from abc import ABC, abstractmethod
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from enum import Enum
import datetime

class Signal(Enum):
    """交易信号枚举"""
    BUY = 1
    SELL = -1
    HOLD = 0

class Position(Enum):
    """持仓状态枚举"""
    LONG = 1
    SHORT = -1
    NEUTRAL = 0

class BaseStrategy(ABC):
    """
    基础策略类
    
    所有量化策略都应该继承这个基类并实现相应的方法
    """
    
    def __init__(self, name: str):
        """
        初始化策略
        
        参数:
            name: 策略名称
        """
        self.name = name
        self.signals = []  # 信号历史
        self.positions = []  # 持仓历史
        self.current_position = Position.NEUTRAL  # 当前持仓
        self.entry_price = 0.0  # 入场价格
        self.parameters = {}  # 策略参数
        
    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, current_index: int) -> Signal:
        """
        生成交易信号
        
        参数:
            data: 包含价格和指标的数据
            current_index: 当前数据索引
            
        返回:
            Signal: 交易信号 (BUY/SELL/HOLD)
        """
        pass
    
    @abstractmethod
    def validate_parameters(self) -> bool:
        """
        验证策略参数是否有效
        
        返回:
            bool: 参数是否有效
        """
        pass
    
    def set_parameters(self, **kwargs):
        """
        设置策略参数
        
        参数:
            **kwargs: 策略参数字典
        """
        self.parameters.update(kwargs)
        if not self.validate_parameters():
            raise ValueError(f"策略 {self.name} 参数无效")
    
    def get_parameters(self) -> Dict:
        """
        获取策略参数
        
        返回:
            Dict: 策略参数字典
        """
        return self.parameters.copy()
    
    def update_position(self, signal: Signal, price: float, timestamp: pd.Timestamp):
        """
        根据信号更新持仓状态
        
        参数:
            signal: 交易信号
            price: 当前价格
            timestamp: 时间戳
        """
        old_position = self.current_position
        
        if signal == Signal.BUY and self.current_position != Position.LONG:
            self.current_position = Position.LONG
            self.entry_price = price
            
        elif signal == Signal.SELL and self.current_position != Position.SHORT:
            self.current_position = Position.SHORT
            self.entry_price = price
            
        # 记录持仓变化
        if old_position != self.current_position:
            self.positions.append({
                'timestamp': timestamp,
                'old_position': old_position,
                'new_position': self.current_position,
                'price': price,
                'signal': signal
            })
    
    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        计算未实现盈亏
        
        参数:
            current_price: 当前价格
            
        返回:
            float: 未实现盈亏百分比
        """
        if self.current_position == Position.NEUTRAL or self.entry_price == 0:
            return 0.0
        
        if self.current_position == Position.LONG:
            return ((current_price - self.entry_price) / self.entry_price) * 100
        elif self.current_position == Position.SHORT:
            return ((self.entry_price - current_price) / self.entry_price) * 100
        
        return 0.0
    
    def run_strategy(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        运行策略，生成完整的信号序列
        
        参数:
            data: 价格数据
            
        返回:
            pd.DataFrame: 包含信号的数据
        """
        if data.empty:
            return data
        
        # 重置状态
        self.signals = []
        self.positions = []
        self.current_position = Position.NEUTRAL
        self.entry_price = 0.0
        
        # 创建结果DataFrame
        result = data.copy()
        signals = []
        positions = []
        unrealized_pnl = []
        
        # 逐行生成信号
        for i in range(len(data)):
            try:
                signal = self.generate_signal(data, i)
                current_price = data.iloc[i]['Close']
                current_time = data.index[i]
                
                # 更新持仓
                self.update_position(signal, current_price, current_time)
                
                # 记录结果
                signals.append(signal.value)
                positions.append(self.current_position.value)
                pnl = self.calculate_unrealized_pnl(current_price)
                unrealized_pnl.append(pnl)
                
                # 记录信号历史
                self.signals.append({
                    'timestamp': current_time,
                    'signal': signal,
                    'price': current_price,
                    'position': self.current_position
                })
                
            except Exception as e:
                print(f"策略运行出错 (第{i}行): {e}")
                signals.append(Signal.HOLD.value)
                positions.append(self.current_position.value)
                unrealized_pnl.append(0.0)
        
        # 添加信号列
        result['Signal'] = signals
        result['Position'] = positions
        result['Unrealized_PnL'] = unrealized_pnl
        result['Strategy'] = self.name
        
        return result
    
    def get_strategy_stats(self) -> Dict:
        """
        获取策略统计信息
        
        返回:
            Dict: 策略统计信息
        """
        if not self.signals:
            return {}
        
        # 统计信号数量
        total_signals = len(self.signals)
        buy_signals = sum(1 for s in self.signals if s['signal'] == Signal.BUY)
        sell_signals = sum(1 for s in self.signals if s['signal'] == Signal.SELL)
        hold_signals = total_signals - buy_signals - sell_signals
        
        # 统计持仓变化
        position_changes = len(self.positions)
        
        stats = {
            'strategy_name': self.name,
            'total_signals': total_signals,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'hold_signals': hold_signals,
            'position_changes': position_changes,
            'buy_signal_rate': (buy_signals / total_signals) * 100 if total_signals > 0 else 0,
            'sell_signal_rate': (sell_signals / total_signals) * 100 if total_signals > 0 else 0,
            'current_position': self.current_position.name,
            'parameters': self.parameters
        }
        
        return stats
    
    def __str__(self):
        """字符串表示"""
        return f"{self.name}"
    
    def __repr__(self):
        """详细字符串表示"""
        return f"{self.__class__.__name__}(name='{self.name}', parameters={self.parameters})"

class StrategyUtils:
    """策略工具类"""
    
    @staticmethod
    def calculate_returns(data: pd.DataFrame) -> pd.Series:
        """计算收益率序列"""
        if 'Close' not in data.columns:
            return pd.Series()
        return data['Close'].pct_change()
    
    @staticmethod
    def calculate_cumulative_returns(returns: pd.Series) -> pd.Series:
        """计算累积收益率"""
        return (1 + returns).cumprod() - 1
    
    @staticmethod
    def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        计算夏普比率
        
        参数:
            returns: 收益率序列
            risk_free_rate: 无风险利率（年化）
            
        返回:
            float: 夏普比率
        """
        if returns.empty or returns.std() == 0:
            return 0.0
        
        excess_returns = returns - risk_free_rate / 252  # 日化无风险利率
        return np.sqrt(252) * excess_returns.mean() / returns.std()
    
    @staticmethod
    def calculate_max_drawdown(cumulative_returns: pd.Series) -> float:
        """
        计算最大回撤
        
        参数:
            cumulative_returns: 累积收益率序列
            
        返回:
            float: 最大回撤百分比
        """
        if cumulative_returns.empty:
            return 0.0
        
        # 计算累积净值
        cumulative_wealth = 1 + cumulative_returns
        
        # 计算历史最高点
        running_max = cumulative_wealth.expanding().max()
        
        # 计算回撤
        drawdown = (cumulative_wealth - running_max) / running_max
        
        return abs(drawdown.min()) * 100
    
    @staticmethod
    def validate_data(data: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        验证数据是否包含必需的列
        
        参数:
            data: 数据DataFrame
            required_columns: 必需的列名列表
            
        返回:
            bool: 数据是否有效
        """
        if data.empty:
            return False
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"数据缺少必需的列: {missing_columns}")
            return False
        
        return True

# 示例和测试
if __name__ == "__main__":
    # 这里可以添加基础策略类的测试代码
    print("=== 基础策略类定义完成 ===")
    print("Signal 枚举:", list(Signal))
    print("Position 枚举:", list(Position))
    
    # 测试工具函数
    test_returns = pd.Series([0.01, -0.02, 0.015, -0.01, 0.02])
    print(f"测试收益率: {test_returns.tolist()}")
    
    cumulative = StrategyUtils.calculate_cumulative_returns(test_returns)
    print(f"累积收益率: {cumulative.iloc[-1]:.4f}")
    
    sharpe = StrategyUtils.calculate_sharpe_ratio(test_returns)
    print(f"夏普比率: {sharpe:.4f}")
    
    max_dd = StrategyUtils.calculate_max_drawdown(cumulative)
    print(f"最大回撤: {max_dd:.2f}%")