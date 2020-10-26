import asyncio
import websockets
import json
import random
import queue

# Initalize the global games dictionary.
games = dict()

open_queue = queue.Queue()


def fmt_host(websocket):
	# return str(websocket.remote_address[0]) + ":" + str(websocket.remote_address[1])
	return str(websocket.remote_address[1])


class Game:
	# Initalize our class members.
	def __init__(self, priv):
		self.private = priv
		self.board = [ '', '', '', '', '', '', '', '', '' ]
		self.turn = random.choice(['X', 'O'])
		self.winner = None
		self.users = dict()
		self.playerx = None
		self.playero = None
		self.specs = set()
		self.id = hex(id(self)).lstrip("0x")


	def remove(self):
		print("G#" + self.id + ": Removing self from coordinator!")
		for user in self.users.keys():
			close()
		self.users.clear()
		games.pop(self)
		return


	# When a new uers is added, the first player is X, the second O, and any other spectators.
	def add_user(self, websocket):
		self.users[websocket] = None
		print("G#" + self.id + ": Users connected to this game: " + str(len(self.users)))
		if not self.playerx:
			self.playerx = websocket
			self.users[websocket] = 'X'
			print("G#" + self.id + ": Assigning user " + fmt_host(websocket) + " to X")
		elif not self.playero:
			self.playero = websocket
			self.users[websocket] = 'O'
			print("G#" + self.id + ": Assigning user " + fmt_host(websocket) + " to O")
		else:
			self.specs.add(websocket)


	def remove_user(self, websocket):
		self.users.pop(websocket)
		print("G#" + self.id + ": Users connected to this game: " + str(len(self.users)))
		if websocket == self.playerx:
			self.playerx = None
			print("G#" + self.id + ": Lost player X")
		elif websocket == self.playero:
			self.playero = None
			print("G#" + self.id + ": Lost player O")
		else:
			self.specs.remove(websocket)

		if not self.playerx and not self.playero:
			self.remove()
		elif not self.playerx or not self.playero:
			if self.private:
				print("G#" + self.id + ": Game is missing a player, but private; not marking as open!")
			else:
				open_queue.put(self)
				print("G#" + self.id + ": Adding game to open game queue!")


	async def reset_game(self):
		await asyncio.sleep(4)
		print("G#" + self.id + ": Resetting gamestate!")
		self.board = [ '', '', '', '', '', '', '', '', '' ]
		self.turn = random.choice(['X', 'O'])
		self.winner = None
		await self.broadcast_gamestate()


	def get_gamestate(self, user):
		return { 'you': self.users[user], 'turn': self.turn, 'winner': self.winner, 'playerx': bool(self.playerx), 'playero': bool(self.playero), 'specs': len(self.specs), 'board': self.board }

	async def send_gamestate(self, user):
		print("G#" + self.id + ": Sending gamestate to user " + fmt_host(user))
		await user.send(json.dumps(self.get_gamestate(user)))


	async def broadcast_gamestate(self):
		print("G#" + self.id + ": Broadcasting gamestate to all users...")
		await asyncio.wait([user.send(json.dumps(self.get_gamestate(user))) for user in self.users.keys()])


	async def handle(self, websocket, message):
		player = str(self.users[websocket])
		if player == '':
			print("G#" + self.id + ": Got an attempted message from a spectator! (" + fmt_host(websocket) + ") Dropping...")
			return

		if not player == self.turn:
			print("G#" + self.id + ": Got message from " + player + " but it wasn't their turn! ('" + player + "' != '" + str(self.turn) + "')")
			return

		index = int(message)
		print("G#" + self.id + ": Attempting to place " + player + "'s piece at position " + str(index) + "...")
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
				self.winner = "tie"
				self.turn = None
				print("G#" + self.id + ": There was a tie!")
				asyncio.create_task(self.reset_game())
			elif self.winner:
				self.turn = None
				print("G#" + self.id + ": " + self.winner + " is the winner!")
				asyncio.create_task(self.reset_game())

			await self.broadcast_gamestate()
		else:
			print("G#" + self.id + ": " + player + " attempted to place at position " + str(index) + " but it was already occupied by " + str(self.board[index]))


async def handler(websocket, path):
	host = fmt_host(websocket)
	print("COORDINATOR: Got connection from " + host + " on path " + str(path))

	game = None
	if path and path != "/":
		if path not in games:
			games[path] = Game(priv=True)
			print("COORDINATOR: Created new game G#" + games[path].id + " on path " + str(path))

		game = games[path]
	else:
		if not open_queue.empty():
			game = open_queue.get()
			print("COORDINATOR: Assigned user " + host + " to game G#" + game.id)
		else:
			game = Game(priv=False)
			open_queue.put(game)
			print("COORDINATOR: Created new open game G#" + game.id + " for user " + host)

	print("COORDINATOR: Currently tracking " + str(len(games)) + " games.")

	game.add_user(websocket)

	await game.broadcast_gamestate()

	try:
		async for message in websocket:
			await game.handle(websocket, message)
	except:
		pass
	finally:
		print("COORDINATOR: User " + host + " disconnected, removing from game #" + game.id + " on path " + str(path))
		game.remove_user(websocket)

print("Serving...")
gameserver = websockets.serve(handler, "", 4629)
asyncio.get_event_loop().run_until_complete(gameserver)
asyncio.get_event_loop().run_forever()