import statistics as stats
from dataclasses import dataclass
from base_api import BaseApi
from player import Player
from positions import Position


@dataclass
class Team(BaseApi):
    """class to represent a fantasy football team"""
    name: str
    roster_id: int
    user_id: int
    players: list
    division: int
    wins: int
    losses: int
    pf: int
    pa: int
    scoreboards: list

    # matchups are teams, scoreboards just the scores
    # matchups: dict
    # scoreboards: list
    
    def __init__(self, user_id: str, roster_id: int, name: str, week: int, players: list[Player], division: int, stats: tuple) -> None:
        super().__init__()

        # set all the dirct stuff from roster input
        self.name = name
        self.roster_id = roster_id
        self.user_id = user_id
        self.players = players
        for player in self.players:
            player.roster = self.roster_id
            
        self.division = division
        
        self.week = week
        self.wins = stats[0]
        self.simmed_wins = 0
        self.losses = stats[1]
        self.simmed_losses = 0
        self.pf = stats[2]
        self.simmed_pf = 0
        self.pa = stats[3]
        self.simmed_pa = 0
        
        # init an empty matchup dict and scoreboard list to hold future matchcups
        self.matchups = {}
        self.scoreboards = []
        self.simmed_weeks = []
        
    def get_record(self, points: bool = False) -> tuple:
        """gets the teams' record"""
        return (self.wins, self.losses, self.pf, self.pa) if points else (self.wins, self.losses)
    
    def build_scoreboards(self) -> None:
        """builds the scoreboards and matchups for this team vs. their weekly opponents"""
        for week in self.matchups:
            for matchup in self.matchups[week]:
                # check individually so we ensure position 0 is always the team that this class is representing
                if self.roster_id is matchup[0]["roster_id"]:
                    self.matchups[week] = matchup
                    self.scoreboards.append(
                        (matchup[0]["points"], matchup[1]["points"]))
                    continue
                elif self.roster_id is matchup[1]["roster_id"]:
                    self.matchups[week] = matchup
                    self.scoreboards.append(
                        (matchup[1]["points"], matchup[0]["points"]))
                    continue

    def summary_stats(self) -> None:
        """populates the summary statistics for this team"""
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

    def set_par_differentials(self, replacements: dict):
        """set the par value for this teams' rostered players"""
        for player in self.players:
            player.set_par(player.points - replacements[player.pos])
    
    def set_paa_differentials(self, replacements: dict):
        """set the paa value for this teams' starters"""
        c = [0,0,0,0,0,0,0]
        
        for player in self.starters:
            if not player: continue
            if player.pos is Position.QB and c[0] < 1:
                player.set_paa(player.points - replacements[player.pos])
                c[0] += 1
            elif player.pos is Position.RB and c[1] < 1:
                player.set_paa(player.points - replacements[player.pos][0])
                c[1] += 1
            elif player.pos is Position.RB and c[1] < 2:
                player.set_paa(player.points - replacements[player.pos][1])
                c[1] += 1
            elif player.pos is Position.WR and c[2] < 1:
                player.set_paa(player.points - replacements[player.pos][0])
                c[2] += 1
            elif player.pos is Position.WR and c[2] < 2:
                player.set_paa(player.points - replacements[player.pos][1])
                c[2] += 1
            elif player.pos is Position.TE and c[3] < 1:
                player.set_paa(player.points - replacements[player.pos])
                c[3] += 1
            elif player.pos is Position.RB and c[1] > 1 and c[4] < 1:
                player.set_paa(player.points - replacements[Position.FLEX][0])
                c[4] += 1
            elif player.pos is Position.RB and c[1] > 1 and c[4] < 2:
                player.set_paa(player.points - replacements[Position.FLEX][1])
                c[4] += 1
            elif player.pos is Position.WR and c[2] > 1 and c[4] < 1:
                player.set_paa(player.points - replacements[Position.FLEX][0])
                c[4] += 1
            elif player.pos is Position.WR and c[2] > 1 and c[4] < 2:
                player.set_paa(player.points - replacements[Position.FLEX][1])
                c[4] += 1
            elif player.pos is Position.TE and c[3] > 1 and c[4] < 1:
                player.set_paa(player.points - replacements[Position.FLEX][0])
                c[4] += 1
            elif player.pos is Position.TE and c[3] > 1 and c[4] < 2:
                player.set_paa(player.points - replacements[Position.FLEX][1])
                c[4] += 1
            elif player.pos is Position.DEF and c[5] < 1:
                player.set_paa(player.points - replacements[player.pos])
                c[4] += 1
            elif player.pos is Position.K and c[6] < 1:
                player.set_paa(player.points - replacements[player.pos])
                c[6] += 1
                
    def calculate_starters(self, positions) -> None:
        """calculates the expected starters for a team given current scoring"""
        players = sorted(self.players, key=lambda p: p.points, reverse=True)
        starters = [[],[],[],[],[],[],[]]
        
        for position in positions:
            if position is Position.QB:
                starters[0].append(None)
            elif position is Position.RB:
                starters[1].append(None)
            elif position is Position.WR:
                starters[2].append(None)
            elif position is Position.TE:
                starters[3].append(None)
            elif position is Position.FLEX:
                starters[4].append(None)
            elif position is Position.DEF:
                starters[5].append(None)
            else:
                starters[6].append(None)
                
        # this is long b/c we have to ensure we only set the starters
        # it's easiest conceptually if we just loop through the players by
        # highest point total and fill in our optimal lineup based on
        # player positions and how many we can start
        for player in players:
            if player.pos == Position.QB:
                if not starters[0][0]:
                    starters[0][0] = (player)
            elif player.pos == Position.RB:
                if not starters[1][0]:
                    starters[1][0] = player
                elif not starters[1][1]:
                    starters[1][1] = player
                elif not starters[4][0]:
                    starters[4][0] = player
                elif not starters[4][1]:
                    starters[4][1] = player
            elif player.pos == Position.WR:
                if not starters[2][0]:
                    starters[2][0] = player
                elif not starters[2][1]:
                    starters[2][1] = player
                elif not starters[4][0]:
                    starters[4][0] = player
                elif not starters[4][1]:
                    starters[4][1] = player
            elif player.pos == Position.TE:
                if not starters[3][0]:
                    starters[3][0] = (player)
                elif not starters[4][0]:
                    starters[4][0] = player
                elif not starters[4][1]:
                    starters[4][1] = player
            elif player.pos == Position.DEF:
                if not starters[5][0]:
                    starters[5][0] = (player)
            else:
                if not starters[6][0]:
                    starters[6][0] = (player)
        
        self.starters = [
            item for sublist in starters for item in sublist]          

    def points_scored(self) -> list:
        """returns a list of points scored for played weeks"""
        return [self.scoreboards[i][0] for i in range(self.week)]
    
    def build_distribution(self, update: bool) -> list:
        """returns the mean and standard deviation of this teams' points scored
        plus a predicted score to update the distribution on prediction
        """
        scores = self.points_scored()
        if update:
            scores += self.simmed_weeks
        
        self.distribution = (stats.mean(scores), stats.stdev(scores))
        return self.distribution
    
    def predict_score(self, dist_func) -> float:
        """predicts the score based off the teams' score distribution"""
        predicted = dist_func(
            loc=self.distribution[0], scale=self.distribution[1])
        self.simmed_weeks.append(predicted)
        return predicted
        
def main() -> None:
    pass


if __name__ == "__main__":
    main()
