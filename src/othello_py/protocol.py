from enum import Enum
from typing import List, Optional

class Command(Enum):
    '''
    Othelloサーバーとクライアント間の通信で使用するコマンド定数
    文字列を指定することで、スペルミスやスペル違いによるエラーを防ぐ
    '''
    MOVE           = "MOVE" # 着手コマンド
    FLIP_COUNT     = "FLIP_COUNT" # ひっくり返る石の数
    BOARD          = "BOARD" # 盤面情報
    PASSED         = "PASSED" # パスの通知
    GAME_OVER      = "GAME_OVER" # ゲーム終了の通知
    ID             = "ID" # プレイヤーIDの通知
    ILLEGAL_COUNT  = "ILLEGAL_COUNT" # 不正手カウンタの通知
    NAME           = "NAME" # プレイヤー名の通知

class Protocol:
    """
    挨拶・勝敗通知定数
    """
    greeting = "Welcome to hidden-view Othello server."
    you_win   = "you win"
    you_lose  = "you lose"
    draw      = "draw"

def serialize_board(board: List[List[Optional[int]]]) -> str:
    """
    盤面を文字列に変換する関数
    board: 盤面の2次元リスト (None=空, 0=黒, 1=白)
    戻り値: 盤面のフラットな文字列
    """
    # 盤面情報をフラットな文字列に変換
    # Noneは'.'に変換し、0と1はそのまま文字列に変換
    # 例: [[None, 0, 1], [1, None, 0]] → ".01.1.0"
    # 盤面のサイズは6x6なので、6*6=36文字
    flat = ''.join(
        '.' if c is None else str(c)
        for row in board for c in row
    )
    return f"{Command.BOARD.value} {flat}"

def parse_move(msg: str) -> tuple[int,int]:
    """
    着手コマンドを解析する関数
    msg: 着手コマンドの文字列 (例: "MOVE 2 3")
    戻り値: (x座標, y座標) のタプル
    """
    parts = msg.split()
    if parts[0] != Command.MOVE.value or len(parts) != 3:
        raise ValueError(f"Invalid MOVE format: {msg!r}")
    return int(parts[1]), int(parts[2]) # x, y 座標を整数に変換して返す
