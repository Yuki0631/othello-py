import sys, os, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py import play_game, Player
from othello_py.field import OthelloField
from othello_py.protocol import Command

Move = tuple[int, int]
BoardState = OthelloField

class InfoSet:
    """
    情報セットに関するクラス
    矛盾がなく、その状態の可能性がある世界を集合で管理する    
    """
    def __init__(self, worlds: list[BoardState]):
        self.worlds = worlds
        

    def possible_moves(self, player_id: int) -> set[Move]:
        """
        少なくとも1つの世界で可能な着手を返す
        """
        moves = set()
        for world in self.worlds:
            moves |= set(world.get_legal_moves(player_id)) # 合法手を取得して既存の集合に追加する
        return moves
    
def evaluate_world(state: BoardState, player_id: int) -> int:
    """
    盤面の評価関数
    完全情報下での評価関数
    ここでは石差を評価値とする
    """
    my_pieces = state.count_pieces(player_id)
    opponent_pieces = state.count_pieces(1 - player_id)
    return my_pieces - opponent_pieces

def max_value(info: InfoSet, depth: int, player_id: int) -> int:
    """
    最大化プレイヤーの評価関数
    info: 情報セット
    depth: 探索の深さ
    player_id: プレイヤーID
    戻り値: 評価値 (整数)
    """
    # 再帰の終了条件または例外的に評価値を返す場合
    if depth == 0 or not info.worlds: # 探索の深さが0または情報セットが空なら評価値を返す
        return evaluate_world(info.worlds[0], player_id) if info.worlds else 0
    
    if all(world.is_game_over() for world in info.worlds): # 全ての世界がゲーム終了なら評価値を返す
        return evaluate_world(info.worlds[0], player_id) if info.worlds else 0
    
    if not info.possible_moves(player_id): # 合法手がなければ評価値を返す
        return evaluate_world(info.worlds[0], player_id) if info.worlds else 0
    
    # 合法手がある場合
    best_value = float('-inf')
    for move in info.possible_moves(player_id): # 各可能な着手を試す
        next_worlds = set()
        for world in info.worlds:
            if move in world.get_legal_moves(player_id): # 合法手であれば、着手を適用した新しい世界を生成
                new_world = copy.deepcopy(world) # 盤面をコピー
                new_world.place(move[0], move[1], player_id) # 着手を適用
                next_worlds.add(new_world) # 新しい盤面を次の世界として追加
        if not next_worlds:
            continue
        value = min_value(InfoSet(list(next_worlds)), depth - 1, 1 - player_id)
        best_value = max(best_value, value)
    return best_value

def min_value(info: InfoSet, depth: int, player_id: int) -> int:
    """
    最小化プレイヤーの評価関数
    info: 情報セット
    depth: 探索の深さ
    player_id: プレイヤーID
    戻り値: 評価値 (整数)
    """
    # 再帰の終了条件または例外的に評価値を返す場合
    if depth == 0 or not info.worlds: # 探索の深さが0または情報セットが空なら評価値を返す
        return evaluate_world(info.worlds[0], player_id) if info.worlds else 0
    
    if all(world.is_game_over() for world in info.worlds): # 全ての世界がゲーム終了なら評価値を返す
        return evaluate_world(info.worlds[0], player_id) if info.worlds else 0
    
    if not info.possible_moves(player_id): # 合法手がなければ評価値を返す
        return evaluate_world(info.worlds[0], player_id) if info.worlds else 0
    
    # 合法手がある場合
    best_value = float('inf')
    for move in info.possible_moves(player_id): # 各可能な着手を試す
        next_worlds = set()
        for world in info.worlds:
            if move in world.get_legal_moves(player_id): # 合法手であれば、着手を適用した新しい世界を生成
                new_world = copy.deepcopy(world) # 盤面をコピー
                new_world.place(move[0], move[1], player_id) # 着手を適用
                next_worlds.add(new_world) # 新しい盤面を次の世界として追加
        if not next_worlds:
            continue
        value = max_value(InfoSet(list(next_worlds)), depth - 1, 1 - player_id)
        best_value = min(best_value, value)
    return best_value

def is_minimax(info: InfoSet, depth: int, player_id: int) -> int:
    """
    情報集合ミニマックス法により評価値を計算する関数
    info: 情報セット
    depth: 探索の深さ
    player_id: プレイヤーID
    戻り値: 評価値 (整数)
    """
    return max_value(info, depth, player_id)

def choose_move(info: InfoSet, depth: int, player_id: int) -> Move | None:
    """
    情報集合ミニマックス法により最適な着手を選択する関数
    info: 情報セット
    depth: 探索の深さ
    player_id: プレイヤーID
    戻り値: 最適な着手 (Move) または None
    """
    bast_val = float('-inf')
    best_move = None
    for move in info.possible_moves(player_id):
        next_worlds = set()
        for world in info.worlds:
            if move in world.get_legal_moves(player_id):
                new_world = copy.deepcopy(world)
                new_world.place(move[0], move[1], player_id)
                next_worlds.add(new_world)
        if not next_worlds:
            continue
        value = min_value(InfoSet(list(next_worlds)), depth - 1, 1 - player_id)
        if value > bast_val:
            bast_val = value
            best_move = move
    return best_move

