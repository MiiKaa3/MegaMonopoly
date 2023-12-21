import mks_commons as mks

def getCommand(active: str, turn: int) -> str:
  return input(f'Y{1+turn//4}Q{1+turn%4} - {active.capitalize()} >> ')
  

def parseCommand(cmd: str) -> None:
  return cmd.lower().split()


def returnmsg(code: bool) -> None:
  if code:
    pass
  else:
    print('failed')


def view(balances: dict[str:dict[str:int]]) -> bool:
  for player in balances.keys():
    print(f'\t{player}:')
    for stock in balances[player].keys():
      if balances[player][stock] != 0:
        print(f'\t\t{stock}: {balances[player][stock]:.2f}')
  return True


def viewmarket(market: dict[str:float]) -> bool:
  for stock in mks.stocknamelist:
    print(f'\t{stock}')
    print(f'\t\tPrice: {market[stock]["price"]:.2f}')
    print(f'\t\t{"Mu:":<6} {market[stock]["mu"]:.2f}')
    print(f'\t\tSigma: {market[stock]["sigma"]:.2f}')
    
  return True