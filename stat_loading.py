import requests
import json
from sleeper_wrapper import Players

sleeper_players = Players()
PLAYER_ROUTE = "https://api.sleeper.app/stats/nfl/player/"
players = sleeper_players.get_all_players()

player_stats = {}

for num, player in enumerate(players):
    if num % 500 == 0:
        print(f"Done with player {num} out of {len(players.keys())}")

    # make this slightly quicker by eliminating defensive player API calls
    player_pos = players[player]["position"]
    if player_pos not in ["QB", "RB", "WR", "TE", "DEF", "K"]:
        continue

    response = requests.get(url=PLAYER_ROUTE+player, params={"season_type": "regular", "season": "2021", "grouping": "season"})
    # None type responses are players without stats
    if response.json():
        player_stats[player] = response.json()["stats"]

with open('player_stats.json', 'w') as fp:
    json.dump(player_stats, fp)