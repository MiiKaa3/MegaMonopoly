import random
import mks_megamonopoly as mks

balances = {player: {stock: 0 for stock in mks.stocknamelist} for player in mks.players}
for player in balances.keys():
  balances[player][mks.money] = mks.startingmoney

def main():
  random.seed(333)
  playing = True
  turn = 0
  
  
  market = mks.initmarket()
  history = [mks.deepcopymarket(market)]

  for _ in range(10):
    mks.stepmarket(market)
    history.append(mks.deepcopymarket(market))
  
  mks.makeplot(history)
      
  while playing:
    playersleft = mks.players.copy()
    
    while True:
      try:
        activeplayer = mks.turndeterminer(playersleft)
        active = True
      
        while playing and active:
          if (parsed := mks.parseCommand(mks.getCommand(activeplayer, turn)))[0] in mks.EXIT_COMMAND:
            playing = False
            break
          
          elif parsed[0] in mks.PASS_COMMAND:
            active = False
            returncode = True
            
          elif parsed[0] in mks.AQUIRE_COMMAND:
            returncode = mks.aquire(balances, activeplayer, parsed[1])
            
          elif parsed[0] in mks.TRADE_COMMAND:
            returncode = mks.trade(balances, activeplayer, parsed[1], parsed[2])
            
          elif parsed[0] in mks.BUY_COMMAND:
            returncode = mks.buy(market, parsed[1].upper(), balances, activeplayer, parsed[2])
            
          elif parsed[0] in mks.SELL_COMMAND:
            returncode = mks.sell(market, parsed[1].upper(), balances, activeplayer, parsed[2])
            
          elif parsed[0] in mks.VIEW_COMMAND:
            returncode = mks.view(balances)
            
          elif parsed[0] in mks.MARKET_COMMAND:
            returncode = mks.viewmarket(market)

          mks.returnmsg(returncode)
            
      except:
          print('Moving to next turn...')
          turn += 1
          
          mks.randomevent(market, 3)
          mks.stepmarket(market)
          history.append(mks.deepcopymarket(market))
          mks.makeplot(history)
          break

    
if __name__ == '__main__':
  try:
    main()
  except:
    print(balances)