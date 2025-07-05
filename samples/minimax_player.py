# othello_pyファイルからのインポートを行うための設定
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import random
from othello_py import play_game, Player

class MinimaxPlayer(Player):
    """
    ミニマックスアルゴリズムを使用して着手を選ぶプレイヤークラス
    """


if __name__=="__main__":
    host,port = sys.argv[1], int(sys.argv[2]) # コマンドライン引数からホストとポートを取得
    play_game(host, port, MinimaxPlayer()) # ランダムプレイヤーでゲームを開始