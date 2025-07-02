# othello_pyファイルからのインポートを行うための設定
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py import play_game, Player
from othello_py.protocol import Command

class ManualPlayer(Player):
    """
    手動で操作するプレイヤークラス
    このクラスは、ユーザーがコンソールから直接入力してゲームを操作する
    """
    def name(self) -> str:
        return "manual-player"

    def action(self) -> str:
        visible = self.field.get_visible_board(self.player_id)
        size = self.field.SIZE
        print("Your view:")
        for y in range(size):
            row = visible[y]
            print(f"{y} " + " ".join("●" if c==self.player_id else "." for c in row))
        print("   " + " ".join(str(x) for x in range(size)))
        print(f"Illegal count → You: {self.illegal_count}, Opponent: {self.opponent_illegal_count}")
        raw = input("Enter move as 'x y' (Enter to pass): ").strip()
        if not raw: return "PASSED"
        try:
            x,y = map(int, raw.split())
            return f"MOVE {x} {y}"
        except:
            return "PASSED"
    
    def handle_message(self, msg: str):
        # ILLEGAL_COUNT の更新を自前でキャッチ
        if msg.startswith(Command.ILLEGAL_COUNT.value):
            parts = msg.split()
            self.illegal_count = int(parts[1])
            self.opponent_illegal_count = int(parts[2])
        # BOARD の処理は親クラスに
        super().handle_message(msg)

if __name__=="__main__":
    host,port = sys.argv[1], int(sys.argv[2]) # コマンドライン引数からホストとポートを取得
    play_game(host, port, ManualPlayer()) # 手動プレイヤーでゲームを開始