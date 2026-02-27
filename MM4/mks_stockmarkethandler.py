import mks_commons as mks
import random
import matplotlib.pyplot as plt
from math import exp, sqrt

def initmarket() -> dict[str:float]:
  result = dict()
  for stock in mks.stocknamelist:
    result[stock] = {'price': 50.0, 'mu': 2*(random.random()-0.5), 'sigma': 3*(random.random()-0.5)}
  return result
    
  
def stepmarket(market: dict[str:float]) -> None:
  for stock in mks.stocknamelist:
    market[stock]['price'] *= exp((market[stock]['mu'] - 0.5 * market[stock]['sigma'] ** 2) * (1. / 180.) + market[stock]['sigma'] * sqrt(1./180.) * random.gauss(mu=0, sigma=1))
    market[stock]['mu'] += random.random()*0.25
    market[stock]['sigma'] *= 0.98


def priceaction(market: dict[str:float], stock: str, var: str, amt: float, mode: int) -> None:
  if mode == 0: market[stock][var] = amt
  elif mode == 1: market[stock][var] += amt
  elif mode == 2: market[stock][var] *= amt
  
  
def buy(market: dict[str:float], stock:str, balances: dict[str:int], active: str, amt: str) -> bool:
  try:
    balance = balances[active][mks.money]
    price = market[stock]['price']
    value = price * int(amt)
    if value > balance:
      print('not enough money!')
      return False
    
    balances[active][mks.money] -= value
    balances[active][stock] += int(amt)
    return True
  except KeyError:
    print('Whoops! Key Error, awkies')
  except TypeError:
    print('Whoops! Type Error awkies')
  except ValueError:
    print('Whoops! Value Error awkies')
  except:
    print('zooweemama! thats an unknown error dawg')
  return False

def sell(market: dict[str:float], stock:str, balances: dict[str:int], active: str, amt: str) -> bool:
  try:
    balance = balances[active][stock]
    price = market[stock]['price']
    value = price * int(amt)
    if int(amt) > balance:
      print('not enough shares!')
      return False
    
    balances[active][mks.money] += value
    balances[active][stock] -= int(amt)
    return True
  except KeyError:
    print('Whoops! Key Error, awkies')
  except TypeError:
    print('Whoops! Type Error awkies')
  except ValueError:
    print('Whoops! Value Error awkies')
  except:
    print('zooweemama! thats an unknown error dawg')
  return False

def deepcopymarket(market: dict[str:float]) -> dict[str:dict[str:float]]:
  result = { key: {
      kkey: vvalue for (kkey, vvalue) in value.items()
    } 
    for (key, value) in market.items()
  }
  return result


