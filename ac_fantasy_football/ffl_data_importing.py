import pandas as pd
import numpy as np

# Standard Globals
valid_sheet_names = ['WK1', 'WK2', 'WK3', 'WK4', 'WK5', 'WK6', 'WK7', 'WK8']  # Update this as changes are made to source spreadsheet
all_sheet_names = ['WK1', 'WK2', 'WK3', 'WK4', 'WK5', 'WK6', 'WK7', 'WK8', 'WK9', 'WK10', 'WK11', 'WK12', 'WK13', 'WK14', 'WK15', 'WK16', 'WK17']
positions = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']
inj_status = ['Q', 'D', 'O', 'IR']
teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET', 'GB', 'HOU', 'IND', 'JAC', 'KC',
         'LAC', 'LAR', 'LV', 'MIA', 'MIN', 'NE', 'NO', 'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS', 'FA', '--', '*BYE*']
na_val = '--'
filler_value = '*--*'
standard_columns = ['PLAYER', 'POS', 'TEAM', 'OPPONENT', 'WEEK', 'FPTS']
basic_stats = {'QB': ['PAYDS', 'PATD', 'INT', 'CAR', 'RUYDS', 'RUTD', 'FUML'],
             'RB': ['CAR', 'RUYDS', 'RUTD', 'REC', 'REYDS', 'RETD', 'FUML'],
             'WR': ['CAR', 'RUYDS', 'RUTD', 'REC', 'REYDS', 'RETD', 'FUML'],
             'TE': ['REC', 'REYDS', 'RETD', 'FUML', 'FPTS'],
             'FLEX': ['CAR', 'RUYDS', 'RUTD', 'REC', 'REYDS', 'RETD', 'FUML'],
             'ALL': ['PAYDS', 'PATD', 'INT', 'CAR', 'RUYDS', 'RUTD', 'REC', 'REYDS', 'RETD', 'FUML']}
future_weeks = all_sheet_names[len(valid_sheet_names):]

# File Paths
file_path_dict = {'player_data_by_week': 'ac_fantasy_football\\player_data_by_week.xlsx',
                  'kicker_data_by_week': 'ac_fantasy_football\\kicker_data_by_week.xlsx',
                  'defense_data_by_week': 'ac_fantasy_football\\defense_data_by_week.xlsx',
                  'utilization_data': 'ac_fantasy_football\\utilization_data.xlsx',
                  'players_out_by_week': 'ac_fantasy_football\\players_out_by_week.xlsx',
                  'ref_for_manual_corrections': 'ac_fantasy_football\\ref_for_manual_corrections.xlsx',
                  'nfl_schedule_2024': 'ac_fantasy_football\\nfl_schedule_2024.xlsx',
                  'current_league_info': 'ac_fantasy_football\\current_league_info.xlsx'
}



# Importing player data with basic stats
def import_player_data(selected_weeks, file_path_dict, w_dnp_info=True):
    ''' 
    Import offensive player data from Excel for the weeks in the selected_weeks. 
    Input should be a string or list, like 'WK1', ['WK1', 'WK2'], or 'all_valid' to select all valid weeks.
    w_dnp_info adds rows for players out or on bye.
    Returns a dataframe with player data. 
    
    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        w_dnp_info (bool, optional): include rows for players out or on bye.

    Returns:
        pd.DataFrame: offensive player data
    
    '''
    # Static values
    players_cols = [0,1,2,3,4,5]
    stats_cols = [7,8,9,10,11,12,13,14,15,16,17,18,19,20,21]
    column_labels = ['C/A', 'PAYDS', 'PATD', 'INT', 'CAR', 'RUYDS', 'RUTD', 'REC', 'REYDS', 'RETD', 'TAR', '2PC', 'FUML', 'MISCTD', 'FPTS']

    # Initialize summary
    player_stats_summary = pd.DataFrame()
    selected_weeks = convert_selected_weeks_input(selected_weeks)
    validate_selected_weeks(selected_weeks)
    
    for sheet in selected_weeks:
        # Import from Excel
        players = import_player_data_from_file(file_path_dict['player_data_by_week'], sheet, players_cols)
        stats = import_stats_data_from_file(file_path_dict['player_data_by_week'], sheet, stats_cols, column_labels)
        # Combine player and stats to one table
        players_stats = pd.concat([players, stats], axis=1)
        # Add column for week
        players_stats['WEEK'] = sheet
        # Append data to summary df
        player_stats_summary = pd.concat([player_stats_summary, players_stats], ignore_index=True)

    player_stats_summary['TEAM'] = convert_team_ini_to_standard(player_stats_summary['TEAM'])
    player_stats_summary['OPPONENT'] = convert_team_ini_to_standard(player_stats_summary['OPPONENT'])
    player_stats_summary = add_OUT_and_BYE(player_stats_summary, stat_to_check='CAR', stat_val_to_check='--')
    if w_dnp_info:
        player_stats_summary = add_dnp_players(player_stats_summary, selected_weeks, file_path_dict)

    player_stats_summary = player_stats_summary.reset_index(drop=True)
    return player_stats_summary
