import statistics as stats
from dataclasses import dataclass
from base_api import BaseApi
from league import League
from players import Players
from player import Player, Position


@dataclass
class Team(BaseApi):
    """class to represent a fantasy football team"""
    name: str
    roster_id: int
    user_id: int
    players: list
    expected_starters: list
    wins: int
    losses: int
    points_for: int
    points_against: int

    # matchups show all metadata, scoreboards just the scores
    matchups: dict
    scoreboards: list

    # summary stats for team point scoring
    week: int
    weekly_pf: list
    weekly_pa: list
    weekly_margin: list
    avg_pf: float
    avg_pa: float
    med_pf: float
    med_pa: float
    msvm: float  # mean squared victory margin
    ma_3: list  # 3 game moving avg
    ma_5: list  # 5 game moving avg

    def __init__(self, name: str, roster: dict, games: dict, players: Players) -> None:
        super().__init__()

        # set all the dirct stuff from roster input
        self.name = name
        self.roster_id = roster["roster_id"]
        self.user_id = roster["owner_id"]
        self.players = [players.all_players[player_id]
                        for player_id in roster["players"]]
        self.wins = roster["settings"]["wins"]
        self.losses = roster["settings"]["losses"]
        self.points_for = roster["settings"]["fpts"]
        self.points_against = roster["settings"]["fpts_against"]

        # _games is all games played in the league
        self._games = games
        self.scoreboards = []
        self.matchups = {}
        self.build_scoreboards()

        self.summary_stats()

    def build_scoreboards(self) -> None:
        """builds the scoreboards and matchups for this team vs. their weekly opponents"""
        for week in self._games:
            for matchup in self._games[week]:
                # check individually so we ensure position 0 is always the team that this class is representing
                if self.roster_id == matchup[0]["roster_id"]:
                    self.matchups[week] = matchup
                    self.scoreboards.append(
                        (matchup[0]["points"], matchup[1]["points"]))
                    continue
                elif self.roster_id == matchup[1]["roster_id"]:
                    self.matchups[week] = matchup
                    self.scoreboards.append(
                        (matchup[1]["points"], matchup[0]["points"]))
                    continue

    def summary_stats(self) -> None:
        """populates the summary statistics for this team"""
        self.week = len(self.scoreboards)

        # the really basic stuff
        self.weekly_pf = [score[0] for score in self.scoreboards]
        self.weekly_pa = [score[1] for score in self.scoreboards]
        self.weekly_margin = [item[0] - item[1]
                              for item in zip(self.weekly_pf, self.weekly_pa)]
        self.avg_pf = stats.mean(self.weekly_pf)
        self.avg_pa = stats.mean(self.weekly_pa)
        self.med_pf = stats.median(self.weekly_pf)
        self.med_pa = stats.median(self.weekly_pa)

        # mean squared victory margin atempts to quantify
        # the degree to which a team plays in blowouts or close games
        self.msvm = sum(
            [margin ** 2 for margin in self.weekly_margin]) / len(self.weekly_margin)

        # 3 and 5 week moving averages
        self.ma_3 = []
        self.ma_5 = []
        for i in range(self.week):
            if i < 3:
                self.ma_3.append(sum(self.weekly_pf[0:i+1])/(i+1))
                self.ma_5.append(sum(self.weekly_pf[0:i+1])/(i+1))
            elif i < 5:
                self.ma_3.append(sum(self.weekly_pf[i-2:i+1])/3)
                self.ma_5.append(sum(self.weekly_pf[0:i+1])/(i+1))
            else:
                self.ma_3.append(sum(self.weekly_pf[i-2:i+1])/3)
                self.ma_5.append(sum(self.weekly_pf[i-4:i+1])/5)

    def set_par_differentials(self):
        """set the par value for this teams' rostered players"""
        for player in self.players:
            player.set_par(player.points -
                           self.replacement_averages[player.pos])

    def set_par_averages(self, par_averages: dict) -> None:
        self.replacement_averages = par_averages

    def set_paa_differentials(self) -> None:
        """set the paa value for every rostered player"""
        players = sorted(self.players, key=lambda p: p.points, reverse=True)
        starters = [[None], [None, None], [None, None],
                    [None], [None, None], [None], [None]]

        # this is long b/c we have to ensure we only set the starters
        # it's easiest conceptually if we just loop through the players by
        # highest point total and fill in our optimal lineup based on
        # player positions and how many we can start
        for player in players:
            if player.pos == Position.QB:
                if not starters[0]:
                    starters[0] = (player)
                    player.set_paa(player.points -
                                   self.average_averages[player.pos])
            elif player.pos == Position.RB:
                if not starters[1][0]:
                    starters[1][0] = player
                    player.set_paa(player.points -
                                   self.average_averages[player.pos][0])
                elif not starters[1][1]:
                    starters[1][1] = player
                    player.set_paa(player.points -
                                   self.average_averages[player.pos][1])
                elif not starters[4][0]:
                    starters[4][0] = player
                    player.set_paa(player.points -
                                   self.average_averages[Position.FLEX][0])
                elif not starters[4][1]:
                    starters[4][1] = player
                    player.set_paa(player.points -
                                   self.average_averages[Position.FLEX][1])
            elif player.pos == Position.WR:
                if not starters[2][0]:
                    starters[2][0] = player
                    player.set_paa(player.points -
                                   self.average_averages[player.pos][0])
                elif not starters[2][1]:
                    starters[2][1] = player
                    player.set_paa(player.points -
                                   self.average_averages[player.pos][1])
                elif not starters[4][0]:
                    starters[4][0] = player
                    player.set_paa(player.points -
                                   self.average_averages[Position.FLEX][0])
                elif not starters[4][1]:
                    starters[4][1] = player
                    player.set_paa(player.points -
                                   self.average_averages[Position.FLEX][1])
            elif player.pos == Position.TE:
                if not starters[3]:
                    starters[3] = (player)
                    player.set_paa(player.points -
                                   self.average_averages[player.pos])
                elif not starters[4][0]:
                    starters[4][0] = player
                    player.set_paa(player.points -
                                   self.average_averages[Position.FLEX][0])
                elif not starters[4][1]:
                    starters[4][1] = player
                    player.set_paa(player.points -
                                   self.average_averages[Position.FLEX][1])
            elif player.pos == Position.D:
                if not starters[5]:
                    starters[5] = (player)
                    player.set_paa(player.points -
                                   self.average_averages[player.pos])
            else:
                if not starters[6]:
                    starters[6] = (player)
                    player.set_paa(player.points -
                                   self.average_averages[player.pos])

        self.expected_starters = [
            item for sublist in starters for item in sublist]

    def set_paa_averages(self, paa_averages: dict) -> None:
        self.average_averages = paa_averages


def main() -> None:
    our_league = League(10, "649912836461539328")
    players = Players(our_league)

    team = our_league.get_rosters()[0]

    ben = Team(
        our_league.name_pairings[team["owner_id"]], team, our_league.matchups, players)

    ben.set_paa_averages(players.average_averages)
    ben.set_par_averages(players.replacement_averages)
    ben.set_par_differentials()
    ben.set_paa_differentials()

    print(ben)


if __name__ == "__main__":
    main()
