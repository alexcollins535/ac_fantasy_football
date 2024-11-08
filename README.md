# AC Fantasy Football

ac_fantasy_football.ffl_data_importing is a Python library of functions used for importing NFL player statistics and Fantasy Football data from the Excel files in this package. Uses numpy and pandas.

ac_fantasy_football.ffl_main contains a functional script which when run, allows the user to output player statistical leaders, a graph of Fantasy Football owner power rankings, or Fantasy Football final standings projections.

## Usage

```python
import ac_fantasy_football.ffl_data_importing as fdi

# Modify this dictionary if making changes to file names
file_path_dict = fdi.file_path_dict

# Returns a DataFrame of Fantasy Football Player data from Weeks 1 and 2
player_data = fdi.import_full_team_data(['WK1', 'WK2'], file_path_dict)

# Refreshes player FFL owners column based on most recent owner mappings
player_data = fdi.refresh_OWNER(player_data, file_path_dict)

# Adds new STARTER and STARTPOS columns to player data (one row per player) 
# where starters (based on most fantasy points) have STARTER = True and 
# STARTPOS is their ranked position, like 'WR2' or 'FLEX'.
player_data = fdi.add_STARTER_and_STARTPOS(player_data)

# Returns only running backs from the player data DataFrame
fdi.slice_of_player_data(player_data, pos_input='RB')

```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.