def import_kicker_data(selected_weeks, file_path_dict):
    '''
    Import kicker data from Excel. Excludes data for bye weeks. Returns dataframe.
    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values

    Returns:
        pd.DataFrame: kicker data
    '''
    
    players_cols = [0,1,2,3,4,5]
    stats_cols = [7,8,9,10,11,12]
    column_labels = ['FG39/FGA39', 'FG49/FGA49', 'FG50+/FGA50+', 'FG/FGA', 'XP/XPA', 'FPTS']
    
    # Initialize summary
    player_stats_summary = pd.DataFrame()
    selected_weeks = convert_selected_weeks_input(selected_weeks)
    validate_selected_weeks(selected_weeks)
    for sheet in selected_weeks:
        # Import from Excel
        players = import_player_data_from_file(file_path_dict['kicker_data_by_week'], sheet, players_cols)
        stats = import_stats_data_from_file(file_path_dict['kicker_data_by_week'], sheet, stats_cols, column_labels, type='Kicker')
        # Combine player and stats to one table
        players_stats = pd.concat([players, stats], axis=1)
        # Add column for week
        players_stats['WEEK'] = sheet
        # Append data to summary df
        player_stats_summary = pd.concat([player_stats_summary, players_stats], ignore_index=True)

    player_stats_summary['TEAM'] = convert_team_ini_to_standard(player_stats_summary['TEAM'])
    player_stats_summary['OPPONENT'] = convert_team_ini_to_standard(player_stats_summary['OPPONENT'])
    player_stats_summary = add_OUT_and_BYE(player_stats_summary, stat_to_check='FG/FGA', stat_val_to_check='--/--')

    for index, row in player_stats_summary.iterrows():
        if row['OUT'] | row['BYE']:
            continue
        #print(row['PLAYER'], " ", row['WEEK'])
        xptm = (row['XP/XPA'].split('/'))[0]
        fg50 = (row['FG50+/FGA50+'].split('/'))[0]
        fg40 = (row['FG49/FGA49'].split('/'))[0]
        fg0 = int((row['FG/FGA'].split('/'))[0]) - int(fg50) - int(fg40)
        fgm = int((row['FG/FGA'].split('/'))[1]) - int((row['FG/FGA'].split('/'))[0])

        player_stats_summary.loc[index, 'XPTM'] = xptm
        player_stats_summary.loc[index, 'FG50'] = fg50
        player_stats_summary.loc[index, 'FG40'] = fg40
        player_stats_summary.loc[index, 'FG0'] = fg0
        player_stats_summary.loc[index, 'FGM'] = fgm
    
    return player_stats_summary
def import_defense_data(selected_weeks, file_path_dict, def_scoring_ranges=False):
    '''
    Import defense data from Excel. Excludes data for bye weeks. Returns dataframe.
    
    Args:
    
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        def_scoring_ranges (dict or bool, optional): dictionary of defense points against and yards against scoring rules like {'PA0': 5, 'PA1': 4, 'PA7': 3 ... 'YA100': 5 ...}

    Returns:
        pd.DataFrame: team defense data
    '''
    global na_val

    players_cols = [0,1,2,3,4,5]
    stats_cols = [7,8,9,10,11,12,13,14,15]
    column_labels = ['DEFTD', 'DEFINT', 'FR', 'SCK', 'SFTY', 'BLK', 'PA', 'YA', 'FPTS']
    
    # Initialize summary
    player_stats_summary = pd.DataFrame()
    selected_weeks = convert_selected_weeks_input(selected_weeks)
    validate_selected_weeks(selected_weeks)
    for sheet in selected_weeks:
        # Import from Excel
        players = import_player_data_from_file(file_path_dict['defense_data_by_week'], sheet, players_cols)
        stats = import_stats_data_from_file(file_path_dict['defense_data_by_week'], sheet, stats_cols, column_labels, type='Defense')
        # Combine player and stats to one table
        players_stats = pd.concat([players, stats], axis=1)
        # Add column for week
        players_stats['WEEK'] = sheet
        # Append data to summary df
        player_stats_summary = pd.concat([player_stats_summary, players_stats], ignore_index=True)

    player_stats_summary['TEAM'] = convert_team_ini_to_standard(player_stats_summary['TEAM'])
    player_stats_summary['OPPONENT'] = convert_team_ini_to_standard(player_stats_summary['OPPONENT'])

    player_stats_summary = add_OUT_and_BYE(player_stats_summary, stat_to_check='PA', stat_val_to_check='--')

    if def_scoring_ranges:
        # Create PAPTS and YAPTS for defensive fantasy scoring
        player_stats_summary.loc[(player_stats_summary['PA'] == na_val), 'PA'] = -1
        player_stats_summary.loc[(player_stats_summary['YA'] == na_val), 'YA'] = -1

        player_stats_summary['PA'] = player_stats_summary['PA'].astype(int)
        player_stats_summary['YA'] = player_stats_summary['YA'].astype(int)

        player_stats_summary['PAPTS'] = pd.cut(player_stats_summary['PA'], bins=[-2, -1, 0, 6, 13, 17, 27, 34, 45, 200], 
                                            labels=[na_val, def_scoring_ranges['PA0'], def_scoring_ranges['PA1'], def_scoring_ranges['PA7'], def_scoring_ranges['PA14'],
                                                    def_scoring_ranges['PA18'], def_scoring_ranges['PA28'], def_scoring_ranges['PA35'], def_scoring_ranges['PA46']])
        player_stats_summary['YAPTS'] = pd.cut(player_stats_summary['YA'], bins=[-2, -1, 99, 199, 299, 349, 399, 449, 499, 549, 1000], 
                                            labels=[na_val, def_scoring_ranges['YA100'], def_scoring_ranges['YA199'], def_scoring_ranges['YA299'], def_scoring_ranges['YA349'],
                                                    def_scoring_ranges['YA399'], def_scoring_ranges['YA449'], def_scoring_ranges['YA499'], def_scoring_ranges['YA549'],
                                                    def_scoring_ranges['YA550']])

        player_stats_summary['PA'] = player_stats_summary['PA'].astype(str)
        player_stats_summary['YA'] = player_stats_summary['YA'].astype(str)

        player_stats_summary.loc[(player_stats_summary['PA'] == '-1'), 'PA'] = na_val
        player_stats_summary.loc[(player_stats_summary['YA'] == '-1'), 'YA'] = na_val

    return player_stats_summary
def import_full_team_data(selected_weeks, file_path_dict, defense_scoring_ranges=False):
    '''
    Forms a merged dataframe using import player, kicker, and defense data. Returns a dataframe.
    
    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        defense_scoring_ranges (dict or bool): dictionary of defense points against and yards against scoring rules like {'PA0': 5, 'PA1': 4, 'PA7': 3 ... 'YA100': 5 ...}

    Returns:
        pd.DataFrame: all fantasy player data
    '''
    player_data = import_player_data(selected_weeks, file_path_dict)
    kicker_data = import_kicker_data(selected_weeks, file_path_dict)
    defense_data = import_defense_data(selected_weeks, file_path_dict, defense_scoring_ranges)
    
    merged = pd.concat([player_data, kicker_data, defense_data], join='outer')
    merged = merged.infer_objects(copy=False).fillna(0).reset_index(drop=True)
    return merged

