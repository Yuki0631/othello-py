import sys, os, copy
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from othello_py import play_game, Player
from othello_py.field import OthelloField

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
    

    