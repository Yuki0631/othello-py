import abc
import socket
from .piece import Piece
from .field import OthelloField as Field
from .protocol import Command, Protocol

def play_game(host: str, port: int, player: 'Player'):
    '''
    プレイヤーとサーバを接続して対局する関数
    '''
    with socket.create_connection((host, port)) as sock: # サーバに接続
        conn = sock.makefile(mode='rw', buffering=1, encoding='utf-8') # テキストモードで読み書きするファイルオブジェクトを作
                                                                       # 文字化エンコーディングはUTF-8

        # IDを受信する
        parts = conn.readline().strip().split() # サーバからの最初の行を読み込み、空白で分割
        if parts[0] != Command.ID.value:
            raise RuntimeError(f"Expected ID, got {parts!r}") # コマンドがIDでない場合はエラー
        player_id = int(parts[1])

        # 挨拶をする
        print(conn.readline().strip()) # サーバからの挨拶を読み込み、表示
        # 自分の名前をサーバへ通知
        print(f"{Command.NAME.value} {player.name()}", file=conn)
        conn.flush()

        # 盤面初期化を待つ
        init = None
        while True:
            l = conn.readline() # サーバからの次の行を読み込む
            if not l: raise RuntimeError("Closed before BOARD")
            if l.startswith(Command.BOARD.value):
                init = l.strip()
                break

        # 盤面を初期化する
        field = Field()
        player.initialize(field, player_id)
        player.handle_message(init)

        # メインループ
        while True:
            l = conn.readline()
            if not l:
                print("Connection closed")
                break
            msg = l.strip()

            if msg in (Protocol.you_win, Protocol.you_lose, Protocol.draw):
                print(msg)
                break

            # ILLEGAL_COUNT の処理
            if msg.startswith(Command.ILLEGAL_COUNT.value):
                parts = msg.split()
                player.illegal_count = int(parts[1])
                player.opponent_illegal_count = int(parts[2])
                print(f"Illegal moves → You: {parts[1]}, Opponent: {parts[2]}")
                player.handle_message(msg)
                continue

            player.handle_message(msg) # プレイヤーにメッセージを処理させる

            if msg == "your turn":
                mv = player.action() # プレイヤーのアクションを取得
                print(mv, file=conn)
                conn.flush()
            if msg.startswith(Command.GAME_OVER.value):
                print("=== Game Over ===")
                break

class Player(abc.ABC):
    """
    プレイヤーの基底クラス
    このクラスを継承して、具体的なプレイヤーを実装する
    initialize(field: Field, player_id: int) : 盤面とプレイヤーIDを初期化する
    name() -> str : プレイヤーの名前を返す
    action() -> str : プレイヤーのアクションを返す（着手コマンド）
    handle_message(msg: str) : サーバからのメッセージを処理する
    """
    def __init__(self):
        self.field: Field = None
        self.player_id: int = None
        self.illegal_count: int = 0
        self.opponent_illegal_count: int = 0
        self.last_flip_count: int = 0

    def initialize(self, field: Field, player_id: int):
        '''
        盤面とプレイヤーIDを初期化する関数
        '''
        self.field = field
        self.player_id = player_id

    @abc.abstractmethod
    def name(self) -> str:
        """
        プレイヤーの名前を返す関数
        """

    @abc.abstractmethod
    def action(self) -> str:
        """
        プレイヤーのアクションを返す関数
        """

    def handle_message(self, msg: str):
        """
        サーバからのメッセージを処理する関数
        盤面情報と石がいくつひっくり返ったかを更新する
        """
        parts = msg.split() # メッセージを空白で分割
        cmd = parts[0] # コマンドを取得
        if cmd == Command.BOARD.value: # コマンドがBOARDの場合
            flat = parts[1] # 盤面のフラットな文字列を取得
            size = Field.SIZE # 盤面のサイズを取得 今回は6
            for y in range(size):
                for x in range(size):
                    self.field.board[y][x] = None # 盤面を空にする
            for idx,ch in enumerate(flat): # 盤面の文字列を走査
                if ch == str(self.player_id): # もし、その文字が自分のIDと一致する場合
                    y,x = divmod(idx,size) # その文字の位置を計算
                    self.field.board[y][x] = Piece(self.player_id) # その位置に自分の石を置く
            return
        if cmd == Command.FLIP_COUNT.value:
            self.last_flip_count = int(parts[1])
            return

        return
