from base_api import BaseApi
from player import Player
from positions import Position
import json


class Players(BaseApi):
    """class for all player data and global player stats"""
    FANTASY_POSITIONS = ["QB", "RB", "WR", "TE", "FLEX", "DEF", "K"]
    REPLACEMENT_CUT = 10
    YEAR = "2021"

    def __init__(self, local=True, fp='player_stats.json', offense_only=True) -> None:
        super().__init__()
        self.fp = fp
        self._get_all_players(offense_only=offense_only)
        self.players_stats = {}
        self.read(self.fp) if local else self._update()

        # build the three player categories
        self.all_players = {}
        self.build_players()
        
        self.average_averages = {}
        self.replacement_averages = {}

    def _update(self) -> None:
        """updates all player data from sleeper api (slow)"""
        for num, player_id in enumerate(self.players_meta):
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
        """builds all player objects in the player universe"""
        for player_id in self.players_stats:
            self.all_players[player_id] = Player(
                player_id,  self.players_meta[player_id], self.players_stats[player_id])

    def build_waivers(self, rostered_players: list[Player]) -> None:
        """builds unrostered/rostered players based off roster list"""
        self.rostered_players = rostered_players
        self.waiver_players = [self.all_players[player_id] for player_id in self.all_players if self.all_players[player_id] not in self.rostered_players]

    def calculate_replacement_averages(self) -> None:
        """calculates the expected points scored for replacement players"""
        for position in Position:
            if position is Position.FLEX:
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
            if position is not Position.FLEX:
                top_rostered = [
                    player.points for player in self.rostered_players if player.pos is position]
            else:
                top_rostered = []
                for flex in [Position.WR, Position.RB, Position.TE]:
                    top_flex = [
                        player.points for player in self.rostered_players if player.pos is flex]
                    top_flex.sort(reverse=True)
                    top_rostered += top_flex[20:]

            top_rostered.sort(reverse=True)
            self.average_averages[position] = sum(
                top_rostered[0:10]) / 10

            # handle the position groups with two starters
            if position is position.RB or position is position.WR or position is position.FLEX:
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
    players = Players()
    print(players.all_players)


if __name__ == "__main__":
    main()
