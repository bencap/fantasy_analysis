import statistics as stats
import numpy as np
from dataclasses import dataclass
from base_api import BaseApi
from positions import Position
from team import Team
from players import Players

@dataclass
class League(BaseApi):
    """class to represent a fantasy football league"""
    week: int
    regular_season_weeks: int
    league_id: str
    starting_positions: list[Position]
    roster_pairings: dict
    name_pairings: dict
    matchups: dict
    medians: list[int]
    teams: dict
    standings: list[Team]
    divisions: list[list[Team]]

    def __init__(self, weeks_elapsed: int, league_id: str, players: Players) -> None:
        super().__init__()

        self.week = weeks_elapsed
        self.league_id = league_id
        self._base_url = "https://api.sleeper.app/v1/league/{}".format(
            self.league_id)

        # get raw api calls for needed league info
        self._league = self._call(self._base_url)
        self.set_league_settings()
        self._rosters = self._call("{}/{}".format(self._base_url, "rosters"))
        self._players = players.all_players
        self._users = self._call("{}/{}".format(self._base_url, "users"))

        # pair users, rosters, and team names
        self.pair_user_rosters(self._rosters)
        self.pair_user_names(self._users)

        # build team skeletons
        self.standings = []
        self.rostered_players = []
        self.teams = {}
        self.build_league()
        
        # build team matchup data and set team objects to have this matchup data
        self.build_matchups()
        
        # build player additional stats
        players.build_waivers(self.get_rosters())
        players.calculate_average_averages()
        players.calculate_replacement_averages()
        
        for team in self.standings:
            team.set_par_differentials(players.replacement_averages)
            team.set_paa_differentials(players.average_averages)
            team.summary_stats()

    def set_league_settings(self) -> None:
        self.positions = self._league["roster_positions"]
        self.starting_positions = [Position[position]
                                   for position in self.positions if position != "BN"]
        self.regular_season_weeks = self._league["settings"]["playoff_week_start"] - 1
        self.divisions = [[]
                          for i in range(self._league["settings"]["divisions"])]

    def pair_user_rosters(self, rosters: dict) -> None:
        """pairs a users' roster id with their user id"""
        self.roster_pairings = {roster["roster_id"]                                : roster["owner_id"] for roster in rosters}

    def pair_user_names(self, users: dict) -> None:
        """pairs a users' user id with their team name"""
        pairings = {}

        # this is stored dumb, but basically team name can be in metadata or it can
        # be outside of it. If a team has no name, we can just use their display name
        for user in users:
            try:
                pairings[user["user_id"]] = user["metadata"]["team_name"]
            except KeyError:  # stored dumb
                try:
                    pairings[user["user_id"]] = user["team_name"]
                except KeyError:  # no team name
                    pairings[user["user_id"]] = user["display_name"]

        self.name_pairings = pairings

    def build_league(self):
        for roster in self._rosters:
            # build players on roster and set them to the roster id, then add it to the league rosters
            players = [self._players[player_id] for player_id in roster["players"]]
            for player in players:
                player.roster = roster["roster_id"]
            self.rostered_players += players

            team = Team(roster["owner_id"],
                        roster["roster_id"],
                        self.name_pairings[roster["owner_id"]],
                        self.week,
                        players,
                        roster["settings"]["division"],
                        (roster["settings"]["wins"],
                         roster["settings"]["losses"],
                         roster["settings"]["fpts"],
                         roster["settings"]["fpts_against"])
                        )
            team.calculate_starters(self.starting_positions)

            self.standings.append(team)
            self.teams[team.roster_id] = team
            self.divisions[team.division-1].append(team)

        self.standings = sorted(self.standings, key=lambda t: (
            t.wins, t.losses, t.pf, t.pa), reverse=True)
        
        for division in self.divisions:
            division = sorted(division, key=lambda t: (
                t.wins, t.losses, t.pf, t.pa), reverse=True)

    def build_matchups(self) -> None:
        """builds the league matchups for all weeks and computes weekly median"""
        matchups = []
        medians = []

        for week in range(1, self.regular_season_weeks + 1):
            games = self._call(
                "{}/{}/{}".format(self._base_url, "matchups", week))

            # weekly matchups are a two element list with both opponents
            pairings = [[] for i in range(len(self.teams) // 2)]
            points = []
            for pairing in games:
                pairings[pairing["matchup_id"]-1].append(pairing)
                points.append(pairing["points"])
            
            for pairing in pairings:
                self.teams[pairing[0]["roster_id"]].matchups[week] = pairings
                self.teams[pairing[1]["roster_id"]].matchups[week] = pairings
                
            matchups.append(pairings)
            medians.append(stats.median(points))

        self.matchups = {week: matchups[week]
                         for week in range(1, self.regular_season_weeks)}
        self.medians = medians
        
        for team in self.standings:
            team.build_scoreboards()

    def get_matchups(self, thru: int = None) -> dict:
        """returns the league matchups through a given week"""
        if not thru:
            thru = self.week

        return {week: self.matchups[week] for week in range(1, thru+1)}

    def get_team_matchups(self, roster_id: int, thru: int = None) -> dict:
        """returns the league matchups through a given week for a team"""
        if not thru:
            thru = self.week
            
        return {w: self.teams[roster_id].matchups[w] for w in range(1, thru+1)}

    def get_rosters(self, desired: int = None) -> list:
        """returns the league rosters sans nicknames, or a specific roster if requested"""
        rosters = []
        if desired:
            return self.teams[desired].players
        else:
            for team in self.standings:
                rosters += team.players

        return rosters

    def get_points(self, team: int = None) -> list:
        """gets all points scored by a team if desired, or the league if none"""
        points = []
        if team:
            return self.teams[team].points_scored()
        else:
            for team in self.standings:
                points += team.points_scored()
            return points

    def get_names_for_plotting(self) -> list[str]:
        """returns a list of team names for plotting"""
        return [team.name for team in self.standings]
    
    def build_team_point_models(self) -> None:
        """builds the point distributions for each team"""
        for team in self.standings:
            
            # reset any prior simulations
            team.simmed_weeks = []
            team.simmed_wins = 0
            team.simmed_pf = 0
            team.simmed_losses = 0
            team.simmed_pa = 0
            
            team.build_distribution(update=False)
    
    def sim_remaining_season(self, distribution) -> None:
        """sim the remainder of the season for teams in the league"""
        
        # reset any previous simulations
        self.build_team_point_models()
            
        # predict scores for each of the remaining weeks for each team
        simmed_medians = []
        for remaining_week in range(self.regular_season_weeks - self.week):
            for team in self.standings:
                team.predict_score(distribution)
                team.build_distribution(update=True)
                
            simmed_medians.append(stats.median([team.simmed_weeks[remaining_week] for team in self.standings]))
        
        # calculate simmed wins and losses
        for remaining_week in range(self.regular_season_weeks - self.week):
            for team in self.standings:
                if team.simmed_weeks[remaining_week] < simmed_medians[remaining_week]:
                    team.simmed_losses += 1
                else:
                    team.simmed_wins += 1

                matchup = team.matchups[remaining_week + self.week]
                opponent = matchup[0]["roster_id"] if matchup[0]["roster_id"] != team.roster_id else matchup[1]["roster_id"]
                
                simmed_week = (team.simmed_weeks[remaining_week], self.teams[opponent].simmed_weeks[remaining_week])
                team.scoreboards[remaining_week + self.week] = simmed_week
                team.simmed_pf += simmed_week[0]
                team.simmed_pa += simmed_week[1]
                
                if simmed_week[0] < simmed_week[1]:
                    team.simmed_losses += 1
                else:
                    team.simmed_wins += 1
            
    def simmed_results(self) -> list[list[Team]]:
        """returns the standings in the two divisions when taking simmed results into account"""
        simmed_standings = []
        for division in self.divisions:
            division = sorted(division, 
                              key=lambda t: (t.wins + t.simmed_wins, t.losses + t.simmed_losses, t.pf + t.simmed_pf, t.pa + t.simmed_pf), 
                              reverse=True)
            
            simmed_standings.append([(t.wins+t.simmed_wins, t.losses + t.simmed_losses, t.pf + t.simmed_pf, t.pa + t.simmed_pa, t.roster_id) for t in division])
         
        return simmed_standings
        
def main() -> None:
    players = Players()
    our_league = League(11, "649912836461539328", players)
    our_league.sim_remaining_season(np.random.normal)
    results = our_league.simmed_results()

if __name__ == "__main__":
    main()
