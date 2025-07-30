import sys, os, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py import Player
from othello_py.player_base import play_game_ws
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
        '''
        すべての世界において、指定プレイヤーが打てる合法手を取得する
        '''
        if not self.worlds:
            return set()
        common = set(self.worlds[0].get_legal_moves(player_id))
        for world in self.worlds[1:]:
            common &= set(world.get_legal_moves(player_id))
        return common
    
    def union_moves(self, player_id: int) -> set[Move]:
        '''
        一つの世界において、指定プレイヤーが打てる合法手を取得する
        '''
        moves = set()
        for world in self.worlds:
            moves |= set(world.get_legal_moves(player_id))
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
    print(f"--- choose_move called (player_id: {player_id}, depth: {depth}) ---")
    print(f"  InfoSet world count: {len(info.worlds)}")

    # この時点での現在の盤面の状態（self.field）を確認するため、InfoSetの最初の世界をログに出す
    if info.worlds:
        print("  First world in InfoSet:")
        board_state = info.worlds[0].get_board_state()
        for row in board_state:
            # Noneは'.'、0は'0'、1は'1'に変換して表示
            print("    " + "".join(['.' if x is None else str(x) for x in row]))
        print(f"  First world legal moves for {player_id}: {info.worlds[0].get_legal_moves(player_id)}")
    
    common_moves = info.possible_moves(player_id)
    print(f"  Common possible moves: {common_moves}")

    union_moves = info.union_moves(player_id)
    print(f"  Union possible moves: {union_moves}")

    best_val = float('-inf')
    best_move = None
    candidate_moves = info.possible_moves(player_id)

    if not candidate_moves:
        print("  No common moves found, using union_moves for candidates.")
        candidate_moves = info.union_moves(player_id) # 合法手がない場合は、全ての合法手を候補にする
    
    if not candidate_moves:
        print("  No candidate moves at all. Returning None.")
        return None # 候補手が全くない場合はNoneを返す
    
    print(f"  Final candidate moves for evaluation: {candidate_moves}")
    
    for move in candidate_moves: # 各候補手を評価
        next_worlds = set()
        for world in info.worlds:
            if move in world.get_legal_moves(player_id):
                new_world = copy.deepcopy(world)
                new_world.place(move[0], move[1], player_id)
                next_worlds.add(new_world)
        if not next_worlds:
            print(f"  Move {move} did not result in any valid next worlds. Skipping.")
            continue
    
        value = min_value(InfoSet(list(next_worlds)), depth - 1, 1 - player_id)
        print(f"  Move {move} evaluated to value: {value}, current best_val: {best_val}, best_move: {best_move}")

        if value > best_val:
            best_val = value
            best_move = move
            print(f"  New best move: {best_move} with value {best_val}")

    print(f"--- choose_move returning: {best_move} ---")
    return best_move

