from typing import Type
from base_api import BaseApi
from league import League
from player import Player, Position
import json


class Players(BaseApi):
    """class for all player data and global player stats"""
    FANTASY_POSITIONS = ["QB", "RB", "WR", "TE", "FLEX", "DEF", "K"]
    REPLACEMENT_CUT = 10
    YEAR = "2021"

    def __init__(self, league: League, local=True, fp='player_stats.json', offense_only=True) -> None:
        super().__init__()
        self.fp = fp
        self._get_all_players(offense_only=offense_only)
        self.players_stats = {}
        self.read(self.fp) if local else self._update()
        self._rosters = league.get_rosters()

        # build the three player categories
        self.all_players = {}
        self.rostered_players = []
        self.waiver_players = []
        self.build_players()

        # build replacement and average players for use by team class
        self.replacement_averages = {}
        self.average_averages = {}
        self.calculate_replacement_averages()
        self.calculate_average_averages()

    def _update(self) -> None:
        """updates all player data from sleeper api (slow)"""
        for num, player_id in enumerate(self.players_meta):
            print(player_id)
            if num % 500 == 0:
                print(
                    f"Done with player {num} out of {len(self.players_meta.keys())}")

            player = self._call(url="https://api.sleeper.app/stats/nfl/player/{}".format(player_id),
                                params={"season_type": "regular", "season": self.YEAR, "grouping": "season"})

            # None type responses are players without stats
            if player:
                self.players_stats[player_id] = player["stats"]

        self.write(self.fp)

    def _get_all_players(self, offense_only: bool) -> None:
        """gets all player metadata (fast)"""
        player_meta = self._call("https://api.sleeper.app/v1/players/nfl")

        # make future updates slightly quicker by eliminating defensive players from this dictionary
        if offense_only:
            self.players_meta = {
                player: player_meta[player] for player in player_meta if player_meta[player]["position"] in self.FANTASY_POSITIONS}
        else:
            self.players_meta = player_meta

    def build_players(self) -> None:
        """builds rostered and unrostered player objects based on league rosters"""
        rostered = {}
        for roster in self._rosters:
            curr_roster = {player_id: roster["roster_id"]
                           for player_id in roster["players"]}
            rostered = {**rostered, **curr_roster}

        # if a player is rostered we set the players' roster field and add them to the rostered list, otherwise we add them to waivers
        for player_id in self.players_stats:

            if player_id in rostered.keys():
                self.rostered_players.append(
                    Player(player_id,  self.players_meta[player_id], self.players_stats[player_id], roster=rostered[player_id]))
                self.all_players[player_id] = Player(
                    player_id,  self.players_meta[player_id], self.players_stats[player_id], roster=rostered[player_id])

            else:
                self.all_players[player_id] = Player(
                    player_id,  self.players_meta[player_id], self.players_stats[player_id])
                self.waiver_players.append(
                    Player(player_id,  self.players_meta[player_id], self.players_stats[player_id]))

    def calculate_replacement_averages(self) -> None:
        """calculates the expected points scored for replacement players"""
        for position in Position:
            if position == Position.FLEX:
                replacements = [
                    player.points for player in self.waiver_players if player.is_flex()]
            else:
                replacements = [
                    player.points for player in self.waiver_players if player.pos == position]

            replacements.sort(reverse=True)
            self.replacement_averages[position] = sum(
                replacements[0:self.REPLACEMENT_CUT]) / self.REPLACEMENT_CUT

    def calculate_average_averages(self) -> None:
        """calculates the expected points among rostered player for position groups"""
        for position in Position:
            if position == Position.QB or position == Position.TE or position == Position.K or position == Position.D:
                top_rostered = [
                    player.points for player in self.rostered_players if player.pos == position]
            elif position == Position.RB or position == Position.WR:
                top_rostered = [
                    player.points for player in self.rostered_players if player.pos == position]
            else:
                top_rostered = []
                for flex in [Position.WR, Position.RB, Position.TE]:
                    top_flex = [
                        player.points for player in self.rostered_players if player.pos == flex]
                    top_flex.sort(reverse=True)
                    top_rostered += top_flex[20:]

            top_rostered.sort(reverse=True)
            self.average_averages[position] = sum(
                top_rostered[0:10]) / 10

            # handle the position groups with two starters
            if position == position.RB or position == position.WR or position == position.FLEX:
                self.average_averages[position] = (
                    sum(top_rostered[0:10]) / 10, sum(top_rostered[10:20]) / 10)

    def write(self, fp: str) -> None:
        """writes player data to a json file"""
        with open(fp, 'w') as fp:
            json.dump(self.players_stats, fp)

    def read(self, fp: str) -> None:
        """reads player data from a json file"""
        with open(fp) as file:
            self.players_stats = json.load(file)


def main():
    our_league = League(10, "649912836461539328")
    players = Players(our_league)
    
    # for updating the league stats
    #players = Players(our_league, local=False)
    print(players.rostered_players)


if __name__ == "__main__":
    main()
