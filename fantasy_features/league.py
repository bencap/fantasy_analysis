import statistics as stats
from dataclasses import dataclass
from base_api import BaseApi


@dataclass
class League(BaseApi):
    """class to represent a fantasy football league"""
    week: int
    league_id: str
    roster_pairings: dict
    name_pairings: dict
    matchups: dict
    medians: list
    standings: list
    division_1: list
    division_2: list

    def __init__(self, weeks_elapsed: int, league_id: str) -> None:
        super().__init__()

        self.week = weeks_elapsed
        self.league_id = league_id
        self._base_url = "https://api.sleeper.app/v1/league/{}".format(
            self.league_id)

        # get raw api calls for needed league info
        self._league = self._call(self._base_url)
        self._rosters = self._call("{}/{}".format(self._base_url, "rosters"))
        self._users = self._call("{}/{}".format(self._base_url, "users"))

        # clean raw data into useable format
        self.pair_user_rosters(self._rosters)
        self.pair_user_names(self._users)
        self.build_matchups()
        self.build_standings()

    def pair_user_rosters(self, rosters: dict) -> None:
        """pairs a users' roster id with their user id"""
        self.roster_pairings = {roster["roster_id"]: roster["owner_id"] for roster in rosters}

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

    def build_matchups(self) -> None:
        """builds the league matchups for all weeks up to current and computes weekly median"""
        matchups = {}
        medians = []

        for week in range(1, self.week+1):
            games = self._call(
                "{}/{}/{}".format(self._base_url, "matchups", week))

            # weekly matchups are a two element list with both opponents
            pairings = [[], [], [], [], []]
            points = []
            for pairing in games:
                pairings[pairing["matchup_id"]-1].append(pairing)
                points.append(pairing["points"])

            matchups[week] = pairings
            medians.append(stats.median(points))

        self.matchups = matchups
        self.medians = medians

    def build_standings(self) -> None:
        """builds the overall and divisional standings for the league"""

        standings = [(p["settings"]["wins"], p["settings"]["losses"], p["settings"]
                      ["fpts"], p["roster_id"], p["settings"]["division"]) for p in self._rosters]

        self.standings = [(item[0], item[1], item[2], item[3])
                          for item in standings]
        self.division_1 = [(item[0], item[1], item[2], item[3])
                           for item in standings if item[4] == 1]
        self.division_2 = [(item[0], item[1], item[2], item[3])
                           for item in standings if item[4] == 2]

        self.standings.sort(reverse=True)
        self.division_1.sort(reverse=True)
        self.division_2.sort(reverse=True)

    def get_rosters(self) -> list:
        """returns the league rosters sans nicknames"""
        rosters = []
        for roster in self._rosters:
            temp = roster.copy()
            temp.pop("metadata", None)
            rosters.append(temp)

        return rosters


def main() -> None:
    our_league = League(10, "649912836461539328")
    print(our_league.medians)
    print(our_league.name_pairings)
    print(our_league.roster_pairings)
    print(our_league.standings)
    print(our_league.division_1)


if __name__ == "__main__":
    main()
