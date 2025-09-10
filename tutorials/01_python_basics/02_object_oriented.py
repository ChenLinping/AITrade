"""
Python基础教程 2: 面向对象编程
为量化交易创建股票类和策略类
"""

import datetime
from typing import List, Dict

print("=== Python面向对象编程：股票和策略类 ===\n")

# 1. 基础类定义 - 股票类
class Stock:
    """股票类 - 封装股票的基本信息和操作"""
    
    def __init__(self, symbol: str, name: str, price: float):
        """初始化股票对象"""
        self.symbol = symbol          # 股票代码
        self.name = name             # 股票名称
        self.price = price           # 当前价格
        self.price_history = []      # 价格历史
        self.volume = 0              # 成交量
        
    def update_price(self, new_price: float, volume: int = 0):
        """更新股票价格"""
        self.price_history.append({
            'price': self.price,
            'volume': volume,
            'timestamp': datetime.datetime.now()
        })
        self.price = new_price
        self.volume = volume
        
    def get_return(self, days_back: int = 1) -> float:
        """计算指定天数的收益率"""
        if len(self.price_history) < days_back:
            return 0.0
        
        old_price = self.price_history[-days_back]['price']
        return ((self.price - old_price) / old_price) * 100
        
    def get_average_price(self, days: int = 5) -> float:
        """计算平均价格"""
        if len(self.price_history) < days:
            prices = [entry['price'] for entry in self.price_history]
        else:
            prices = [entry['price'] for entry in self.price_history[-days:]]
            
        prices.append(self.price)  # 包含当前价格
        return sum(prices) / len(prices)
        
    def __str__(self):
        """字符串表示"""
        return f"{self.symbol}({self.name}): ${self.price:.2f}"
        
    def __repr__(self):
        """详细字符串表示"""
        return f"Stock('{self.symbol}', '{self.name}', {self.price})"

# 创建股票对象示例
print("=== 创建股票对象 ===")
apple = Stock("AAPL", "Apple Inc.", 150.25)
tesla = Stock("TSLA", "Tesla Inc.", 245.80)

print(f"创建股票: {apple}")
print(f"创建股票: {tesla}")

# 更新价格
apple.update_price(152.30, 1000000)
apple.update_price(151.85, 1200000)
apple.update_price(153.45, 900000)

print(f"\n苹果股票当前价格: ${apple.price}")
print(f"1日收益率: {apple.get_return(1):.2f}%")
print(f"3日平均价格: ${apple.get_average_price(3):.2f}")

