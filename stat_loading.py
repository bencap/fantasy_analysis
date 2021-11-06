import requests
import json
from sleeper_wrapper import Players

sleeper_players = Players()
PLAYER_ROUTE = "https://api.sleeper.app/stats/nfl/player/"
players = sleeper_players.get_all_players()

player_stats = {}

for num, player in enumerate(players):
    response = requests.get(url=PLAYER_ROUTE+player, params={"season_type": "regular", "season": "2021", "grouping": "season"})
    if response.json():
        player_stats[player] = response.json()["stats"]
    if num % 500 == 0:
        print(f"Done with player {num} out of  {len(players.keys())}")

with open('player_stats.json', 'w') as fp:
    player_stats = json.dumps('player_stats.json', fp)