class IsMinimaxPlayer(Player):
    """
    情報集合ミニマックスアルゴリズムを使用して着手を選ぶプレイヤークラス
    """
    def __init__(self, depth=4):
        """
        コンストラクタ
        depth: ミニマックスの探索の深さ (デフォルト値は4)
        """
        super().__init__()
        self.depth = depth
        self.info_set: InfoSet = None # 情報集合を初期化する
        self.just_moved = False # 最後の着手が自分の手かどうか
        self._pending_move: Move | None = None # 直前に送った手
        self._info_snapshot: InfoSet | None = None # 直前の情報集合のスナップショット
    
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
        
        self._pending_move = move
        self._info_snapshot = copy.deepcopy(self.info_set) # 現在の情報集合をスナップショットとして保存

        print(f"Chosen move: {move[0]} {move[1]}")
        return f"MOVE {move[0]} {move[1]}"
    
    def handle_message(self, msg: str) -> None:
        """
        サーバから来る BOARD, FLIP_COUNT, TURN_ENDなどのメッセージを受け取って
        可視盤面自体の更新と、相手手を仮定して世界の更新を行う
        """

        super().handle_message(msg) #

        parts = msg.split()
        cmd = parts[0]

        if cmd == Command.ILLEGAL_COUNT.value:
            print(f"[IsMinimaxPlayer] Illegal moves → You: {self.illegal_count}, Opponent: {self.opponent_illegal_count}") #
            
            if self._pending_move is not None and self._info_snapshot is not None:
                move = self._pending_move
                updated_worlds = []
                for world in self._info_snapshot.worlds:
                    if not world.is_legal_move(self.player_id, move[0], move[1]):
                        updated_worlds.append(world)
                if updated_worlds:
                    self.info_set = InfoSet(updated_worlds)
                    print(f"InfoSet updated after illegal move: {len(updated_worlds)} worlds remaining.")
                else:
                    #self.info_set = InfoSet(legal_worlds or self._info_snapshot.worlds)
                    self.info_set = InfoSet([copy.deepcopy(self.field)])
                    print("Warning: All worlds considered the move legal. InfoSet reset to current visible board.")
            self._pending_move = self._info_snapshot = None # スナップショットをクリア
            return

        elif cmd == Command.BOARD.value:
            super().handle_message(msg) # player_base.pyのhandle_messageを呼び出して盤面を更新
            if self.info_set is None:
                # 初回のBOARD受信時にのみInfoSetを初期生成する
                self.info_set = InfoSet([OthelloField()]) # 初期世界として、相手の石も含めた初期盤面を設定する
                self.last_flip_count = 0
            else:
                if self.just_moved:
                    self.just_moved = False # 最後の着手が自分の手であった場合はフラグをリセットする
                    self._pending_move = self._info_snapshot = None # スナップショットをクリア
                else:
                    # 相手の手を仮定して情報集合を更新する
                    self._update_info_set()

        elif cmd == Command.FLIP_COUNT.value:
            self.last_flip_count = int(parts[1]) # 最後のひっくり返った石の数を更新

            if self._pending_move is not None and self.last_flip_count > 0:
                x, y = self._pending_move
                worlds = []
                for world in self.info_set.worlds:
                    if (x, y) in world.get_legal_moves(self.player_id):
                        new_world = copy.deepcopy(world)
                        new_world.place(x, y, self.player_id)
                        worlds.append(new_world)
                if worlds:
                    self.info_set = InfoSet(worlds)
                else:
                    print("Warning: No valid worlds after flip count update.")
                self._pending_move = self._info_snapshot = None # スナップショットをクリア
                self.just_moved = True
            
            else:
                # 最後の着手が自分の手でなかった場合は、情報集合を更新しない
                self.just_moved = False
            return

        else:
            super().handle_message(msg)


    def _update_info_set(self):
        new_worlds: list[BoardState] = []
        visible_board = self.field.get_visible_board(self.player_id)
        flip_count = self.last_flip_count

        if flip_count == 0:
            # パスは合法手の有無に依らず起こり得るので、可視盤面の不変性で整合性を取る
            for world in self.info_set.worlds:
                if world.get_visible_board(self.player_id) == visible_board:
                    new_worlds.append(copy.deepcopy(world))
            if new_worlds:
                self.info_set = InfoSet(new_worlds)
            # 一致が無ければ、古い集合を保持（破綻防止）
            return

        for world in self.info_set.worlds:
            opp = 1 - self.player_id
            for move in world.get_legal_moves(opp):
                new_world = copy.deepcopy(world)
                flips = new_world.place(move[0], move[1], opp)
                if new_world.get_visible_board(self.player_id) == visible_board and flips == flip_count:
                    new_worlds.append(new_world)

        if new_worlds:
            self.info_set = InfoSet(new_worlds)
        else:
            # 整合性が取れない場合は、現在の情報集合を保持
            for world in self.info_set.worlds:
                new_world = copy.deepcopy(world)
                if new_world.get_visible_board(self.player_id) == visible_board:
                    new_worlds.append(new_world)
            if new_worlds:
                self.info_set = InfoSet(new_worlds)
            else:
                print("Warning: No matching worlds found after opponent's move. Keeping current info set.")

async def main():
    host, port = sys.argv[1], int(sys.argv[2])
    uri = f"ws://{host}:{port}/ws/player"
    player = IsMinimaxPlayer()
    await play_game_ws(uri, player)

if __name__=="__main__":
    import asyncio
    host, port = sys.argv[1], int(sys.argv[2])
    uri = f"ws://{host}:{port}/ws/player"
    player = IsMinimaxPlayer()
    asyncio.run(play_game_ws(uri, player))