def randomevent(market: dict[str:float], reps: int) -> None:
  picked = []
  globalchosen = False
  price = 'price'
  mu = 'mu'
  sigma = 'sigma'
  
  for _ in range(reps):
    chosen = False
    while not chosen:
      index, event = random.choice(mks.stockevents)
      if index < 4 and random.random() < 0.01 and not globalchosen:
        globalchosen = True
        chosen = True
      if index > 3:
        chosen = True
        
    if index < 4:
      print(f'Global - {event}')
      for stock in mks.stocknamelist:
        
        if index == 0:
          priceaction(market, stock, price, 0.76, 2)
          priceaction(market, stock, mu, -0.25, 1)
          priceaction(market, stock, sigma, 2, 2)
        if index == 1:
          priceaction(market, stock, mu, -0.25, 1)
          priceaction(market, stock, sigma, 1.1, 2)
        if index == 2:
          priceaction(market, stock, sigma, 2, 2)
        if index == 3:
          priceaction(market, stock, mu, 0.25, 1)
          priceaction(market, stock, sigma, 1.1, 2)
    
    elif index < 8:
      uniquestock = False
      while not uniquestock:
        stock = random.choice(mks.stocknamelist)
        if stock not in picked:
          uniquestock = True
          picked.append(stock)
      print(f'{stock} - {event}')
      
      if index == 4:
        priceaction(market, stock, mu, 0.05, 2)
      elif index == 5:
        priceaction(market, stock, mu, -0.5, 1)
        priceaction(market, stock, sigma, 1.5, 2)
      elif index == 6:
        priceaction(market, stock, mu, 0.35, 1)
        priceaction(market, stock, sigma, 1.25, 2)
      elif index == 7:
        priceaction(market, stock, mu, -0.35, 1)
        priceaction(market, stock, sigma, 1.25, 2)
    
    elif index < 13:
      uniquestock = False
      while not uniquestock:
        stock = random.choice(mks.stocknamelist[:3])
        if stock not in picked:
          uniquestock = True
          picked.append(stock)
      print(f'{stock} - {event}')
      
      if index == 8:
        priceaction(market, stock, price, 0.8, 2)
        priceaction(market, stock, mu, -0.2, 1)
        priceaction(market, stock, sigma, 1.2, 2)
      if index == 9:
        priceaction(market, stock, mu, -0.1, 1)
      if index == 10:
        priceaction(market, stock, mu, 0.3, 1)
      if index == 11:
        priceaction(market, stock, price, 1.2, 2)
        priceaction(market, stock, mu, 0.3, 1)
        priceaction(market, stock, sigma, 0.9, 2)
      if index == 12:
        priceaction(market, stock, price, 0.9, 2)
        priceaction(market, stock, mu, -0.3, 1)
        priceaction(market, stock, sigma, 1.1, 2)
      
    elif index < 17:
      uniquestock = False
      while not uniquestock:
        stock = random.choice(mks.stocknamelist[3:6])
        if stock not in picked:
          uniquestock = True
          picked.append(stock)
      print(f'{stock} - {event}')
      
      if index == 13:
        priceaction(market, stock, price, 1.2, 2)
        priceaction(market, stock, mu, 0.3, 1)
        priceaction(market, stock, sigma, 1.5, 2)
      if index == 14:
        priceaction(market, stock, price, 0.7, 2)
        priceaction(market, stock, mu, -0.5, 1)
        priceaction(market, stock, sigma, 0.8, 2)
      if index == 15:
        priceaction(market, stock, sigma, 1.5, 2)
      if index == 16:
        priceaction(market, stock, mu, -0.3, 1)
        priceaction(market, stock, sigma, 1.4, 2)
      
    else:
      uniquestock = False
      while not uniquestock:
        stock = random.choice(mks.stocknamelist[6:])
        if stock not in picked:
          uniquestock = True
          picked.append(stock)
      print(f'{stock} - {event}')
      
      if index == 17:
        priceaction(market, stock, mu, -0.5, 1)
      if index == 18:
        priceaction(market, stock, sigma, 1.6, 2)
      if index == 19:
        priceaction(market, stock, price, 1.2, 2)
        priceaction(market, stock, mu, 1.1, 2)
        priceaction(market, stock, sigma, 1.5, 2)
      if index == 20:
        priceaction(market, stock, mu, -0.5, 1)
        priceaction(market, stock, sigma, 1.3, 2)
        

def makeplot(history: list[dict[str:dict[str:float]]]) -> None:
  for stock in mks.stocknamelist:
    plt.plot(
      range(len(history)),
      [step[stock]['price'] for step in history],
      marker='o',
      markersize=6,
      label=stock,
      color=mks.stockcolors[stock]
    )
    plt.xticks(range(0,len(history), 1))
    plt.legend()
    plt.savefig(f'./figures/{stock}.png')  
    plt.cla()
    
  for stock in mks.stocknamelist:
    plt.plot(
      range(len(history)),
      [step[stock]['price'] for step in history],
      marker='o',
      markersize=6,
      label=stock,
      color=mks.stockcolors[stock]
    )
  plt.xticks(range(0,len(history), 1))
  plt.legend()
  plt.savefig(f'./figures/0alltogeter.png')  
  plt.cla()
    