class IsMinimaxPlayer(Player):
    """
    情報集合ミニマックスアルゴリズムを使用して着手を選ぶプレイヤークラス
    """
    def __init__(self, depth=3):
        """
        コンストラクタ
        depth: ミニマックスの探索の深さ (デフォルト値は3)
        """
        super().__init__()
        self.depth = depth
        self.info_set: InfoSet = None # 情報集合を初期化する
        self.just_moved = False # 最後の着手が自分の手かどうか
    
    def name(self) -> str:
        return "IsMinimaxPlayer"
    
    def action(self) -> str:
        """
        情報集合ミニマックスアルゴリズムを使用して最適な着手を選ぶ関数
        """
        if self.info_set is None:
            self.info_set = InfoSet([OthelloField()]) # 初期世界として、相手の石も含めた初期盤面を設定する
        
        move = choose_move(self.info_set, self.depth, self.player_id)
        if move is None:
            self.just_moved = False
            return "PASSED"
        
        x, y = move

        new_worlds: list[BoardState] = []
        for world in self.info_set.worlds:
            if move in world.get_legal_moves(self.player_id):
                new_world = copy.deepcopy(world)
                new_world.place(x, y, self.player_id)
                new_worlds.append(new_world)
        if new_worlds:
            self.info_set = InfoSet(new_worlds) # 新しい世界を情報集合に更新する
         
        self.just_moved = True # 最後の着手が自分の手であることを記録する
        print(f"Chosen move: {x} {y}")
        return f"MOVE {x} {y}"
    
    def handle_message(self, msg: str) -> None:
        """
        サーバから来る BOARD, FLIP_COUNT, TURN_ENDなどのメッセージを受け取って
        可視盤面自体の更新と、相手手を仮定して世界の更新を行う
        """
        parts = msg.split()
        cmd = parts[0]

        if cmd == Command.BOARD.value:
            super().handle_message(msg) # player_base.pyのhandle_messageを呼び出して盤面を更新
            if self.info_set is None:
                # 初回のBOARD受信時にのみInfoSetを初期生成する
                self.info_set = InfoSet([OthelloField()]) # 初期世界として、相手の石も含めた初期盤面を設定する
                self.last_flip_count = 0
            else:
                if self.just_moved:
                    self.just_moved = False # 最後の着手が自分の手であった場合はフラグをリセットする
                else:
                    # 相手の手を仮定して情報集合を更新する
                    self._update_info_set()

        elif cmd == Command.FLIP_COUNT.value:
            parts = msg.split()
            self.last_flip_count = int(parts[1]) # 最後のひっくり返った石の数を更新
        else:
            super().handle_message(msg)


    def _update_info_set(self):
        """
        情報集合を更新する関数
        現在の盤面と相手の手を考慮して情報集合を更新する
        """
        new_worlds: list[BoardState] = []
        # サーバから返ってきた、可読な盤面情報とひっくり返った石の数を使って、情報集合を更新する
        visible_board = self.field.get_visible_board(self.player_id)
        flip_count = self.last_flip_count

        # まずパスのケースを処理
        if flip_count == 0:
            # 相手にパスがあった場合、相手に合法手なかった世界だけを残す
            for world in self.info_set.worlds:
                if not world.get_legal_moves(1 - self.player_id):
                    new_worlds.append(copy.deepcopy(world))
            if new_worlds:
                self.info_set = InfoSet(new_worlds)
                return
        
            # 一致する世界がない場合は、古い情報集合をそのまま保持する
            return

        for world in self.info_set.worlds:
            # worldは過去における仮説的な盤面情報を保持している
            for move in world.get_legal_moves(opp := 1 - self.player_id):
                # 相手の手を仮定して新しい盤面を生成
                new_world = copy.deepcopy(world)
                flips = new_world.place(move[0], move[1], opp) # 相手の手を適用してひっくり返る石の数を取得

                # 可読な盤面とひっくり返った石の数を考慮して、情報集合に追加
                if new_world.get_visible_board(self.player_id) == visible_board and flips == flip_count:
                    new_worlds.append(new_world)
        
        if new_worlds:
            self.info_set = InfoSet(new_worlds)
        else:
            # 相手の手が合法手でない場合は、情報集合をそのまま保持し、
            # 警告を表示する
            print("No valid moves found for opponent, keeping current state.")
    
if __name__=="__main__":
    host,port = sys.argv[1], int(sys.argv[2]) # コマンドライン引数からホストとポートを取得
    play_game(host, port, IsMinimaxPlayer()) # 情報集合ミニマックスプレイヤーでゲームを開始
