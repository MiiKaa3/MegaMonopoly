# Mega Monopoly 5
A python server runs on my home network.
Clients connect to the server via a webapp on their phone's broswer.
Player's can buy "virtual currency" with their physical cash, and can cash out with a time delay (keeps things fair, and ensures players can't only hold virtual currency).

Players can:
- buy stocks
- trade money with each other
- view a news feed (which ties into price action on the stock market)
- buy other securities? - gold, bonds, etc?

All player actions are server requests.
The server recieves these requests, gives them to a python backend which processes the requests, and then sends results back to the client, and updates the databases accordingly.

## Phase 1: Minimal Server
I want to be able to run a server, and serve some info to my client test devices.