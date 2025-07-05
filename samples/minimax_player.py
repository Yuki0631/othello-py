# othello_pyファイルからのインポートを行うための設定
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py import play_game, Player

class MinimaxPlayer(Player):
    """
    ミニマックスアルゴリズムを使用して着手を選ぶプレイヤークラス
    """
    def __init__(self, depth=5):
        """
        コンストラクタ
        depth: ミニマックスの探索の深さ (デフォルト値は5)
        """
        super().__init__()
        self.depth = depth

    def evaluate(self, field_state, player_id) -> int:
        """
        盤面の評価関数
        field_state: 現在の盤面状態
        player_id: プレイヤーID
        戻り値: 評価値 (整数)
        """
        # 単純に自分の石の数を評価値とする
        my_pieces = field_state.count_pieces(player_id)
        opponent_pieces = field_state.count_pieces(1 - player_id)
        return my_pieces - opponent_pieces
        

    def minimax(self, depth: int, field_state) -> tuple[int, str]:
        """
        ミニマックスアルゴリズムを実装する関数
        depth: 探索の深さ
        maximizing_player: 最大化プレイヤーかどうか
        field_state: 現在の盤面状態
        戻り値: (utility/eval, action)
        """
        return self.max_value(depth, field_state)

    def max_value(self, depth: int, field_state) -> tuple[int, str]:
        """
        最大化プレイヤーの評価関数
        depth: 探索の深さ
        field_state: 現在の盤面状態
        戻り値: (utility/eval, move)
        """
        if depth == 0 or field_state.is_game_over():
            return self.evaluate(field_state, self.player_id), "PASS"
        best_value = float('-inf')
        best_move = "PASS"
        for move in field_state.get_legal_moves(self.player_id):
            new_state = field_state.make_move(move, self.player_id)
            value, _ = self.minimax(depth - 1, False, new_state)
            if value > best_value:
                best_value = value
                best_move = move
        return best_value, best_move

    def min_value(self, depth: int, field_state) -> tuple[int, str]:
        """
        最小化プレイヤーの評価関数
        depth: 探索の深さ
        field_state: 現在の盤面状態
        戻り値: (utility/eval, move)
        """
        if depth == 0 or field_state.is_game_over():
            return self.evaluate(field_state, 1-self.player_id), "PASS"
        best_value = float('inf')
        best_move = "PASS"
        for move in field_state.get_legal_moves(1-self.player_id):
            new_state = field_state.make_move(move, 1-self.player_id)
            value, _ = self.minimax(depth - 1, True, new_state)
            if value < best_value:
                best_value = value
                best_move = move
        return best_value, best_move
    
    def name(self) -> str:
        return "minimax-player"
    
    def action(self) -> str:
        """
        ミニマックスアルゴリズムを使用して最適な着手を選ぶ関数
        """
        best_value, best_move = self.minimax(self.depth, self.field)
        print(f"Best move: {best_move} with value {best_value}")
        return best_move if best_move != "PASS" else "PASSED"


if __name__=="__main__":
    host,port = sys.argv[1], int(sys.argv[2]) # コマンドライン引数からホストとポートを取得
    play_game(host, port, MinimaxPlayer()) # ランダムプレイヤーでゲームを開始
