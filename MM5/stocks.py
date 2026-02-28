from random import gauss, randint
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
        
    def update_trend(self, trend):
        self.trend = trend
    
    def update(self):
        prices = [gauss(self.mean, self.volatility) for _ in range(abs(self.trend) + 1)]
        if self.trend > 0:
            price_change = max(prices)
        else:
            price_change = min(prices)
        if randint(0,10) < 2:
            self.trend = 0
        self.price = price_change
        self.history.append(self.price)
        
    def plot(self, show: bool = True, path: str | None = None):
        """Optional debugging helper. Imports matplotlib lazily."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(self.history[-50:])
        plt.title(f"{self.name} $USD")
        plt.ylabel("Price ($USD)")
        if path:
            plt.savefig(path, bbox_inches="tight")
        if show and not path:
            plt.show()
        plt.close()

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
