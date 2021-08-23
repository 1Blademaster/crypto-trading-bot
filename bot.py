import os
import time
import traceback
from pprint import pprint

import pandas as pd
from binance.spot import Spot
from binance.websocket.spot.websocket_client import SpotWebsocketClient
from dotenv import load_dotenv
import matplotlib.pyplot as plt

TEST_NET = True

load_dotenv()

class TradingBot:
	def __init__(self, testnet):
		self.connectToBinance(testnet)

	def connectToBinance(self, testnet):
		client = Spot()

		if testnet:
			client = Spot(base_url='https://testnet.binance.vision', key=os.getenv('TESTNET_API_KEY'), secret=os.getenv('TESTNET_API_SECRET'))
			ws_client = SpotWebsocketClient(stream_url='wss://testnet.binance.vision/ws')
			# ws_client.start()
			print('Connected to the TestNet server')
		else:
			client = Spot(key=os.getenv('API_KEY'), secret=os.getenv('API_SECRET'))#
			ws_client = SpotWebsocketClient()
			# ws_client.start()
			print('Connected to the main server')

		self.client = client
		self.ws_client = ws_client

	def getData(self, symbol, interval, limit):
		frame = pd.DataFrame(self.client.klines(symbol.upper(), interval, limit=limit))
		frame = frame.iloc[:,:6]
		frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
		frame = frame.set_index('Time')
		frame.index = pd.to_datetime(frame.index, unit='ms')
		frame = frame.astype(float)

		return frame

	def strategyTest(self, symbol, quantity, entried=False):
		'''
		Buy if asset falls by more than 0.2% within the last 30mins
		Sell if asset rises by more than 0.15% or falls further by 0.15%
		'''
		df = self.getData(symbol, '1m', 30)
		print(df)
		cumulative_returns = (df.Open.pct_change() + 1).cumprod() - 1

		if not entried:
			if cumulative_returns[-1] > -0.002:
				order = self.client.new_order(
					symbol=symbol,
					side='BUY',
					type='MARKET',
					quantity=quantity
				)
				print(order)
				entried = True
			else:
				print('No Trade has been executed')
		
		if entried:
			while True:
				df = self.getData(symbol, '1m', 30)
				since_buy = df.loc[df.index > pd.to_datetime(order['transactTime'], unit='ms')]
				if len(since_buy) > 0:
					since_buy_return = (since_buy.Open.pct_change() + 1).cumprod() - 1
					if since_buy_return[-1] > 0.0015 or since_buy_return[-1] < -0.0015:
						order = self.client.new_order(
							symbol=symbol,
							side='SELL',
							type='MARKET',
							quantity=quantity
						)
						print(order)
						break

if __name__ == "__main__":
	tradingBot = TradingBot(TEST_NET)
	tradingBot.strategyTest('BTCUSDT', 0.1)