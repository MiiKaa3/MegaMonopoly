EXIT_COMMAND = ['q', 'exit', 'quit']
PASS_COMMAND = ['p', 'pass']
AQUIRE_COMMAND = ['a', 'aquire']
TRADE_COMMAND = ['t', 'trade']
BUY_COMMAND = ['b', 'buy']
SELL_COMMAND = ['s', 'sell']
VIEW_COMMAND = ['v', 'view']
MARKET_COMMAND = ['m', 'market']
money = 'Money'
startingmoney = 2000
players = sorted(['daniel', 'renee', 'mae', 'leo', 'nikola'])
stocknamelist = ['XOM', 'CVX', 'ALD', 'APPL', 'MFST', 'GOOG', 'PFE', 'JNJ', 'CSL']
stockcolors = {'XOM': '#ff0000', 'CVX': '#00ff00', 'ALD': '#0000ff', 'APPL': '#ffd700', 'MFST': '#ff00ff', 'GOOG': '#00ffff', 'PFE': '#ff9900', 'JNJ': '#9900ff', 'CSL': '#00ff99'}
stockevents = [
  # Global
  (0, f'Global pandemic rocks economy!'),
  (1, f'A boom in crypto has caused investors to withdraw their money from the stock market!'),
  (2, f'A war declared between two international super powers! Causes supply chain issues.'),
  (3, f'An economic bubble popped! Investors flock to assets which make sense'),
  # General
  (4, f'Dividend paid! All shareholders recieve money equal to 10% of their holdings!'),
  (5, f'Shady dealings and corruption discovered in upper management! Several executives under invevstigation'),
  (6, f'Major aquisition announced!'),
  (7, f'Major aquisition falls through!'),
  # Energy
  (8, f'Major oil spill in gulf of Mexico. Company says they\'re sorry, regret catestrophe.'),
  (9, f'New green tech is threatening company\'s market share'),
  (10, f'New green tech is bringing new government contracts and subsidies to company'),
  (11, f'Purchased an overseas plant!'),
  (12, f'Much anticpated plant purchase falls through'),
  # Tech
  (13, f'Exciting new product is announced!'),
  (14, f'New product is a colossal failure'),
  (15, f'Company is impacted by global chip-shortage'),
  (16, f'A major hack has caused loss in consumer confidence'),
  # Healthcare
  (17, f'Vaccine trials catestrophically fail'),
  (18, f'Sued by vitims of drug'),
  (19, f'Aquired another pharamecutical company'),
  (20, f'Patent expiration on drug where company dominated market'),
]