# Importing offensive player data with snap count information
def import_utilization_data(selected_weeks, file_path_dict):
    '''
    Import utilization data from Excel for the weeks in the selected_weeks. 

    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values

    Returns:
        pd.DataFrame: offensive player utilization data
    
    '''
    # Static values
    util_cols = [0,1,2,3,4,5,6,7,8,9,10,11,12]
    global utilization_data_file 
    # Initialize summary
    util_summary = pd.DataFrame()
    selected_weeks = convert_selected_weeks_input(selected_weeks)
    validate_selected_weeks(selected_weeks)
    for sheet in selected_weeks:
        # Import from Excel
        util_data = import_utilization_data_from_file(file_path_dict['utilization_data'], sheet, util_cols)
        # Add column for week
        util_data['WEEK'] = sheet
        # Append data to summary df
        util_summary = pd.concat([util_summary, util_data], ignore_index=True)
    return util_summary
def import_player_with_util_data(selected_weeks, file_path_dict):
    '''
    selected_weeks must be either a string like 'WK1', 'WK2', or 'all', or a list of these values.
    Imports data using import_player_data and import_utilization_data and merges the two with an outer join. 
    
    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        
    Returns:
        pd.DataFrame: offensive player data with utilization stats
    
    '''
    global teams

    player_data = import_player_data(selected_weeks, file_path_dict)
    util_data = import_utilization_data(selected_weeks, file_path_dict)
    new_table = player_data.merge(util_data, on=['PLAYER', 'POS', 'WEEK','TEAM'], how='outer', suffixes=('','_U'))
    
    opp_dict = {}
    filled_opp = new_table[~new_table['OPPONENT'].isna()]
    na_opp = new_table[new_table['OPPONENT'].isna()]
    
    for index, row in filled_opp.iterrows():
        if row['TEAM'] in opp_dict.keys():
            if row['WEEK'] in opp_dict[row['TEAM']].keys():
                continue    
            else:
                opp_dict[row['TEAM']][row['WEEK']] = row['OPPONENT']
                continue
        opp_dict[row['TEAM']] = {row['WEEK']: row['OPPONENT']}
       
    for index, row in na_opp.iterrows():
        
        if row['TEAM'] in opp_dict.keys():
            if row['WEEK'] in opp_dict[row['TEAM']].keys():
                new_table.loc[index, 'OPPONENT'] = opp_dict[row['TEAM']][row['WEEK']]
            else:
                new_table.loc[index, 'OPPONENT'] = 'BYE WEEK'
        
    return new_table

# Other imports to be used with the player_data dataframe
def import_recent_roster_mappings(owners_for_manual_corrections, file_path_dict, pull_from_dataframe=False):
    '''
    Import the players specifically on rosters based on the three most recent weeks to player_scoring_data. 
    Returns dictionary with player names as keys. pull_from_dataframe is a dataframe of player data to pull
    the most recent roster mappings from. If not entered, a full import is run.
    
    Args:
        owners_for_manual_correction (dict or bool): {old_team_initials: [new_team1, new_team2]}, correct owners with old_team_initials based on ref_for_manual_corrections file. 
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        pull_from_dataframe (False or pd.Dataframe, optional): if set to a pd.Dataframe, pulls roster mappings from this dataframe.
            Otherwise, imports full_team_data for most recent mappings.

    Returns:
        dict: {PLAYER: OWNER}
    '''
    global valid_sheet_names
    global na_val

    most_recent = valid_sheet_names.copy()
    most_recent.reverse() 
    # Removed line to cut down on most recent weeks, long term injuries result in players not being on rosters.
    map_dict = {}

    if isinstance(pull_from_dataframe, pd.DataFrame): 
        for week in most_recent:
            rel_subset = pull_from_dataframe.loc[pull_from_dataframe['WEEK'] == week]
            for index, row in rel_subset.iterrows():
                if ((row['OWNER'] != na_val) and (row['OWNER'] != 0) and (row['PLAYER'] not in map_dict.keys())):
                    map_dict[row['PLAYER']] = row['OWNER']

    else:
        for week in most_recent:
            player_data = import_full_team_data(week)
            player_data = player_data[['PLAYER', 'TEAM', 'POS', 'OWNER']]
            
            for index, row in player_data.iterrows():
                if ((row['OWNER'] != na_val) and (row['PLAYER'] not in map_dict.keys())):
                    map_dict[row['PLAYER']] = row['OWNER']
    if owners_for_manual_corrections:
        map_dict = run_manual_roster_corrections(map_dict, owners_for_manual_corrections, file_path_dict)
    return map_dict
def import_nfl_team_pos_mappings(file_path_dict):
    '''
    Import a dictionary {'PLAYER': ['TEAM', 'POS']} based on most recent additions to scoring data. Returns a dictionary.
    
    Args:
        file_path_dict (dict): dictionary with original file name as keys and file paths as values

    Returns:
        dict: {PLAYER: [TEAM, POS]}
    '''
    global valid_sheet_names
    most_recent = valid_sheet_names
    most_recent.reverse()
    map_dict = {}
    for week in most_recent:
        player_data = import_full_team_data(week, file_path_dict)
        player_data = player_data[['PLAYER', 'TEAM', 'POS']]
        for index, row in player_data.iterrows():
            if not(row['PLAYER'] in map_dict.keys()):
                if row['TEAM'] not in teams:
                    map_dict[row['PLAYER']] = [row['POS'], row['TEAM']]
                else:
                    map_dict[row['PLAYER']] = [row['TEAM'], row['POS']]
   
    return map_dict
