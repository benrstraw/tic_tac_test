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


	async def broadcast_update(self):
		if self.users:
			await asyncio.wait([user.send(json.dumps({ 'turn': self.turn, 'board': self.board })) for user in self.users])


	async def handle(self, websocket, message):
		if websocket == self.playerx && self.turn == 'x':
			player = 'x'
		elif websocket == self.playero && self.turn == 'o':
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
			await self.broadcast_update()


async def handler(websocket, path):
	host = str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1])
	print("Got connection from " + host + " on path " + str(path))

	if path not in games:
		print("Game doesn't already exist on path " + str(path) + " , creating...")
		games[path] = Game()

	game = games[path]
	if not game.add_user(websocket):
		return

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