# fantasy_analysis

Using the Sleeper API to analyze our leagues' results. You can view an interactive version of these notebooks on the web on [Binder](https://mybinder.org/). Simply add the repository information after following the link and launch the server. Most weeks I dive into a specific aspect of the week and try to analyze our fantasy league in a way that is deeper than the summary statistics provided on the league homepage.

To run these notebooks on your personal machine, first clone the repository into a directory of your choice. Then run 
```
pip install requierements.txt
```
to install the required dependencies. After these are installed, run
```
python3 stat_loading.py
```
to load the player statistics for each player in the fantasy football universe. I include a copy of this file in the repository, but depending on when this repo was last updated you may want to get the most up to date player stats. Note that the public Sleeper stats API is limited in that a new call is required to get each players' stats, so be conscious that this command may take a while. Periodic updates are outputted to the command line. Once player stats are loaded into a local JSON file, run
```
jupyter notebook
```
to initialize the local notebook server and run/view the files.