def run_manual_roster_corrections(map_dict, owners_for_manual_correction, file_path_dict):
    '''
    For import_recent_roster_mappings, manual corrections for teams with the same initials.
    
    Args:
        owners_for_manual_correction (dict): {old_team_initials: [new_team1, new_team2]}, correct owners with old_team_initials based on ref_for_manual_corrections file. 
        map_dict (dict): roster mapping dictionary to run corrections on.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values

    Returns:
        dict: {PLAYER: OWNER}
    '''
    
    global na_val
    global inj_status
    for old_name, owners in owners_for_manual_correction.items():
        for owner in owners:
            raw_players = pd.read_excel(file_path_dict['ref_for_manual_corrections'], sheet_name=owner, skiprows=1)
            raw_players['Player'] = raw_players['Player'].fillna(na_val).astype(str)
            # Name corrections
            loop_num = 0
            while loop_num < len(raw_players):
                str1 = raw_players.iloc[loop_num,1]
                if str1 == na_val:
                    loop_num += 1
                    continue
                str2 = raw_players.iloc[(loop_num+1),1]
                end_name_pos = 0
                #print('str1: ',str1,' str2: ',str2)
                for num, char in enumerate(str2):
                    if char != str1[num]: 
                        end_name_pos = num 
                        break
                if end_name_pos == 0:
                    player_name = str2
                else:
                    player_name = str2[:end_name_pos]
                
                # Weird edge case for IR players, any players name ending in capital I, Q, D, with the exception of III will be stripped
                if player_name[(len(player_name)-3):] != 'III' :
                    for status in inj_status:
                        if len(status) > 1:
                            status = status[0]
                        if player_name[(len(player_name)-1)] == status :
                            player_name = player_name[:(len(player_name)-1)]
                if player_name in map_dict.keys():
                    map_dict[player_name] = owner
                loop_num += 3
        # Treating the corrections as the most up to date roster
        for key, value in map_dict.items():
            if value == old_name:
                map_dict[key] = 'FA'
    return map_dict
def import_player_status(selected_weeks, file_path_dict):
    ''' 
    Import player status data for the selected weeks from Excel. Returns dataframe.
    
    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values

    Returns:
        pd.DataFrame: players who were out or on bye on a given week.
    '''
    # Static values
    status_cols = [0,1,2,3]
    
    # Initialize summary
    summary = pd.DataFrame()
    selected_weeks = convert_selected_weeks_input(selected_weeks)
    validate_selected_weeks(selected_weeks)
    for sheet in selected_weeks:
        # Import from Excel
        data = pd.read_excel(file_path_dict['players_out_by_week'], sheet_name=sheet, usecols=status_cols)
        # Add column for week
        data['WEEK'] = sheet
        # Append data to summary df
        summary = pd.concat([summary, data], ignore_index=True)
    return summary
def import_player_status_dict(selected_weeks, file_path_dict):
    '''
    Reformats output of import_player_status. Returns dictionary formatted {('PLAYER', 'TEAM', 'POS'): {'WEEK': 'STATUS'}} where status is either 'Out' or 'BYE'.
    
    Args:
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values

    Returns:
        dict: {('PLAYER', 'TEAM', 'POS'): {'WEEK': 'STATUS'}}

    '''
    global teams

    player_status_df = import_player_status(selected_weeks, file_path_dict)
    #print(player_status_df.head())
    player_status_dict = {}
    for index, row in player_status_df.iterrows():
        team = row['TEAM']
        pos = row['POS']

        if (row['PLAYER'], team, pos) in player_status_dict.keys():
            player_status_dict[(row['PLAYER'], team, pos)][row['WEEK']] = row['STATUS']
        else:
            player_status_dict[(row['PLAYER'], team, pos)] = {row['WEEK']: row['STATUS']}
    return player_status_dict
def import_nfl_schedule_dict(file_path_dict, selected_weeks='all'):
    '''
    Import a dictionary of the NFL schedule with teams as primary key, week as secondary key, and opponent as value. Returns dictionary.
    
    Args:
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        selected_weeks (str or list, optional): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.

    Returns:
        dict: {TEAM: {WEEK: OPPONENT}}

    '''
    global nfl_schedule_file
    selected_weeks = convert_selected_weeks_input(selected_weeks)
    schedule_dict = {}

    # Import
    schedule = pd.read_excel(file_path_dict['nfl_schedule_2024'], index_col=0)
    
    for team, row in schedule.iterrows():
        for week in selected_weeks:
            if team in schedule_dict.keys():
                schedule_dict[team][week] = row[week]
            else:
                schedule_dict[team] = {week: row[week]}
    return schedule_dict
def import_owner_matchups(file_path_dict):
    '''
    Import owner matchups from current league info with owners as the index. Returns dataframe.
    
    Args:
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
    Returns:
        pd.DataFrame: owner matchups
    
    '''
    owner_matchups = pd.read_excel(file_path_dict['current_league_info'], sheet_name='FFL_Schedule', index_col=0)

    return owner_matchups
def import_current_standings(file_path_dict):
    '''
    Import current owner standings from current league info with owners as the index. Returns dataframe.
    
    Args:
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
    
    Returns:
        pd.DataFrame: current standings with owners as index.

    '''
    current_standings = pd.read_excel(file_path_dict['current_league_info'], sheet_name='Standings', index_col=0)

    return current_standings

# Used in dataframe imports for handling players who did not play on a given week
def add_OUT_and_BYE(player_stats_summary, stat_to_check, stat_val_to_check):
    '''
    Adds bool columns OUT and BYE based on stat_to_check and stat_val_to_check are the column value pair that indicates the player did not play on a given week. 
    
    Args:
        player_stats_summary (pd.DataFrame): dataframe of player data to add to
        stat_to_check (str): label of column in player_stats_summary to check
        stat_val_to_check (str): value in stat_to_check column to indicate player did not play

    Returns:
        pd.DataFrame: player_stats_summary with added bool columns OUT and BYE

    '''

    player_stats_summary = player_stats_summary.assign(OUT=lambda x: ((x[stat_to_check] == stat_val_to_check) & (x['OPPONENT'] != '*BYE*')))
    player_stats_summary = player_stats_summary.assign(BYE=lambda x: ((x[stat_to_check] == stat_val_to_check) & (x['OPPONENT'] == '*BYE*')))

    return player_stats_summary
