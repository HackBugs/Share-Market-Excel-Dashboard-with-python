     import websockets
     import asyncio

     async def handler(websocket, path):
         async for message in websocket:
             if message == "reload" or message == "refreshcss":
                 await websocket.send(message)

     start_server = websockets.serve(handler, "localhost", 8501)
     asyncio.get_event_loop().run_until_complete(start_server)
     asyncio.get_event_loop().run_forever()
