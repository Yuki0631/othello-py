class Piece:
    """
    Othello の石を表す
    owner: 0=黒, 1=白
    """
    def __init__(self, owner: int):
        self.owner = owner