def add_dnp_players(player_stats_summary, selected_weeks, file_path_dict):
    '''
    Specific to import_player_data (does not include defense or kicker data). Adds rows in player_stats_summary for players who did not play 
    on a given week listed in the players_out_by_week Excel file. Returns the expanded dataframe
    
    Args:
        player_stats_summary (pd.DataFrame): dataframe to add rows to
        selected_weeks (str or list): weeks to return data for. 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
        file_path_dict (dict): dictionary with original file name as keys and file paths as values


    Returns:
        pd.DataFrame: player_stats_summary with added rows
    '''
    global na_val
    global teams
    global positions
    
    df_set_index = player_stats_summary.set_index(['PLAYER', 'WEEK'])
    player_status_dict = import_player_status_dict(selected_weeks, file_path_dict)
    new_entries = pd.DataFrame(columns=player_stats_summary.columns)
    index = 0
    # key1 is player, key2 is week
    for key1, value1 in player_status_dict.items():
        for key2, value2 in value1.items():
            # If the entry doesn't already exist in the dataframe
            if not((key1, key2) in df_set_index.index):
                new_entries.loc[index, 'PLAYER'] = key1[0]
                new_entries.loc[index, 'WEEK'] = key2

                assert key1[1] in teams
                assert key1[2] in positions

                new_entries.loc[index, 'TEAM'] = key1[1]
                new_entries.loc[index, 'POS'] = key1[2]
                if value2.str.upper() == 'BYE':
                    new_entries.loc[index, 'BYE'] = True
                    new_entries.loc[index, 'OUT'] = False
                else: 
                    new_entries.loc[index, 'BYE'] = False
                    new_entries.loc[index, 'OUT'] = True
                index+=1
    
    new_entries = new_entries.infer_objects(copy=False)
    values_dict = get_row_for_out_bye(new_entries.columns) # Filling NA, no need to worry about OUT/BYE args
    for col in new_entries.columns:
        new_entries[col].fillna(values_dict[col])

    return pd.concat([player_stats_summary, new_entries])
def add_missing_player_rows(player_data, file_path_dict, include_team_pos_data=True):
    '''
    Adds rows to player data for listed players missing values for certain weeks due to low point totals. Fills in stats with fill_value.
    include_team_pos_data is a bool to include the players most recent team and position mapping on new entries. Returns dataframe.
    
    Args:
        player_data (pd.DataFrame): dataframe to add rows to
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        include_team_pos_data (bool, optional): include team, pos data based on most recent player data, more performance intensive, default: True
        
    Returns:
        pd.DataFrame: dataframe with added rows for missing players
    '''
    
    if include_team_pos_data:
        team_pos_map = import_nfl_team_pos_mappings(file_path_dict)
    
    # {team: {week: oppponent}}
    nfl_schedule_dict = import_nfl_schedule_dict()

    players = unique(player_data['PLAYER'])
    weeks = unique(player_data['WEEK'])
    players_dict = {}
    # Create a tracker dictionary with all entries 
    for player in players:
        players_dict[player] = {weeks[0]: False}
        for week in weeks[1:]:
            players_dict[player][week] = False

    # In players_dict mark off existing values
    for index, row in player_data.iterrows():
        players_dict[row['PLAYER']][row['WEEK']] = True        

    # Create new entries for each key pair still False in players_dict
    new_entries = pd.DataFrame(columns=player_data.columns)
    ne_index = 0
    for player, value1 in players_dict.items():
        for week, value2 in value1.items():
            if value2:
                continue
            else:
                new_entries.loc[ne_index, 'PLAYER'] = player
                new_entries.loc[ne_index, 'WEEK'] = week
                if include_team_pos_data:
                    new_entries.loc[ne_index, 'POS'] = team_pos_map[player][1]
                    new_entries.loc[ne_index, 'TEAM'] = team_pos_map[player][0]
                    if nfl_schedule_dict[team_pos_map[player][0]][week] == 'BYE':
                        new_entries.loc[ne_index, 'BYE'] = True
                ne_index += 1


    new_entries = new_entries.infer_objects(copy=False)
    values_dict = get_row_for_missing(new_entries.columns)
    for col in new_entries.columns:
        new_entries[col].fillna(values_dict[col])

    new_df = pd.concat([player_data, new_entries])
    new_df = new_df.reset_index(drop=True)
    return new_df

# Direct file imports with formatting
def import_player_data_from_file(player_data_file, sheet, players_cols):
    '''
    Import and manipulate the player half of the data from Excel. Return a dataframe of the player data from sheet.
    
    Args:
        player_data_file (str): file path
        sheet (str): sheet to import
        player_cols (list): columns with player data
        
    Returns:
        pd.DataFrame: dataframe with player data
    '''
    # Globals
    global filler_value

    # Import
    raw_players = pd.read_excel(player_data_file,sheet_name=sheet,usecols=players_cols)
    raw_players['Unnamed: 5'] = raw_players['Unnamed: 5'].fillna(filler_value).astype(str)
    
    #print(raw_players.head())
    # Initialize values
    skip = True
    player_data = []
    loop_num = 0 # used in loop_num as the index value

    while loop_num < len(raw_players): 
        # Iterate loop_num if we are not currently on a row with player data
        if (raw_players.iloc[loop_num, 5] == filler_value)|(raw_players.iloc[loop_num, 5] == 'proj') :
            skip = True
            while skip == True:
                loop_num+=1
                if loop_num >= len(raw_players):
                    break
                elif raw_players.iloc[(loop_num-1), 5] == 'proj':
                    skip = False
        
        # Sanity check for index integrity
        if loop_num+2 >= len(raw_players):
            break
        
        #print('week: ',sheet,' loop_num: ',loop_num)
        player_name, team_ini, position, owner_ini, opponent_ini, final_score, proj_pts = parse_player_chunk(raw_players, chunk_start_index=loop_num)
        player_data.append([player_name, team_ini, position, owner_ini, opponent_ini, final_score, proj_pts])

        # Jump to next player
        loop_num += 3
    players = pd.DataFrame(player_data, columns=['PLAYER', 'TEAM', 'POS', 'OWNER', 'OPPONENT', 'FINALSCORE', 'PROJ']).reset_index(drop=True)
    #print('length players: ', len(players))
    return players
