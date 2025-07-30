import asyncio
import websockets
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py import Player
from othello_py.protocol import Command
from othello_py.player_base import play_game_ws


class ManualPlayerWS(Player):
    def __init__(self, uri):
        super().__init__()
        self.uri = uri
        self.move_event = asyncio.Event()
        self.move = None
    
    def name(self) -> str:
        return "manual-player-ws"

    async def connect(self):
        self.websocket = await websockets.connect(self.uri)
        asyncio.create_task(self.recv_loop())

    async def recv_loop(self):
        async for msg in self.websocket:
            # UIからのクリック座標が player に送られてくる
            if msg.startswith("MOVE"):
                # 既にMOVEコマンドならそのままセット
                self.move = msg
                self.move_event.set()
            elif msg == "PASSED":
                self.move = "PASSED"
                self.move_event.set()
            elif msg.startswith("ILLEGAL"):
                # illegal count更新
                parts = msg.split()
                self.illegal_count = int(parts[1])
                self.opponent_illegal_count = int(parts[2])
                await self.websocket.send(f"UPDATE_ILLEGAL_COUNT {self.illegal_count} {self.opponent_illegal_count}") #追加

            else:
                # それ以外は盤面更新等を親に処理させる
                self.handle_message(msg)

    async def action(self) -> str:
        # UIから手が来るまで待つ
        self.move_event.clear()
        await self.move_event.wait()
        return self.move

if __name__ == "__main__":
    import sys
    import asyncio
    from othello_py import play_game_ws

    host = sys.argv[1]
    port = int(sys.argv[2])
    player = ManualPlayerWS("ws://localhost:8000/ws/player")

    async def main():
        await player.connect()
        await play_game_ws("ws://localhost:8000/ws/player", player)

    asyncio.run(main())
