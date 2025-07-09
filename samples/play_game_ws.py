import abc
import asyncio
import websockets
from othello_py.protocol import Command, Protocol
from othello_py.player_base import Player


async def play_game_ws(uri: str, player: Player):
    async with websockets.connect(uri) as ws:
        msg = await ws.recv()
        if not msg.startswith(Command.ID.value):
            raise RuntimeError("Invalid protocol, expected ID")
        player_id = int(msg.split()[1])
        print(f"Player ID: {player_id}")

        while True:
            msg = await ws.recv()
            print(f"Received: {msg}")

            if msg == "your turn":
                move = await player.action() if asyncio.iscoroutinefunction(player.action) else player.action()
                await ws.send(move)
            elif msg == Protocol.you_win:
                print("You win!")
                break
            elif msg == Protocol.you_lose:
                print("You lose!")
                break
            elif msg == Protocol.draw:
                print("Draw")
                break
            else:
                player.handle_message(msg)
