import asyncio
import websockets
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py.protocol import Command
from othello_py import Player
from othello_py.player_base import play_game_ws

import random

class RandomPlayer(Player):
    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)
        self.legal_moves = []

    def name(self):
        return "random-player-ws"
    
    def handle_message(self, msg: str):
        try:
            super().handle_message(msg)
        except Exception as e:
            print("handle_message 例外:", e)
            return
        if msg.startswith("LEGAL_MOVES"):
            # サーバーから "LEGAL_MOVES x,y x,y ..." 形式で来ると仮定
            parts = msg.split()
            self.legal_moves = [tuple(map(int, p.split(','))) for p in parts[1:]]
        elif msg.startswith(Command.ILLEGAL_COUNT.value):
            parts = msg.split()
            self.illegal_count = int(parts[1])
            self.opponent_illegal_count = int(parts[2])
            print(f"[RandomPlayer] Illegal moves → You: {self.illegal_count}, Opponent: {self.opponent_illegal_count}")


    async def action(self): #すべての盤面から選ぶように変更
        
        print(">> action() called")
        print("field:", self.field)
        print("player_id:", self.player_id)

        legal_moves = self.field.get_legal_moves(self.player_id)  # 合法手の取得（メソッド名は例）
        if not legal_moves:
            return "PASSED"
        
        all_possible_moves = [(x, y) for x in range(6) for y in range(6)]

        while True:
            x, y = self.rng.choice(all_possible_moves)
            if self.field.is_legal_move(self.player_id, x, y):
                print(f"Legal move found: ({x}, {y})")
                return f"MOVE {x} {y}"
            else:
                print(f"Illegal move detected: ({x}, {y})")
                return f"ILLEGAL {x} {y}"


async def main():
    host, port = sys.argv[1], int(sys.argv[2])
    uri = f"ws://{host}:{port}/ws/player"
    player = RandomPlayer()
    await play_game_ws(uri, player)

if __name__=="__main__":
    import asyncio
    host, port = sys.argv[1], int(sys.argv[2])
    uri = f"ws://{host}:{port}/ws/player"
    player = RandomPlayer()
    asyncio.run(play_game_ws(uri, player))
