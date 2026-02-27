from random import gauss, randint
import matplotlib.pyplot as plt
class Stock:
    def __init__(self, name, params):
        self.name = name
        self.price = params[0]
        self.mean = params[0]
        self.volatility = params[1]
        self.history = []
        self.trend = params[2]
        self.softening_factor = params[3]
    
    def update_params(self, params):
        self.mean = params[0]
        self.volatility = params[1]
        self.trend = params[2]
        self.softening_factor = params[3]
    
    def update(self):
        prices = [gauss(self.mean, self.volatility) for _ in range(abs(self.trend) + 1)]
        if self.trend > 0:
            price_change = max(prices)
        else:
            price_change = min(prices)
        self.price = price_change
        self.history.append(self.price)
        
    def plot(self):
        plt.plot(self.history[-50:])
        plt.title(f"{self.name} $USD")
        plt.ylabel("Price ($USD)")
        plt.show()

# This usage will be handled by market 
if __name__ == "__main__":
    stock = Stock("Test stock", [100, 5, 0, 0.2])
    for i in range(50):
        stock.update()
        if randint(0,10) <= 1:
            trend = randint(-3, 3)
            stock.update_params([stock.price + trend*stock.softening_factor, stock.volatility + randint(-1,1), trend, stock.softening_factor])
            print(f"At turn {i}: trend changed to {trend}")
    stock.plot()