def import_stats_data_from_file(player_data_file, sheet, stats_cols, column_labels, type='Offense'):
    '''
    Import and manipulate the stats half of the data from Excel. Return a dataframe of the player data from sheet.
    Type is to indicate the type of file: 'Offense', 'Kicker', 'Defense'
    
     Args:
        player_data_file (str): file path
        sheet (str): sheet to import
        stats_cols (list): columns with stats data
        column_labels (list): labels to give columns, post data manipulation
        type (str, optional): type of file import, 'Offense', 'Defense', 'Kicker'. Default: 'Offense'
        
    Returns:
        pd.DataFrame: dataframe with stats data
    '''
    stats = pd.read_excel(player_data_file,sheet_name=sheet,usecols=stats_cols)
    # Only manipulation on stats is to drop header rows
    if type == 'Offense':
        header_rows = stats[(stats['Passing'] == 'C/A') | (stats['Passing'] == 'Passing')]
        #print(header_rows)
    elif type == 'Kicker':
        header_rows = stats[(stats['Kicking'] == 'FG39/FGA39') | (stats['Kicking'] == 'Kicking')]
    else:
        header_rows = stats[(stats['Team Defense / Special Teams'] == 'TD') | (stats['Team Defense / Special Teams'] == 'Team Defense / Special Teams')]
 
    stats.drop(header_rows.index, inplace=True)
    stats.dropna(inplace=True)
    stats = stats.reset_index(drop=True)
    stats.columns = column_labels
    #print('length stats: ', len(stats['FPTS']))
    #print(stats['C/A'].unique())
    return stats
def import_utilization_data_from_file(utilization_data_file, sheet, util_cols):
    '''
    Complete the import and format the data from Excel. Returns dataframe.

     Args:
        utilization_data_file (str): file path
        sheet (str): sheet to import
        util_cols (list): columns with relevant data
        
    Returns:
        pd.DataFrame: dataframe with utilization data
    '''
    util_data = pd.read_excel(utilization_data_file, sheet_name=sheet, usecols=util_cols, skiprows=1)
    util_data.columns = util_data.columns.str.upper()
    return util_data

# Used in file imports
def parse_out_player_name(raw_players, chunk_start_index):
    '''
    Takes raw player data from Excel files and an index value corresponding to the start of the player chunk.
    Parses out and returns the player_name.
    
    Args:
        raw_players (pd.DataFrame): dataframe to manipulate
        chunk_start_index (int): index value corresponding to start of player chunk
        
    Returns:
        str: parsed player name
    
    '''
    # need raw_players, start_index (rename to index_num) return player_name    
    # Name corrections
    global inj_status
    str1 = raw_players.iloc[chunk_start_index,0]
    str2 = raw_players.iloc[(chunk_start_index+1),0]
    end_name_pos = 0
    for num, char in enumerate(str2):
        if char != str1[num]: 
            end_name_pos = num 
            break
    if end_name_pos == 0:
        player_name = str2
    else:
        player_name = str2[:end_name_pos]
    
    # Weird edge case for IR players, any players name ending in capital I, Q, D, with the exception of III will be stripped
    if player_name[(len(player_name)-3):] != 'III' :
        for status in inj_status:
            if len(status) > 1:
                status = status[0]
            if player_name[(len(player_name)-1)] == status :
                player_name = player_name[:(len(player_name)-1)]
    return player_name
def parse_out_team_and_pos(raw_players, chunk_start_index):
    '''
    Takes raw player data from Excel files and an index value corresponding to the start of the player chunk.
    Parses out and returns a tuple: (team_ini, position)
    
    Args:
        raw_players (pd.DataFrame): dataframe to manipulate
        chunk_start_index (int): index value corresponding to start of player chunk
        
    Returns:
        tuple: (team_ini, pos), parsed player team and position
    '''
    global positions
    global na_val
    team_ini = na_val
    team_pos = raw_players.iloc[(chunk_start_index+2),0]
    for pos in positions:
        if team_pos[len(team_pos)-len(pos):] == pos:
            position = pos
            team_ini = team_pos[:len(team_pos)-len(pos)].upper()

    if team_ini == na_val:        
        raise ValueError(f'Unable to parse out string: {team_pos}')

    return (team_ini, position)
def parse_out_owner(raw_players, chunk_start_index):
    '''
    Takes raw player data from Excel files and an index value corresponding to the start of the player chunk.
    Parses out and returns a team owner_ini

    Args:
        raw_players (pd.DataFrame): dataframe to manipulate
        chunk_start_index (int): index value corresponding to start of player chunk
        
    Returns:
        str: parsed player owner
    '''
    owner_ini = raw_players.iloc[chunk_start_index,1].upper()
    # Set to FA if listed on waivers
    if 'WA ' in owner_ini:
        owner_ini = 'FA'
    return owner_ini
def parse_out_opponent(raw_players, chunk_start_index):
    '''
    Takes raw player data from Excel files and an index value corresponding to the start of the player chunk.
    Parses out and returns a team opponent_ini
    
    Args:
        raw_players (pd.DataFrame): dataframe to manipulate
        chunk_start_index (int): index value corresponding to start of player chunk
        
    Returns:
        str: parsed opponent
    '''
    opponent_ini = raw_players.iloc[chunk_start_index,3].upper()
    if opponent_ini[0] == '@':
        opponent_ini = opponent_ini[1:]
    return opponent_ini
def parse_player_chunk(raw_players, chunk_start_index):
    '''
    Takes raw player data from Excel files and an index value corresponding to the start of the player chunk.
    Parses out all relevant values, returns tuple (player_name, team_ini, position, owner_ini, opponent_ini, final_score, proj_pts)
    
    Args:
        raw_players (pd.DataFrame): dataframe to manipulate
        chunk_start_index (int): index value corresponding to start of player chunk
        
    Returns:
        tuple: (player_name, team_ini, position, owner_ini, opponent_ini, final_score, proj_pts), parsed player info
    '''

    player_name = parse_out_player_name(raw_players, chunk_start_index)
    team_ini, position = parse_out_team_and_pos(raw_players, chunk_start_index)
    owner_ini = parse_out_owner(raw_players, chunk_start_index)
    opponent_ini = parse_out_opponent(raw_players, chunk_start_index)
    final_score = raw_players.iloc[chunk_start_index,4]
    proj_pts = raw_players.iloc[chunk_start_index,5]
    return (player_name, team_ini, position, owner_ini, opponent_ini, final_score, proj_pts)

