from typing import List, Optional, Tuple
import copy

class Piece:
    """
    Othello の石を表す
    owner: 0=黒, 1=白
    """
    def __init__(self, owner: int):
        self.owner = owner

class OthelloField:
    """
    Othelloの盤面のクラス
    SIZE: 盤面のサイズ (6x6)
    board: 盤面の状態を表す2次元リスト
    初期状態では中央に4つの石が配置されている
    in_bounds: 座標が盤面内かどうかを判定するメソッド
    get_visible_board: プレイヤーの視界に入る盤面を取得するメソッド
    _captures: 指定位置に石を置いたときにひっくり返る石の座標を取得するメソッド
    legal_moves: 指定プレイヤーの合法手を取得するメソッド
    place: 指定位置に石を置き、ひっくり返る石の数を返すメソッド
    """

    SIZE = 6 # 盤面のサイズ 

    def __init__(self):
        """
        盤面の初期化を行う
        """
        # None=空, Piece(0)=黒, Piece(1)=白
        self.board: List[List[Optional[Piece]]] = [
            [None] * self.SIZE for _ in range(self.SIZE) # 6x6の盤面
        ]
        mid = self.SIZE // 2  # 3
        # 初期配置
        # (2,2), (3,3) = 白, (2,3), (3,2) = 黒
        self.board[mid-1][mid-1] = Piece(1)  # 白
        self.board[mid][mid]     = Piece(1)
        self.board[mid-1][mid]   = Piece(0) # 黒
        self.board[mid][mid-1]   = Piece(0)

    def check_in_bounds(self, x: int, y: int) -> bool:
        """
        指定された座標が盤面内にあるか判定するメソッド
        """
        return 0 <= x < self.SIZE and 0 <= y < self.SIZE

    def get_visible_board(self, player_id: int) -> List[List[Optional[int]]]:
        '''
        指定プレイヤーの司会に入る盤面を取得する関数
        player_id: プレイヤーのID (0=黒, 1=白)
        戻り値: 盤面の2次元リスト (None=空, player_id=そのプレイヤーの石)
        '''
        visible = [[None] * self.SIZE for _ in range(self.SIZE)]
        for y in range(self.SIZE):
            for x in range(self.SIZE):
                p = self.board[y][x]
                if p is not None and p.owner == player_id:
                    visible[y][x] = player_id # 自分の石はそのまま表示する
        return visible

    def _captures(self, x: int, y: int, owner: int) -> List[Tuple[int,int]]:
        '''
        指定位置に石を置いたときに、ひっくり返る石の座標をsh得する関数
        '''
        if not self.check_in_bounds(x, y) or self.board[y][x] is not None:
            return [] # 盤面外または既に石が置かれている場合は空リストを返す
        
        dirs = [(-1,-1), (0,-1), (1,-1), (-1,0), (1,0), (-1,1), (0,1), (1,1)] # 8方向
        flips: List[Tuple[int,int]] = []
        for dx, dy in dirs:
            path: List[Tuple[int,int]] = []
            nx, ny = x + dx, y + dy
            while self.check_in_bounds(nx, ny) and self.board[ny][nx] is not None and self.board[ny][nx].owner != owner: 
                # 条件としては、ひっくり返る石があるかつ、相手の石であること
                path.append((nx, ny)) # 相手の石の座標を記録
                nx += dx; ny += dy
            if path and self.check_in_bounds(nx, ny) and self.board[ny][nx] is not None and self.board[ny][nx].owner == owner:
                # 最後に自分の石がある場合、ひっくり返る石の座標を追加
                # ひっくり返る石の座標を flips に追加
                # ここで nx, ny は自分の石の座標
                flips.extend(path)
        return flips

    def legal_moves(self, owner: int) -> List[Tuple[int,int]]:
        '''
        指定プレイヤーの合法手を取得する関数
        '''
        legal_moves_list = []
        for x in range(self.SIZE):
            for y in range(self.SIZE):
                if self.board[y][x] is None and self._captures(x, y, owner):
                    legal_moves_list.append((x, y))
        return legal_moves_list
    

    def place(self, x: int, y: int, owner: int) -> int:
        '''
        石をひっくり返し、その数を返す関数
        '''
        flips = self._captures(x, y, owner) # ひっくり返る石の座標を取得
        if not flips:
            raise ValueError("Illegal move")
        self.board[y][x] = Piece(owner)
        for fx, fy in flips:
            self.board[fy][fx].owner = owner # ひっくり返る石のオーナーを変更
        return len(flips)
        
    def get_legal_moves(self, owner: int):
        """
        legal_moves のエイリアスとして実装
        指定プレイヤーの合法手を取得する
        """
        return self.legal_moves(owner)

    def make_move(self, move: Tuple[int,int], owner: int) -> 'OthelloField':
        """
        この手を打った後の新しい盤面を返す
        盤面を丸ごとコピーして place() を実行する
        """
        new_field = copy.deepcopy(self)
        x, y = move
        new_field.place(x, y, owner)
        return new_field

    def is_game_over(self) -> bool:
        """
        両プレイヤーに合法手がなければゲーム終了とみなす
        """
        return not self.legal_moves(0) and not self.legal_moves(1)

    def count_pieces(self, owner: int) -> int:
        """
        指定プレイヤーの石の数をカウントする
        owner: 0=黒, 1=白
        戻り値: 石の数
        """
        sum = 0
        for row in self.board:
            for piece in row:
                if piece is not None and piece.owner == owner:
                    sum += 1
        return sum
    
    def get_board_state(self) -> List[List[Optional[int]]]:
        """
        現在の盤面の状態を数値形式で返す。
        None = 空、0 = 黒、1 = 白
        """
        return [[None if cell is None else cell.owner for cell in row]for row in self.board]
    
    def is_legal_move(self, owner: int, x: int, y: int) -> bool:
        """
        指定された手 (x, y) が指定されたプレイヤー (owner) にとって合法であるかを判定します。
        """
        # 1. 盤面内であるか、かつ、そのマスが空であるか
        if not self.check_in_bounds(x, y) or self.board[y][x] is not None:
            return False
        
        # 2. その手を打つことで石がひっくり返るか
        return bool(self._captures(x, y, owner))
