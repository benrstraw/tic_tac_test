import asyncio
import websockets

async def handler(websocket, path):
	async for message in websocket:
		print(message)

start_server = websockets.serve(hello, "", 4629)
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()