# 2. 投资组合类
class Portfolio:
    """投资组合类 - 管理多只股票"""
    
    def __init__(self, name: str, initial_cash: float):
        self.name = name
        self.cash = initial_cash      # 现金余额
        self.holdings = {}           # 持仓: {symbol: shares}
        self.stocks = {}             # 股票对象: {symbol: Stock}
        self.transactions = []       # 交易记录
        
    def add_stock(self, stock: Stock):
        """添加股票到组合"""
        self.stocks[stock.symbol] = stock
        
    def buy_stock(self, symbol: str, shares: int) -> bool:
        """买入股票"""
        if symbol not in self.stocks:
            print(f"错误: 股票 {symbol} 不在投资组合中")
            return False
            
        stock = self.stocks[symbol]
        cost = stock.price * shares
        
        if self.cash < cost:
            print(f"现金不足！需要 ${cost:.2f}，可用 ${self.cash:.2f}")
            return False
            
        # 执行买入
        self.cash -= cost
        self.holdings[symbol] = self.holdings.get(symbol, 0) + shares
        
        # 记录交易
        transaction = {
            'type': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': stock.price,
            'total': cost,
            'timestamp': datetime.datetime.now()
        }
        self.transactions.append(transaction)
        
        print(f"买入成功: {shares} 股 {symbol} @ ${stock.price:.2f}")
        return True
        
    def sell_stock(self, symbol: str, shares: int) -> bool:
        """卖出股票"""
        if symbol not in self.holdings or self.holdings[symbol] < shares:
            print(f"持仓不足！当前持有 {self.holdings.get(symbol, 0)} 股")
            return False
            
        stock = self.stocks[symbol]
        revenue = stock.price * shares
        
        # 执行卖出
        self.cash += revenue
        self.holdings[symbol] -= shares
        
        # 清除零持仓
        if self.holdings[symbol] == 0:
            del self.holdings[symbol]
            
        # 记录交易
        transaction = {
            'type': 'SELL',
            'symbol': symbol,
            'shares': shares,
            'price': stock.price,
            'total': revenue,
            'timestamp': datetime.datetime.now()
        }
        self.transactions.append(transaction)
        
        print(f"卖出成功: {shares} 股 {symbol} @ ${stock.price:.2f}")
        return True
        
    def get_portfolio_value(self) -> float:
        """计算投资组合总价值"""
        total_value = self.cash
        
        for symbol, shares in self.holdings.items():
            stock_value = self.stocks[symbol].price * shares
            total_value += stock_value
            
        return total_value
        
    def get_portfolio_summary(self):
        """获取投资组合摘要"""
        print(f"\n=== {self.name} 投资组合摘要 ===")
        print(f"现金余额: ${self.cash:.2f}")
        print(f"持仓明细:")
        
        total_stock_value = 0
        for symbol, shares in self.holdings.items():
            stock = self.stocks[symbol]
            value = stock.price * shares
            total_stock_value += value
            print(f"  {symbol}: {shares} 股 × ${stock.price:.2f} = ${value:.2f}")
            
        total_value = self.cash + total_stock_value
        print(f"股票总价值: ${total_stock_value:.2f}")
        print(f"投资组合总价值: ${total_value:.2f}")
        
        return {
            'cash': self.cash,
            'stock_value': total_stock_value,
            'total_value': total_value
        }

# 3. 简单交易策略类
class SimpleMovingAverageStrategy:
    """简单移动平均策略"""
    
    def __init__(self, short_window: int = 5, long_window: int = 20):
        self.short_window = short_window
        self.long_window = long_window
        self.name = f"SMA({short_window},{long_window})"
        
    def generate_signal(self, stock: Stock) -> str:
        """生成交易信号"""
        if len(stock.price_history) < self.long_window:
            return "HOLD"  # 数据不足
            
        # 计算短期和长期移动平均
        short_ma = stock.get_average_price(self.short_window)
        long_ma = stock.get_average_price(self.long_window)
        
        # 生成信号
        if short_ma > long_ma * 1.02:  # 上升趋势，2%阈值避免噪音
            return "BUY"
        elif short_ma < long_ma * 0.98:  # 下降趋势
            return "SELL"
        else:
            return "HOLD"
            
    def __str__(self):
        return self.name

# 使用示例
print("\n=== 投资组合管理示例 ===")

# 创建投资组合
my_portfolio = Portfolio("我的量化组合", 10000.0)

# 添加股票
my_portfolio.add_stock(apple)
my_portfolio.add_stock(tesla)

# 执行交易
my_portfolio.buy_stock("AAPL", 50)
my_portfolio.buy_stock("TSLA", 20)

# 查看组合
summary = my_portfolio.get_portfolio_summary()

print("\n=== 策略测试示例 ===")

# 创建策略
strategy = SimpleMovingAverageStrategy(3, 10)
print(f"使用策略: {strategy}")

# 模拟更多价格数据
price_sequence = [150, 152, 148, 155, 158, 156, 160, 162, 159, 165, 168, 170]

for i, price in enumerate(price_sequence):
    apple.update_price(price, 1000000)
    
    if i >= 9:  # 有足够数据后开始生成信号
        signal = strategy.generate_signal(apple)
        print(f"第{i+1}日 价格: ${price} -> 信号: {signal}")

print("\n=== 面向对象编程总结 ===")
print("1. 学会了创建类来封装股票信息")
print("2. 掌握了投资组合管理的基本操作")
print("3. 了解了如何实现简单的交易策略")
print("4. 理解了类的继承、封装和多态概念")
print("\n下一步：学习使用pandas和numpy进行数据分析！")