# Utility functions
def convert_team_ini_to_standard(team_ini_col):
    '''
    Converts any non-standard team ini values to standard array below. Returns a pandas Series. 
    
    Args:
        team_ini_col (pd.Series): team column to convert

    Returns:
        pd.Series: team_ini_col with corrections made
    '''
    #print(team_ini_col)
    global teams
    standard_array = teams
    for num, val in enumerate(team_ini_col):
        if val not in standard_array:
            #print(num," ",val)  #***
            if val == 'JAX':
                #print(num)
                new_val = 'JAC'
            elif val == 'WSH':
                new_val = 'WAS'
            elif len(val) > 3:
                new_val = val[:3]
            elif val == '--':
                new_val = 'FA'
            else:
                raise ValueError(f'Team INI value {val} is not accounted for. Need to adjust convert_team_ini_to_standard.')
            team_ini_col[num] = new_val

    return team_ini_col
def convert_selected_weeks_input(selected_weeks):
    ''' 
    Input handling for selected_weeks. Returns a list of weeks.
    
    Args:
        selected_weeks (str or list): 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.

    Returns:
        list: list of weeks
    '''
    global valid_sheet_names
    global all_sheet_names
    new_selected_weeks = selected_weeks
    if isinstance(selected_weeks, str):
        if selected_weeks.lower() == 'all':
            new_selected_weeks = all_sheet_names
        elif selected_weeks.lower() == 'all_valid':
            new_selected_weeks = valid_sheet_names
        else:
            new_selected_weeks = [selected_weeks]
    return new_selected_weeks
def validate_selected_weeks(selected_weeks):
    ''' 
    Assert that the input is valid. Otherwise, throws error.
    Args:
        selected_weeks (str or list): 'all' for all weeks, 'all_valid' for previous weeks. 
            Otherwise a string or list of strings like 'WK1', 'WK2', etc.
    
    '''
    global valid_sheet_names
    for week in selected_weeks:
        assert week in valid_sheet_names
def unique(list):
    '''
    Returns a list of unique values in the input list.
    
    Args:
        list (list): inputs to check

    Returns:
        list: list of unique values
    '''
    unique_list = []
    for x in list:
        # check if exists in unique_list or not
        if x not in unique_list:
            unique_list.append(x)
    return unique_list

# Slicing player data
def slice_of_player_data(player_data, team_input='ALL', pos_input='ALL', opp_input='ALL', weeks_input='ALL', use_basic_stats=True):
    '''
    Function to return slice of player data filtered by the inputs. If any input is not used,
    player data is not filtered by that value. Returns dataframe. Any one of the inputs can be
    a string or a list of strings. basic_stats is a boolean whether or not to return only basic 
    stats (no snap count analysis).

    Args:
        player_data (pd.DataFrame): data to be parsed
        team_input (str or list): string or list of teams to include
        pos_input (str or list): string or list of positions to include
        opp_input (str or list): string or list of opponents to include
        weeks_input (str or list): string or list of weeks to include
        use_basic_stats (bool): drops non-standard statistics.

    Returns:
        pd.DataFrame: player_data filtered
    '''
    global teams
    global basic_stats
    global standard_columns
    global all_sheet_names
    global positions
    all_weeks = all_sheet_names

    if team_input!='ALL':
        if isinstance(team_input, str):
            assert team_input in teams
            player_data = player_data[player_data['TEAM'] == team_input]
        elif isinstance(team_input, list):
            if team_input: #there is content in the list
                for value in team_input:
                    assert value in teams
                player_data = player_data[player_data['TEAM'].isin(team_input)]
    
    if pos_input!='ALL':
        if isinstance(pos_input, str):
            assert pos_input in positions
            player_data = player_data.loc[player_data['POS'] == pos_input]
            if use_basic_stats:
                cols = standard_columns+basic_stats[pos_input]
                player_data = player_data[cols]

        elif isinstance(pos_input, list):
            if pos_input:
                for value in pos_input:
                    assert value in positions
                    
                player_data = player_data[player_data['POS'].isin(pos_input)]

                if use_basic_stats:
                    cols = standard_columns
                    for value in pos_input:
                        cols = cols+basic_stats[value]
                    cols = unique(cols)
                    player_data = player_data[cols]
    elif use_basic_stats:
        cols = standard_columns+basic_stats[pos_input]
        player_data = player_data[cols]

    
    if opp_input!='ALL':
        if isinstance(opp_input, str):
            assert opp_input in teams
            player_data = player_data[player_data['OPPONENT'] == opp_input]
        elif isinstance(opp_input, list):
            if opp_input:
                for value in opp_input:
                    assert value in teams
                player_data = player_data[player_data['OPPONENT'].isin(opp_input)]
    
    if weeks_input!='ALL':
        if isinstance(weeks_input, str):
            assert weeks_input in all_weeks
            player_data = player_data[player_data['WEEK'] == weeks_input]
        elif isinstance(weeks_input, list):
            if weeks_input:
                for value in weeks_input:
                    assert value in all_weeks
                player_data = player_data[player_data['WEEK'].isin(weeks_input)]
    
    return player_data 

# Functions for additional features
def add_FPTS_CLASS(data):
    '''
    Adds a new column to the dataframe 'FPTS_CLASS' based on 'FPTS'. Returns dataframe.
    
    Args:
        data (pd.DataFrame): dataframe to add column to

    Returns:
        pd.DataFrame: dataframe with added column
    
    '''
    global na_val

    data.loc[data['FPTS'] == na_val, 'FPTS'] = 0
    data['FPTS'] = data['FPTS'].astype(float)
    data['FPTS_CLASS'] = pd.cut(data['FPTS'], bins=[-20, 10, 15, 20, 25, 100], right=False, labels=[0, 1, 2, 3, 4])
    #print(data[data['PLAYER']=='Colts D/ST'])    
    data['FPTS_CLASS'] = data['FPTS_CLASS'].astype(int)
    return data
