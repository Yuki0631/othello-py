
# othello_pyファイルからのインポートを行うための設定
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import random
from othello_py import play_game, Player

class RandomPlayer(Player):
    """
    ランダムに着手を選ぶプレイヤークラス
    このクラスは、ランダムな位置に着手を行う
    seedを指定することで、同じランダムシーケンスを再現可能
    """
    def __init__(self, seed=None):
        super().__init__()
        self.rng = random.Random(seed)

    def name(self) -> str:
        return "random-player"

    def action(self) -> str:
        """
        ランダムに着手を選ぶ関数
        盤面のサイズに基づいてランダムな座標を生成し、MOVEコマンドを返す
        """
        size = self.field.SIZE # 盤面のサイズを取得
        # 空きマスを取得（自分・相手の石が置かれていないマス）
        empty_cells = []
        for y in range(size):
            for x in range(size):
                if self.field.board[y][x] is None:
                    empty_cells.append((x, y))
        # 空きマスがなければパス
        if not empty_cells:
            return "PASSED"
        # ランダムに選択
        x, y = self.rng.choice(empty_cells)
        print(f"Illegal count → You: {self.illegal_count}, Opp: {self.opponent_illegal_count}")
        return f"MOVE {x} {y}"

if __name__=="__main__":
    host,port = sys.argv[1], int(sys.argv[2]) # コマンドライン引数からホストとポートを取得
    play_game(host, port, RandomPlayer()) # ランダムプレイヤーでゲームを開始