import asyncio
import websockets
import json
import random


games = dict()


class Game:
	def __init__(self):
		self.users = set()
		self.board = [ '', '', '', '', '', '', '', '', '' ]
		self.turn = random.choice(['x', 'o'])
		self.playerx = None
		self.playero = None

	def add_user(self, websocket):
		self.users.add(websocket)
		if self.playerx and self.playero:
			return False
		elif self.playerx:
			self.playero = websocket
			return True
		else:
			self.playerx = websocket
			return True


	def remove_user(self, websocket):
		self.users.remove(websocket)
		print('Users connected to this match: ' + str(len(self.users)))
		if websocket == self.playerx:
			self.playerx = None
		elif websocket == self.playero:
			self.playero = None


	async def handle(self, websocket, message):
		if websocket == self.playerx and self.turn == 'x':
			player = 'x'
		elif websocket == self.playero and self.turn == 'o':
			player = 'o'
		else:
			return

		index = int(message)
		if self.board[index] == '':
			self.board[index] = player

			if player == 'x':
				self.turn = 'o'
			else:
				self.turn = 'x'

			winner = None
			if self.board[0] != '' and self.board[0] == self.board[1] and self.board[1] == self.board[2]:
				winner = self.board[0]
			elif self.board[3] != '' and self.board[3] == self.board[4] and self.board[4] == self.board[5]:
				winner = self.board[4]
			elif self.board[6] != '' and self.board[6] == self.board[7] and self.board[7] == self.board[8]:
				winner = self.board[6]
			elif self.board[0] != '' and self.board[0] == self.board[3] and self.board[3] == self.board[6]:
				winner = self.board[0]
			elif self.board[1] != '' and self.board[1] == self.board[4] and self.board[4] == self.board[7]:
				winner = self.board[1]
			elif self.board[2] != '' and self.board[2] == self.board[5] and self.board[5] == self.board[8]:
				winner = self.board[2]
			elif self.board[0] != '' and self.board[0] == self.board[4] and self.board[4] == self.board[8]:
				winner = self.board[0]
			elif self.board[2] != '' and self.board[2] == self.board[4] and self.board[4] == self.board[6]:
				winner = self.board[2]

			if winner:
				await asyncio.wait([user.send(json.dumps({ 'winner': winner, 'board': self.board })) for user in self.users])
			else:
				await asyncio.wait([user.send(json.dumps({ 'turn': self.turn, 'board': self.board })) for user in self.users])


async def handler(websocket, path):
	host = str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1])
	print("Got connection from " + host + " on path " + str(path))

	if path not in games:
		print("Game doesn't already exist on path " + str(path) + " , creating...")
		games[path] = Game()

	game = games[path]
	if not game.add_user(websocket):
		return

	await websocket.send(json.dumps({ 'turn': game.turn, 'board': game.board }))

	try:
		print("Listening to " + host + "...")
		async for message in websocket:
			print("Message from " + host + ": " + message)
			await game.handle(websocket, message)
	finally:
		print("Websocket to " + host + " disconnected, removing user from game " + path + "...")
		game.remove_user(websocket)

start_server = websockets.serve(handler, "", 4629)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()