def add_OWNER(data, file_path_dict, owners_for_manual_correction=False, pull_mapping_from_df=False):
    '''
    Adds column 'OWNER' to dataframe data or refreshes column using most recent roster mappings.
    pull_mapping_from_df is a bool, if true will pull the owner roster mappings from the passed in dataframe.
    
    Args:
        data (pd.DataFrame): dataframe to add column to
        file_path_dict (dict): dictionary with original file name as keys and file paths as values
        owners_for_manual_correction (dict or bool, optional): {old_team_initials: [new_team1, new_team2]}, correct owners with old_team_initials based on ref_for_manual_corrections file. 
        pull_mapping_from_df (bool or pd.DataFrame, optional): if a dataframe, will pull recent roster mappings from this dataframe.

    Returns:
        pd.DataFrame: dataframe with owner data
    
    '''
    if pull_mapping_from_df:
        map_dict = import_recent_roster_mappings(owners_for_manual_correction, file_path_dict, pull_from_dataframe=data)
    else: 
        map_dict = import_recent_roster_mappings(owners_for_manual_correction, file_path_dict)
    
    
    for index, row in data.iterrows():

        if row['PLAYER'] in map_dict.keys():
            data.loc[index, 'OWNER'] = map_dict[row['PLAYER']]
        else:
            data.loc[index, 'OWNER'] = 'FA'
    return data
def add_STARTER_and_STARTPOS(data, value_cols=['FPTS_CLASS', 'FPTS'], start_by_pos={'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'D/ST': 1}, flex_positions=['RB', 'WR', 'TE'], debug_mode=False):
    '''
    Takes in a dataframe where 'PLAYER' values are unique and 'OWNER' values have been added and adds columns for 'STARTER' (boolean) and
    'STARTPOS' indicating RB1, WR2, FLEX, etc. based on 'FPTS_CLASS' and 'FPTS' columns. value_cols is a list of player values to sort by,
    higher values are better. Returns dataframe with additional columns
    
    Args:
        data (pd.DataFrame): dataframe to add columns to
        value_cols (list, optional): list of columns used for player values in determining starters. Default: ['FPTS_CLASS', 'FPTS']
        start_by_pos (dictionary, optional): keys = positions, values = number to start. Default: {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'D/ST': 1}
        flex_positions (list, optional): list of positions considered for FLEX. Default: ['RB', 'WR', 'TE']
        debug_mode (bool, optional): more verbose output used for debugging. Default: False

    Returns:
        pd.DataFrame: dataframe with added columns
    
    '''
    
    owners = data['OWNER'].unique()

    ascending = []
    for val in value_cols:
        ascending.append(False)

    for owner in owners:
        # Skip players not on teams
        if debug_mode:
            print(owner)
        if owner == na_val:
            continue
        subset = data.loc[data['OWNER'] == owner]
        for key, value in start_by_pos.items():
            # key is pos, value is number to start
            if key == 'FLEX':
                pos_subset = data.loc[(data['POS'].isin(flex_positions)) & (data['STARTER'] != True) & (data['OWNER'] == owner)]     # This only works if flex is the last listed start_by_pos
                if pos_subset.empty:
                    continue        # This condition causes an error, it is normal for an owner to not have a starting player due to future bye weeks
                pos_subset_sorted = pos_subset.sort_values(by=value_cols, ascending=ascending).reset_index()
                #print(pos_subset_sorted)
                for i in range(value):
                    if debug_mode:
                        print('key: ',key,' i: ',i,' value: ',value)
                    index_val = pos_subset_sorted.loc[i, 'index']
                    data.loc[index_val, 'STARTER'] = True
                    data.loc[index_val, 'STARTPOS'] = key
            else:
                pos_subset = subset.loc[subset['POS'] == key]
                #if pos_subset.empty:
                #    continue        # This condition causes an error, it is normal for an owner to not have a starting player due to future bye weeks
                if len(pos_subset['PLAYER']) < value:
                    continue       # This condition causes an error, it is normal for an owner to not have a starting player due to future bye weeks

                pos_subset_sorted = pos_subset.sort_values(by=value_cols, ascending=ascending).reset_index()
                #print(pos_subset_sorted)
                for i in range(value):
                    if debug_mode:
                        print('key: ',key,' i: ',i,' value: ',value)
                    index_val = pos_subset_sorted.loc[i, 'index']
                    data.loc[index_val, 'STARTER'] = True
                    if value > 1:
                        start_pos = key + str(i+1)
                    else: 
                        start_pos = key
                    data.loc[index_val, 'STARTPOS'] = start_pos
    
    # Fill in everything else
    data.loc[data[data['STARTER'].isna()].index, 'STARTER'] = False
    data.loc[data[data['STARTPOS'].isna()].index, 'STARTPOS'] = na_val
    
    return data

# Functions for dnp and missing handling
def get_row_for_out_bye(columns, bye=False, out=False):
    '''
    Returns a dictionary used for filling columns with a value indicating player was out or on bye.
    Args:
        columns (list): columns to be filled
        bye (bool): set to true if player on bye
        out (boot): set to true if player is out

    Returns:
        dictionary: {columns: values}
    '''
    global na_val
    summary_dict = {}
    for column in columns:
        if (column == 'OUT'):
            summary_dict[column] = out
        elif (column == 'BYE'):
            summary_dict[column] = bye  
        elif ('/' in column):
            summary_dict[column] = na_val + '/' + na_val
        else:
            summary_dict[column] = na_val
    
    return summary_dict
def get_row_for_missing(columns):
    '''
    Returns a dictionary used for filling columns with a value indicating player was missing from the top 300 on a given week.
    Args:
        columns (list): columns to be filled

    Returns:
        dictionary: {columns: values}
    '''
    global na_val
    summary_dict = {}
    for column in columns:
        if (column == 'OUT'):
            summary_dict[column] = False
        elif (column == 'BYE'):
            summary_dict[column] = False 
        elif (column == 'PA') | (column == 'YA'):
            summary_dict[column] = na_val
        elif ('/' in column):
            summary_dict[column] = na_val + '/' + na_val
        else:
            summary_dict[column] = 0
    
    return summary_dict

# Used to add additional rows for players with missing info, assumed zeros for a given week
