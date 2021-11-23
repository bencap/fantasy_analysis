from base_api import BaseApi
from league import League
from dataclasses import dataclass
import enum


class Position(enum.Enum):
    QB = enum.auto()
    RB = enum.auto()
    WR = enum.auto()
    TE = enum.auto()
    D = enum.auto()
    K = enum.auto()
    FLEX = enum.auto()


@dataclass
class Player(BaseApi):
    """class that represents a single players' season stats"""

    player_id: str
    name: str
    roster: int
    points: float
    pos: Position
    rank: int
    par: float  # points above replacement
    paa: float  # points above average

    def __init__(self, player_id: str, meta: dict, stats: dict, roster: int = None) -> None:
        super().__init__()
        self.player_id = player_id
        self.roster = roster
        self.rank = stats["rank_ppr"]
        self.enum_pos(meta["position"])
        self.set_paa(None)
        self.set_par(None)

        # players with no points won't have this key, so we set it at 0
        # soemetimes a user will roster a player on ir so we should handle this case
        try:
            self.points = stats["pts_half_ppr"]
        except KeyError:
            self.points = 0

        # defenses have no full name, but we can just use their player id
        try:
            self.name = meta["full_name"]
        except KeyError:
            self.name = meta["player_id"]

    def set_par(self, par) -> None:
        self.par = par

    def set_paa(self, paa) -> None:
        self.paa = paa

    def enum_pos(self, pos: str):
        if pos == "QB":
            self.pos = Position.QB
        elif pos == "RB":
            self.pos = Position.RB
        elif pos == "WR":
            self.pos = Position.WR
        elif pos == "TE":
            self.pos = Position.TE
        elif pos == "DEF":
            self.pos = Position.D
        else:
            self.pos = Position.K

    def is_flex(self):
        return True if self.pos in [Position.RB, Position.WR, Position.TE] else False