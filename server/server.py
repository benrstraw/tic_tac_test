import asyncio
import websockets
import json
import random


games = dict()


class Game:
	def __init__(self):
		self.users = dict()
		self.board = [ '', '', '', '', '', '', '', '', '' ]
		self.turn = random.choice(['X', 'O'])
		self.playerx = None
		self.playero = None


	def add_user(self, websocket):
		self.users[websocket] = ''
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


	async def handle(self, websocket, message):
		player = self.users[websocket]
		if player == '':
			print("Got an attempted message from a spectator! Dropping...")
			return

		if not player == self.turn:
			print("Got message from " + player + " but it wasn't their turn! ('" + player + "' != '" + self.turn + "')")
			return

		index = int(message)
		print("Attempting to place " + player + "'s piece at position " + str(index) + "...")
		if self.board[index] == '':
			self.board[index] = player

			if self.turn == 'X':
				self.turn = 'O'
			else:
				self.turn = 'X'

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

			tie = True
			for x in self.board:
				if x == '':
					tie = False

			if tie:
				print("There was a tie!")
				await asyncio.wait([user.send(json.dumps({ 'you': self.users[user], 'winner': 'tie', 'board': self.board })) for user in self.users.keys()])
			elif winner:
				print(winner + " is the winner!")
				await asyncio.wait([user.send(json.dumps({ 'you': self.users[user], 'winner': winner, 'board': self.board })) for user in self.users.keys()])
			else:
				print("No winner, sending game state and awaiting...")
				await asyncio.wait([user.send(json.dumps({ 'you': self.users[user], 'turn': self.turn, 'board': self.board })) for user in self.users.keys()])
		else:
			print(player + " attempted to place at position " + str(index) + " but it was already occupied by " + self.board[index] + "!")


async def handler(websocket, path):
	host = str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1])
	print("Got connection from " + host + " on path " + str(path))

	if path not in games:
		print("Game doesn't already exist on path " + str(path) + " , creating...")
		games[path] = Game()

	game = games[path]
	game.add_user(websocket)

	await websocket.send(json.dumps({ 'you': game.users[websocket], 'turn': game.turn, 'board': game.board }))

	try:
		print("Listening to " + host + "...")
		async for message in websocket:
			await game.handle(websocket, message)
	finally:
		print("Websocket to " + host + " disconnected, removing user from game " + path + "...")
		game.remove_user(websocket)

start_server = websockets.serve(handler, "", 4629)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()