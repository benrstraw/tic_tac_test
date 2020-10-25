import asyncio
import websockets
import json
import random
import queue

# Initalize the global games dictionary.
games = dict()

open_queue = queue.Queue()


class Game:
	# Initalize our class members.
	def __init__(self):
		self.board = [ '', '', '', '', '', '', '', '', '' ]
		self.turn = random.choice(['X', 'O'])
		self.winner = None
		self.users = dict()
		self.playerx = None
		self.playero = None


	# When a new uers is added, the first player is X, the second O, and any other spectators.
	def add_user(self, websocket):
		self.users[websocket] = None
		print('Users connected to this game: ' + str(len(self.users)))
		if not self.playerx:
			self.playerx = websocket
			self.users[websocket] = 'X'
		elif not self.playero:
			self.playero = websocket
			self.users[websocket] = 'O'


	def remove_user(self, websocket):
		self.users.pop(websocket)
		print('Users connected to this game: ' + str(len(self.users)))
		if websocket == self.playerx:
			self.playerx = None
		elif websocket == self.playero:
			self.playero = None


	async def reset_game(self):
		await asyncio.sleep(4)
		print("Resetting gamestate...")
		self.board = [ '', '', '', '', '', '', '', '', '' ]
		self.turn = random.choice(['X', 'O'])
		self.winner = None
		await self.broadcast_gamestate()


	async def send_gamestate(self, user):
		print("Sending gamestate to user...")
		await user.send(json.dumps({ 'you': self.users[user], 'turn': self.turn, 'winner': self.winner, 'board': self.board }))


	async def broadcast_gamestate(self):
		print("Broadcasting gamestate to all users...")
		await asyncio.wait([user.send(json.dumps({ 'you': self.users[user], 'turn': self.turn, 'winner': self.winner, 'board': self.board })) for user in self.users.keys()])


	async def handle(self, websocket, message):
		player = str(self.users[websocket])
		if player == '':
			print("Got an attempted message from a spectator! Dropping...")
			return

		if not player == self.turn:
			print("Got message from " + player + " but it wasn't their turn! ('" + player + "' != '" + str(self.turn) + "')")
			return

		index = int(message)
		print("Attempting to place " + player + "'s piece at position " + str(index) + "...")
		if self.board[index] == '':
			self.board[index] = player

			if self.turn == 'X':
				self.turn = 'O'
			else:
				self.turn = 'X'

			if self.board[0] != '' and self.board[0] == self.board[1] and self.board[1] == self.board[2]:
				self.winner = self.board[0]
			elif self.board[3] != '' and self.board[3] == self.board[4] and self.board[4] == self.board[5]:
				self.winner = self.board[4]
			elif self.board[6] != '' and self.board[6] == self.board[7] and self.board[7] == self.board[8]:
				self.winner = self.board[6]
			elif self.board[0] != '' and self.board[0] == self.board[3] and self.board[3] == self.board[6]:
				self.winner = self.board[0]
			elif self.board[1] != '' and self.board[1] == self.board[4] and self.board[4] == self.board[7]:
				self.winner = self.board[1]
			elif self.board[2] != '' and self.board[2] == self.board[5] and self.board[5] == self.board[8]:
				self.winner = self.board[2]
			elif self.board[0] != '' and self.board[0] == self.board[4] and self.board[4] == self.board[8]:
				self.winner = self.board[0]
			elif self.board[2] != '' and self.board[2] == self.board[4] and self.board[4] == self.board[6]:
				self.winner = self.board[2]

			tie = True
			for x in self.board:
				if x == '':
					tie = False

			if tie:
				self.turn = None
				print("There was a tie!")
				asyncio.create_task(self.reset_game())
			elif self.winner:
				self.turn = None
				print(self.winner + " is the winner!")
				asyncio.create_task(self.reset_game())

			await self.broadcast_gamestate()
		else:
			print(player + " attempted to place at position " + str(index) + " but it was already occupied by " + str(self.board[index]) + "!")


async def handler(websocket, path):
	host = str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1])
	print("Got connection from " + host + " on path " + str(path))

	game = None
	if path:
		if path not in games:
			print("Game doesn't already exist on path " + str(path) + " , creating...")
			games[path] = Game()

		game = games[path]
	else:
		if not open_queue.empty():
			game = open_queue.get()
		else:
			game = Game()
			open_queue.put(game)

	game.add_user(websocket)

	await game.send_gamestate(websocket)

	try:
		print("Listening to " + host + "...")
		async for message in websocket:
			await game.handle(websocket, message)
	finally:
		print("Websocket to " + host + " disconnected, removing user from game " + path + "...")
		game.remove_user(websocket)

print("Serving...")
gameserver = websockets.serve(handler, "", 4629)
asyncio.get_event_loop().run_until_complete(gameserver)
asyncio.get_event_loop().run_forever()