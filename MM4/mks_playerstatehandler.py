import random
import pprint
import mks_commons as mks

def turndeterminer(names: list[str]) -> str:
  return names.pop(random.randrange(len(names)))


def aquire(balances: dict[str:int], active: str, amt: str) -> bool:  
  try:
    balances[active][mks.money] += int(amt)
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


def trade(balances: dict[str:int], active: str, target: str, amt: str) -> bool:
  try:
    balances[active][mks.money] += int(amt)
    balances[target][mks.money] -= int(amt)
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


