import abc
import socket
import asyncio
import inspect
import websockets
from .piece import Piece
from .field import OthelloField as Field
from .protocol import Command, Protocol

async def play_game_ws(uri: str, player: 'Player'):
    async with websockets.connect(uri) as ws:
        # ID受信
        msg = await ws.recv()
        parts = msg.split()
        if parts[0] != Command.ID.value:
            raise RuntimeError("Expected ID from server")
        player_id = int(parts[1])
        player.initialize(player.field or Field(), player_id)  # フィールドは適宜用意

        # 挨拶受信
        greeting = await ws.recv()
        print(greeting)

        # 初期盤面受信
        while True:
            msg = await ws.recv()
            print("Sending the initial board...:", msg) 
            if msg.startswith(Command.BOARD.value):
                player.handle_message(msg)
                break

        # メインループ
        while True:
            msg = await ws.recv()
            if msg in (Protocol.you_win, Protocol.you_lose, Protocol.draw):
                print(msg)
                break

            if msg.startswith(Command.ILLEGAL_COUNT.value):
                parts = msg.split()
                player.illegal_count = int(parts[1])
                player.opponent_illegal_count = int(parts[2])
                print(f"Illegal moves → You: {parts[1]}, Opponent: {parts[2]}")
                player.handle_message(msg) # from Yuki added

                # 直後のBOARDも受け取って盤面更新
                board_msg = await ws.recv()
                player.handle_message(board_msg)

                # 再度打つ（再帰やループでなく、明示的にactionして送信）
                print("→ Re-attempting action after illegal move")
                mv = await player.action() if asyncio.iscoroutinefunction(player.action) else player.action()
                await ws.send(mv)
                continue

            player.handle_message(msg)

            if msg == "your turn":
                mv = await player.action() if asyncio.iscoroutinefunction(player.action) else player.action()
                await ws.send(mv)


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
        print(f">> initialize() called: player_id = {player_id}")
        self.field = field
        self.player_id = player_id

    @abc.abstractmethod
    def name(self) -> str:
        """
        プレイヤーの名前を返す関数
        """

    @abc.abstractmethod
    def action(self):
        """
        着手を返す（同期またはasync関数）
        """
    
    """
    @abc.abstractmethod
    def action(self) -> str:
        
        #プレイヤーのアクションを返す関数
    """

    def handle_message(self, msg: str):
        parts = msg.split()
        cmd = parts[0]
        if cmd == Command.BOARD.value:
            flat = parts[1]
            size = Field.SIZE
            for y in range(size):
                for x in range(size):
                    self.field.board[y][x] = None
            for idx, ch in enumerate(flat):
                y, x = divmod(idx, size)
                if ch == '.':
                    self.field.board[y][x] = None
                elif ch == '0':
                    self.field.board[y][x] = Piece(0)
                elif ch == '1':
                    self.field.board[y][x] = Piece(1)
            return

        if cmd == Command.FLIP_COUNT.value:
            self.last_flip_count = int(parts[1])
            return

        return
