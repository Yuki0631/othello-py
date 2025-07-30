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

def choose_move(info: InfoSet, depth: int, player_id: int, illegal_moves_to_avoid: set[Move]) -> Move | None:
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
    def __init__(self, depth=4):
        super().__init__()
        self.depth = depth
        self.info_set: InfoSet = None
        self.just_moved = False
        self._pending_move: Move | None = None
        self._info_snapshot: InfoSet | None = None
        self.illegal_moves_this_turn: set[Move] = set()
        self.game_turn_count = 0 
    
    def name(self) -> str:
        return "IsMinimaxPlayer"
    
    def action(self) -> str:
        print(">> action() called") # デバッグ用にこのログを追加すると良いでしょう
        print(f"field in action: {self.field.get_board_state()}") # 現在の盤面状態を確認
        print(f"player_id in action: {self.player_id}")

        # ensure info_set is initialized
        if self.info_set is None:
             # This should ideally be handled by the first BOARD message in handle_message
             # But as a fallback, ensure it's not None
             self.info_set = InfoSet([copy.deepcopy(self.field)])
             print("InfoSet fallback initialized in action(). This might indicate a timing issue.")


        # choose_move 関数に illegal_moves_this_turn を渡すように修正
        move = choose_move(self.info_set, self.depth, self.player_id, self.illegal_moves_this_turn) # ここを修正
        
        if move is None:
            self.just_moved = False
            return "PASSED"
        
        self._pending_move = move
        self._info_snapshot = copy.deepcopy(self.info_set)

        print(f"IsMinimaxPlayer Chosen move: {move[0]} {move[1]}")
        return f"MOVE {move[0]} {move[1]}"
    
    def handle_message(self, msg: str) -> None:
        # 必ず先に基底クラスのhandle_messageを呼び出し、self.fieldを更新させる
        super().handle_message(msg) 

        parts = msg.split()
        cmd = parts[0]

        # ILLEGAL_COUNTの処理は変更なし
        if cmd == Command.ILLEGAL_COUNT.value:
            print(f"[IsMinimaxPlayer] Illegal moves → You: {self.illegal_count}, Opponent: {self.opponent_illegal_count}")
            
            if self._pending_move is not None:
                self.illegal_moves_this_turn.add(self._pending_move)
                print(f"Added {self._pending_move} to illegal_moves_this_turn.")

            # 不正手と通知されたら、InfoSetをAIが見ている現在の盤面で強制的にリセットする
            # self.field は super().handle_message で既に更新されているはず
            self.info_set = InfoSet([copy.deepcopy(self.field)]) # この行は維持
            print("InfoSet reset to current visible board due to illegal move.")

            self._pending_move = None
            self._info_snapshot = None
            return

        # BOARDコマンドの処理を修正
        elif cmd == Command.BOARD.value:
            # super().handle_message(msg) は既に上で呼び出されているので、self.field は最新になっている
            
            # InfoSetがまだ初期化されていないか、不正手でリセットされた場合
            if self.info_set is None: 
                # ゲーム開始時、または明示的にリセットされた後の最初のBOARDメッセージ受信時
                # self.field はサーバーからの最新の盤面情報が反映されているので、それをInfoSetのベースにする
                self.info_set = InfoSet([copy.deepcopy(self.field)]) 
                print("InfoSet initialized with current received board state (from BOARD msg).")
            else:
                # 自分の手番後、または相手の手番後に盤面が更新された場合
                # ここで情報集合の更新（相手の推測など）を行う必要がある
                if self.just_moved:
                    # 自分の手が成功して盤面が更新された場合
                    self.just_moved = False
                    self._pending_move = self._info_snapshot = None
                    self.illegal_moves_this_turn.clear()
                    print("Illegal moves list cleared for new turn.")
                    self.game_turn_count += 1
                    # 自分の手番成功後のInfoSetは、相手のターンで更新されるべきなので、ここでは特に変更しない。
                    # AIの見える盤面と完全に一致するInfoSetにするなら、ここでリセットも可能だが、
                    # _update_info_set()が相手のターンを推測するロジックなので、ここは相手ターン処理を待つ。
                else:
                    # 相手の手番後の盤面更新。相手の手を推測してInfoSetを更新
                    # この _update_info_set() が正しく self.info_set を更新すべき
                    # self.field はこの時点で最新の盤面状態（人間の手が打たれた後）になっている
                    self._update_info_set()
                    print("InfoSet updated based on opponent's move.")
            return # BOARDコマンドの処理が完了したらreturn

        # PASSEDコマンドの処理は変更なし
        elif msg == "PASSED":
            self.illegal_moves_this_turn.clear()
            print("Illegal moves list cleared due to PASSED.")
            self.game_turn_count += 1
            return
        
        # FLIP_COUNT は super().handle_message で処理済み

        # その他のメッセージは super().handle_message が処理する
        # ここでは return されない他のメッセージの場合、特に IsMinimaxPlayer 固有の処理は不要。
        # super().handle_message が最終的に return される。

    # _update_info_set メソッドは、引数を追加したデバッグコードを元に戻す

    def _update_info_set(self):
            print(f"--- _update_info_set called ---")
            # self.fieldはサーバーからの最新のBOARD情報が格納されている
            current_perceived_board_state = self.field.get_board_state() # デバッグ用
            print(f"self.field in _update_info_set (AI's current actual view): {current_perceived_board_state}")
            
            # AIが実際に「見える」形式の盤面を取得
            visible_board_for_comparison = self.field.get_visible_board(self.player_id) # ここが重要
            print(f"visible_board_for_comparison (AI's processed view for comparison): {visible_board_for_comparison}")

            flip_count = self.last_flip_count
            print(f"Update InfoSet - Current flip_count: {flip_count}")

            new_worlds: list[BoardState] = []

            if flip_count == 0: # 相手がパスした場合の処理
                print("Processing opponent's PASS (unexpected if flip_count != 0).")
                for world in self.info_set.worlds:
                    # 相手に合法手がなく、かつ「AIが実際にそのworldを見たときに」visible_board_for_comparison と一致するか
                    if not world.legal_moves(1 - self.player_id) and \
                    world.get_visible_board(self.player_id) == visible_board_for_comparison: # ここを修正
                        new_worlds.append(copy.deepcopy(world))
                if new_worlds:
                    self.info_set = InfoSet(new_worlds)
                else:
                    print("Warning: No matching worlds found for opponent's pass. Resetting InfoSet to current perceived board.")
                    self.info_set = InfoSet([copy.deepcopy(self.field)])
                print(f"--- _update_info_set finished (pass). New InfoSet world count: {len(self.info_set.worlds)}")
                return

            else: # 相手が石を置いた場合の処理 (flip_count > 0)
                print(f"Processing opponent's MOVE with flip_count: {flip_count}")
                
                # ログを追加して、各 world がなぜ除外されるのかを特定
                debug_skipped_worlds_count = 0
                debug_total_candidates_per_world = 0

                for world_idx, world in enumerate(self.info_set.worlds):
                    opp = 1 - self.player_id
                    world_legal_moves = world.get_legal_moves(opp)
                    debug_total_candidates_per_world += len(world_legal_moves)
                    
                    print(f"  -- World {world_idx} (from InfoSet) --")
                    board_state_in_world = world.get_board_state()
                    for row in board_state_in_world:
                        print("    " + "".join(['.' if x is None else str(x) for x in row]))
                    print(f"  World {world_idx} legal moves for opponent: {world_legal_moves}")

                    for move in world_legal_moves:
                        temp_world = copy.deepcopy(world)
                        try:
                            flips_in_this_move = temp_world.place(move[0], move[1], opp)
                            
                            # その仮定した手で盤面を更新した後、AIから見える盤面を取得
                            temp_world_visible = temp_world.get_visible_board(self.player_id)
                            
                            print(f"    Checking move {move} in World {world_idx}: flips={flips_in_this_move}, visible_after_move={temp_world_visible}")
                            
                            # 条件1: 可視盤面が一致するか
                            visible_match = (temp_world_visible == visible_board_for_comparison)
                            # 条件2: フリップ数が一致するか
                            flip_count_match = (flips_in_this_move == flip_count)

                            print(f"    Conditions: Visible Match={visible_match}, Flip Count Match={flip_count_match}")

                            if visible_match and flip_count_match:
                                new_worlds.append(temp_world)
                                print(f"    -> World {world_idx} with move {move} MATCHES! Added to new_worlds.")
                            else:
                                debug_skipped_worlds_count += 1
                                print(f"    -> World {world_idx} with move {move} SKIPPED (Visible Match: {visible_match}, Flip Count Match: {flip_count_match}).")

                        except ValueError:
                            print(f"    Move {move} was illegal in World {world_idx} (ValueError). SKIPPED.")
                            pass # このmoveはこのworldでは不正

                if new_worlds:
                    self.info_set = InfoSet(new_worlds)
                else:
                    # ここに到達した場合、なぜ new_worlds が空になったのか、上記のログで確認する
                    print(f"Warning: No matching worlds found after opponent's move (flip_count={flip_count}). Resetting info set to current perceived board. Skipped count: {debug_skipped_worlds_count}/{debug_total_candidates_per_world}")
                    self.info_set = InfoSet([copy.deepcopy(self.field)]) # AIの認識を強制的に現在の可視盤面にリセット
                print(f"--- _update_info_set finished (move). New InfoSet world count: {len(self.info_set.worlds)}")
                return
        
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
