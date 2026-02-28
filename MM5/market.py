import stocks
from random import randint, gauss
import math

class Market:
    def __init__(self, stockdict:dict[stocks.Stock]):
        self.stocks = stockdict
        self.turn_counter = 0
        
    def update(self):
        for stock in self.stocks.values():
            if randint(0,10) <= 1:
                trend = randint(-3, 3)
                stock.update_params([stock.price + trend*stock.softening_factor, stock.volatility + stock.softening_factor*randint(-5,5), trend, max(stock.softening_factor + gauss(0, 0.1), 0.1)])
                print(f"At turn {self.turn_counter}: trend changed to {trend}")
            stock.update()
        self.turn_counter += 1
    
    def plot(self, show: bool = True, path: str | None = None):
        """Optional debugging helper. Imports matplotlib lazily."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        stocks_list = list(self.stocks.values())
        n = len(stocks_list)

        if n == 0:
            return

        # --- grid size (max 4x4 for 16 stocks) ---
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)

        fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 3*rows))

        # axes handling when rows/cols == 1
        if rows == 1 and cols == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        # --- plot each stock ---
        for ax, stock in zip(axes, stocks_list):

            history = stock.history[-50:]  # last 50 points
            x = range(len(history))

            ax.plot(x, history)
            ax.set_title(stock.name)
            ax.set_ylabel("Price")
            ax.grid(True, alpha=0.3)

        # --- hide unused subplots ---
        for ax in axes[n:]:
            ax.set_visible(False)

        plt.tight_layout()
        if path:
            plt.savefig(path, bbox_inches="tight")
        if show and not path:
            plt.show()
        plt.close()
        
if __name__ == "__main__":
    stockdict = {
        "Test stock 1": stocks.Stock("Test stock 1", [100, 2, 0, 1]),
        "Test stock 2": stocks.Stock("Test stock 2", [50, 1, 0, 0.2]),
        "Test stock 3": stocks.Stock("Test stock 3", [200, 3, 0, 2]),
        "Test stock 4": stocks.Stock("Test stock 4", [75, 2, 0, 0.2])
    }
    market = Market(stockdict)
    for i in range(50):
        market.update()
    while True: 
        market.plot()
        for stock in market.stocks.values():
            print(f"{stock.name} at price {stock.price} with trend {stock.trend} and volatility {stock.volatility} and softening factor {stock.softening_factor}")
        if input("Continue? (y/n) ") != "y":
            break
        market.update()
    
        

# Summary of what I did
# Basic stock and stock container class
# The stock class has a price, mean, volatility, trend and softening factor. The market class contains a dict of stocks and updates them each turn. Each turn there is a chance for the trend to change, which also changes the mean and volatility. The plot function plots the last 50 points of each stock in a grid.
# The update method is akin to "rolling with advantage/disadvantage" in DnD, where the trend determines whether we take the max or min, and the number of rolls is determined by abs(trend). 
# Softening factor was added because I wanted to change mean and volatility and not have it be too extreme. I might need 2 softening factors but for now they are the same. The longterm behaviour hasn't been tested yet but I think it should be fine.

# Things to do:
# - Add news events that affect stocks or multiple stocks at once (include a class system like last time?)
# - Change the stock chart to a candle stick chart, but don't calc open, close, high and low, just fake it and have this current graph be the underlying chart. Prettify it I guess
# - Portfolio manager, which will be a similar set up to stock and market. i.e. each player has their own portfolio but the server has the manager which keeps track of everything
# - Smooth out the chart just a little because some of the charts are too volatile and it looks too spiky
