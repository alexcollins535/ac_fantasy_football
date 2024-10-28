import fantasy_football.ffl_data_importing as fdi
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Global Imports
teams = fdi.teams
positions = fdi.positions
valid_weeks = fdi.valid_sheet_names
all_weeks = fdi.all_sheet_names
future_weeks = fdi.future_weeks
na_val = fdi.na_val
file_path_dict = fdi.file_path_dict

# League Specific Globals
owners_for_manual_correction = {'CARM': ['CJ', 'MAS']} # Teams with the same initials
scoring_rules = {'PAYDS': 0.04, 'PATD': 6, 'INT': -2, 'RUYDS': 0.1, 'RUTD': 6, 'REC': 1, 'REYDS': 0.1, 'RETD': 6, '2PC': 2, 'FUML': -2,
                 'MISCTD': 6, 'FG50': 5, 'FG40': 4, 'FG0': 3, 'FGM': -1, 'XPTM': 1, 'DEFTD': 6, 'SCK': 1, 'DEFINT': 2, 'SFTY': 2, 'FR': 2,
                 'PAPTS': 1, 'YAPTS': 1, 'CAR': 0}
def_scoring_ranges = {'PA0': 5, 'PA1': 4, 'PA7': 3, 'PA14': 1, 'PA18': 0, 'PA28': -1, 'PA35': -3, 'PA46': -5,
                      'YA100': 5, 'YA199': 3, 'YA299': 2, 'YA349': 0, 'YA399': -1, 'YA449': -3, 'YA499': -5, 'YA549': -6, 'YA550': -7}                 
playoff_weeks = ['WK15', 'WK16', 'WK17']
flex_positions = ['RB', 'WR', 'TE']
start_by_pos = {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'D/ST': 1} 

# File Specific Globals
startpos_colors = { 'QB': 'red', 'RB1': 'darkgreen', 'RB2': 'forestgreen', 'WR1': 'darkblue',
                    'WR2': 'blue', 'TE': 'gold', 'FLEX': 'silver', 'K': 'purple', 'D/ST': 'navy'}
weight_of_def_factor = 0.4
nfl_schedule_dict = fdi.import_nfl_schedule_dict(file_path_dict, 'all')

stats = []
for key in scoring_rules:
    stats.append(key)

# For Debugging
debug_mode = False
debug_player = 'Player Name Here'

# Utility Functions
def create_agg_dict(keys, function):
    '''
    keys is a list and function is a string. Create a dictionary containing key:function for each key to be used for aggregate functions. Returns dictionary.
    
    Args:
        keys (list): keys for dictionary
        function (str): function value for dictionary
        
    Returns:
        dictionary: formatted {key: function}
    '''
    dict = {}
    for key in keys:
        dict[key] = function
    return dict
def convert_yes_no(input):
    '''
    Convert user input like y or yes to YES, n or no to NO. Returns string.
    
    Args:
        input (str): user input
        
    Returns:
        str: 'YES' or 'NO
    '''
    if (input.upper() == 'Y' | input.upper() == 'YES'):
        input = 'YES'
    if (input.upper() == 'N' | input.upper() == 'NO'):
        input = 'NO'
    return input

# Function to produce a graph of FPTS_CLASS by team with bars color coded by position
def run_graph_fptsclass_by_team_and_position():
    '''
    Generate and show a graph of player data FPTS_CLASS broken down by fantasy owner and position.
    '''
    global teams
    global positions
    global all_weeks
    global startpos_colors
    global na_val
    global owners_for_manual_correction
    global start_by_pos
    global flex_positions
    global file_path_dict

    # Cut down the full team data dataframe
    player_data = fdi.import_full_team_data('all_valid', file_path_dict)
    #print('add fpts class')
    player_data = fdi.add_FPTS_CLASS(player_data)
    player_data['FPTS_CLASS'] = player_data['FPTS_CLASS'].astype(float)

    # Add the OWNER column
    player_data = fdi.add_OWNER(player_data, file_path_dict, owners_for_manual_correction, pull_mapping_from_df=True)

    # Aggregate the data using sum of FPTS and FPTS_CLASS
    player_totals = player_data.groupby(['PLAYER', 'POS', 'OWNER']).agg({'FPTS': 'sum', 'FPTS_CLASS': 'sum'})
    player_totals = player_totals.reset_index().sort_values('FPTS_CLASS', ascending=False).reset_index(drop=True)


    # Remove any FA entries not on a team
    player_totals = player_totals[player_totals['OWNER'] != 'FA']
    player_totals = player_totals.dropna(subset='OWNER').reset_index(drop=True)

    # Add starter info columns based on OWNER and FPTS/FPTS_CLASS
    player_totals = fdi.add_STARTER_and_STARTPOS(player_totals, start_by_pos=start_by_pos, flex_positions=flex_positions)

    # Filter to only starters
    player_totals = player_totals[player_totals['STARTER']]

    # Prep for graphing, pivot so we graph a value for each position
    pivoted_totals = player_totals.pivot(index='OWNER', columns='STARTPOS', values=['FPTS_CLASS', 'FPTS'])

    # Initialize objects for graphing
    start_positions = ['QB', 'RB1', 'RB2', 'WR1', 'WR2', 'TE', 'FLEX', 'K', 'D/ST']
    bottom = False
    fig, ax = plt.subplots()

    for pos in start_positions:
        if isinstance(bottom, bool):
            rects = ax.bar(x=pivoted_totals.index, height=pivoted_totals[('FPTS_CLASS', pos)], color=startpos_colors[pos], label=pos)
            bottom = pivoted_totals[('FPTS_CLASS', pos)]
        else:
            rects = ax.bar(x=pivoted_totals.index, height=pivoted_totals[('FPTS_CLASS', pos)], color=startpos_colors[pos], bottom=bottom, label=pos)
            bottom = bottom + pivoted_totals[('FPTS_CLASS', pos)]

    ax.set_xlabel('FFL Team Owner')
    ax.set_ylabel('Player Value')
    ax.set_title('FFL Power Rankings Breakdown by Position')
    ax.legend(loc='upper right', fontsize='xx-small')
    plt.show()

# Functions for team projections
def calculate_player_stat_wavg(all_weeks_data, last_three_data, stats):
    '''
    Assumes last_three_data is a slice of all_weeks_data. Calculates the mean stat for each player all inputted stats in the two dataframes, then calculates an average
    of each stat for each player. Formula: (mean(all_weeks) + mean(last_three)) / 2. Returns a dataframe.
    
    Args:
        all_weeks_data (pd.DataFrame): all weeks of player data
        last_three_data (pd.DataFrame): last three weeks of player data
        stats (list): list of stats to aggregate
        
    Returns:
        pd.DataFrame: agrregated averages of player stats
    '''
    agg_dict = create_agg_dict(stats, 'mean')
    
    all_weeks_aggregate = all_weeks_data.groupby(['PLAYER', 'POS', 'OWNER']).agg(agg_dict)
    three_weeks_aggregate = last_three_data.groupby(['PLAYER', 'POS', 'OWNER']).agg(agg_dict)
    player_scores = all_weeks_aggregate.merge(three_weeks_aggregate, on=['PLAYER', 'POS', 'OWNER'], how='outer', suffixes=('_ALL', '_L3'))
    player_scores = player_scores.fillna(-200)
    # Naming new columns with plain stat name to match stats global
    # If _L3 is NaN use only _ALL value
    
    for stat in stats:
        player_scores[stat] = player_scores.apply((lambda row: ((row[stat+'_ALL'] + row[stat+'_L3']) / 2) if row[stat+'_L3'] != -200 else row[stat+'_ALL']), axis=1)
        player_scores = player_scores.drop([(stat+'_ALL'), (stat+'_L3')], axis=1)
    
    return player_scores
def calculate_opp_stat_wavg(all_weeks_data, last_three_data, stats):
    '''
    Assumes last_three_data is a slice of all_weeks_data. Calculates the sum stat grouped by position, opponent, and week, then mean across weeks, grouping by position and opponent
    for all inputted stats in the two dataframes. Summarizes by averaging the values in both dataframes. Formula: (mean(all_weeks) + mean(last_three)) / 2. Returns a dataframe.
    
    Args:
        all_weeks_data (pd.DataFrame): all weeks of player data
        last_three_data (pd.DataFrame): last three weeks of player data
        stats (list): list of stats to aggregate
        
    Returns:
        pd.DataFrame: aggregated averages of stats vs. opponent by position
    '''
    global na_val

    mean_dict = create_agg_dict(stats, 'mean')
    sum_dict = create_agg_dict(stats, 'sum')
    
    # Note: bye weeks should be a non-issue here, teams not listed as opponents, does not count against mean
    # Drop any rows without an opponent, there shouldn't be any
    all_weeks_data = all_weeks_data.drop(all_weeks_data[all_weeks_data['OPPONENT'] == na_val].index)
    last_three_data = last_three_data.drop(last_three_data[last_three_data['OPPONENT'] == na_val].index)

    # Sum for each opponent, position, week
    all_weeks_totals = all_weeks_data.groupby(['OPPONENT', 'POS', 'WEEK']).agg(sum_dict)
    last_three_totals = last_three_data.groupby(['OPPONENT', 'POS', 'WEEK']).agg(sum_dict)

    # Average for each opponent, position
    all_weeks_average = all_weeks_totals.groupby(['OPPONENT', 'POS']).agg(mean_dict)
    last_three_average = last_three_totals.groupby(['OPPONENT', 'POS']).agg(mean_dict)

    # Merge the dataframes
    opponent_scores = all_weeks_average.merge(last_three_average, on=['OPPONENT', 'POS'], how='inner', suffixes=('_ALL', '_L3'))

    # Average all_weeks and last_three, then drop the old columns
    for stat in stats:
        opponent_scores[stat] = (opponent_scores[stat+'_ALL'] + opponent_scores[stat+'_L3']) / 2
        opponent_scores = opponent_scores.drop([(stat+'_ALL'), (stat+'_L3')], axis=1)
    return opponent_scores
def calculate_def_factor(opp_stats, stats):
    '''
    Calculate the defense factor for each stat. 
    def_factor(opp, pos) = ((stat(opp, pos) - min(stat(pos))) / (mean(stat(pos)) - min(stat(pos)))) - 1
    
    Args:
        opp_stats (pd.DataFrame): output of calculate_opp_stat_wavg
        stats (list): list of stats in opp_stats
        
    Returns:
        dictionary: {OPPONENT: {POS: {STAT: factor}}}
    '''
    global positions

    mean_min_dict = {}
    for pos in positions:
        pos_only = opp_stats.loc[opp_stats['POS'] == pos]
        for stat in stats:
            mean = pos_only[stat].mean()
            min = pos_only[stat].min()
            if stat in mean_min_dict.keys():
                mean_min_dict[stat][pos] = [mean, min]
            else:
                mean_min_dict[stat] = {pos: [mean, min]}
    # def_factor dict format - {OPPONENT: {POS: {STAT: factor}}}     
    def_factor_dict = {}
    for index, row in opp_stats.iterrows():
        for stat in stats:
            mean = mean_min_dict[stat][row['POS']][0]
            min = mean_min_dict[stat][row['POS']][1]
            
            if (mean==0):
                factor = 0
            else:
                factor = ((row[stat] - min) / (mean - min)) - 1
            
            if row['OPPONENT'] in def_factor_dict.keys():
                if row['POS'] in def_factor_dict[row['OPPONENT']].keys():
                    def_factor_dict[row['OPPONENT']][row['POS']][stat] = factor  
                else:
                    def_factor_dict[row['OPPONENT']][row['POS']] = {stat: factor}
            else:
                def_factor_dict[row['OPPONENT']] = {row['POS']: {stat: factor}}

            
    return def_factor_dict
def process_all_weeks_data(all_weeks_data, debug_mode=False, debug_player=False):
    '''
    Process all_weeks_data, add in any missing player rows, drop players without owner, drop dnp weeks, 
    fill in entries without opponents, drop any new bye week entries, convert stat columns to floats.
    Returns dataframe.
    
    Args:
        all_weeks_data (pd.DataFrame): all weeks of player data
        debug_mode (bool, optional): set to True for more verbose debugging output
        debug_player (str or bool, optional): use with debug_mode, set to a string player's name to output debug data for this player
        
    Returns:
        pd.DataFrame: post-processing all_weeks_data
    '''
    global scoring_rules
    global nfl_schedule_dict
    global file_path_dict

    # Process all_weeks_data, drop players without owner, drop dnp weeks
    all_weeks_data = fdi.add_missing_player_rows(all_weeks_data, file_path_dict)
    if debug_mode:
        print('After add missing: ')
        print(all_weeks_data[all_weeks_data['PLAYER'] == debug_player])
    
    all_weeks_data = fdi.add_OWNER(all_weeks_data, file_path_dict, pull_mapping_from_df=True)
    if debug_mode:
        print('After add owner: ')
        print(all_weeks_data[all_weeks_data['PLAYER'] == debug_player])
    
    all_weeks_data = all_weeks_data.drop(all_weeks_data[(all_weeks_data['TEAM'] == 'FA') | (all_weeks_data['BYE'].astype(bool)) | (all_weeks_data['OUT'].astype(bool))].index)
    if debug_mode:
        print('After drop FA/BYE: ')
        print(all_weeks_data[all_weeks_data['PLAYER'] == debug_player])
    
    # Fill in entries without opponents, drop any new bye week entries
    all_weeks_data['OPPONENT'] = all_weeks_data.apply(lambda row: nfl_schedule_dict[row['TEAM']][row['WEEK']] if row['OPPONENT'] == 0 else row['OPPONENT'], axis=1)
    all_weeks_data = all_weeks_data.drop(all_weeks_data[all_weeks_data['OPPONENT'] == 'BYE'].index)

    # Convert columns for averages
    for key in scoring_rules:
        all_weeks_data[key] = all_weeks_data[key].astype(float)
    return all_weeks_data
def calculate_player_projections(player_stats, def_factor_dict, weight_of_def_factor, verbose=False):
    '''
    Calculate player projected score each week by projecting stats using the weighted average with a defense factor, then multiplying by scoring rules.
    Returns a dataframe. 

    Args:
        player_stats (pd.DataFrame): output of calculate_player_stat_wavg
        def_factor_dict (dict): output of calculate_def_factor
        wieght_of_def_factor (float): between 0 and 1, influence of opponent defense on player projections
        verbose (bool, optional): set to True for a more verbose output
        
    Returns:
        pd.DataFrame: projected player data for future weeks
    
    '''
    global future_weeks
    global nfl_schedule_dict

    projections_df = pd.DataFrame(columns=player_stats.columns)
    proj_df_index = 0
    for week in future_weeks:
        if verbose:
            print('Calculating ',week,'...')
        for index, row in player_stats.iterrows():
            # Handle bye weeks by skipping them - no rows for bye week data in projections_df, owners will not start a player on bye
            opponent = nfl_schedule_dict[row['TEAM']][week]
            if opponent == 'BYE':
                continue

            projections_df.loc[proj_df_index, ['PLAYER', 'TEAM', 'POS', 'OWNER', 'WEEK']] = [row['PLAYER'], row['TEAM'], row['POS'], row['OWNER'], week]
            projections_df.loc[proj_df_index, 'OPPONENT'] = opponent
    
            proj_pts_sum = 0
            for stat in stats:
                def_factor = def_factor_dict[opponent][row['POS']][stat]
                player_prev = row[stat]
                proj_stat = player_prev * (1 + (def_factor * weight_of_def_factor))
                projections_df.loc[proj_df_index, stat] = proj_stat
                proj_pts_sum = proj_pts_sum + proj_stat * scoring_rules[stat]
            
            projections_df.loc[proj_df_index, 'PROJ_FPTS'] = proj_pts_sum
            proj_df_index += 1
    return projections_df
def calculate_weekly_final_scores(projections_df):
    '''
    Sums projected scores for owners across starting players. Returns dictionary formatted {OWNER: {WEEK: {'PTS': PROJ_FPTS}}}
    
    Args:
        projections_df (pd.DataFrame): output of calculate_player_projections
        
    Returns:
        dictionary: {OWNER: {WEEK: {'PTS': PROJ_FPTS}}}
    
    '''
    global future_weeks
    global start_by_pos
    global flex_positions

    # proj_final_score_dict - {OWNER: {WEEK: {'PTS': PROJ_FPTS}}}
    proj_final_score_dict = {}
    for week in future_weeks:
        week_data = projections_df.loc[projections_df['WEEK'] == week]
        week_data = week_data.copy()
        week_data = fdi.add_STARTER_and_STARTPOS(week_data, ['PROJ_FPTS'], start_by_pos=start_by_pos, flex_positions=flex_positions)
        
        starters_only = week_data[week_data['STARTER']]

        sums = starters_only.groupby('OWNER').agg({'PROJ_FPTS': 'sum'})
        
        for index, row in sums.iterrows():
            if index in proj_final_score_dict.keys():
                proj_final_score_dict[index][week] = {'PTS': row['PROJ_FPTS']}
            else:
                proj_final_score_dict[index] = {week: {'PTS': row['PROJ_FPTS']}}
    
    return proj_final_score_dict
def add_matchup_result_info(proj_final_score_dict):
    '''
    Adds matchup result and point differential to proj_final_score_dict in the OWNER, WEEK, RESULT and OWNER, WEEK, DIFF nodes. Returns updated dictionary.
    
    Args:
        proj_final_score_dict (dict): output of calculate_weekly_final_scores
        
    Returns:
        dictionary: {OWNER: {WEEK: {'PTS': proj_fpts, 'RESULT': matchup_result, 'DIFF': point_differential}}}
    
    '''
    global playoff_weeks
    global file_path_dict

    matchups_df = fdi.import_owner_matchups(file_path_dict)
    for owner, value1 in proj_final_score_dict.items():
        for week, value2 in value1.items():
            if week in playoff_weeks:
                continue
            if 'RESULT' in proj_final_score_dict[owner][week].keys():
                continue    # Result has already bee added
            score = np.round(value2['PTS'], 2)
            opponent = matchups_df.loc[owner, week]
            opponent_score = np.round(proj_final_score_dict[opponent][week]['PTS'], 2)
            diff = score - opponent_score

            proj_final_score_dict[owner][week]['DIFF'] = diff
            proj_final_score_dict[opponent][week]['DIFF'] = diff * -1

            if score > opponent_score:
                proj_final_score_dict[owner][week]['RESULT'] = 'W'
                proj_final_score_dict[opponent][week]['RESULT'] = 'L'
            elif score == opponent_score:
                proj_final_score_dict[owner][week]['RESULT'] = 'T'
                proj_final_score_dict[opponent][week]['RESULT'] = 'T'
            else:
                proj_final_score_dict[owner][week]['RESULT'] = 'L'
                proj_final_score_dict[opponent][week]['RESULT'] = 'W'

    return proj_final_score_dict
def project_final_standings(proj_final_score_dict):
    '''
    Add matchup result info to an import of the current standings. Returns dataframe of projected standings.
    
    Args:
        proj_final_score_dict (dict): output of add_matchup_result_info
        
    Returns:
        pd.DataFrame: projected final standings
    '''
    global file_path_dict

    standings = fdi.import_current_standings(file_path_dict)
    for owner, value1 in proj_final_score_dict.items():
        wins_to_add = 0
        losses_to_add = 0
        ties_to_add = 0
        pts_to_add = 0
        for week, value2 in value1.items():
            if week in playoff_weeks:
                continue  # There are projected points for these weeks but no results
            #print(owner, " ", week)
            #print(value2)
            if value2['RESULT'] == 'W':
                wins_to_add += 1
            elif value2['RESULT'] == 'L':
                losses_to_add += 1
            else:
                ties_to_add += 1
            pts_to_add += value2['PTS']
        # add these values to the current standings
        standings.loc[owner, 'WINS'] = standings.loc[owner, 'WINS'] + wins_to_add
        standings.loc[owner, 'TIES'] = standings.loc[owner, 'TIES'] + ties_to_add
        standings.loc[owner, 'LOSSES'] = standings.loc[owner, 'LOSSES'] + losses_to_add
        standings.loc[owner, 'PTS'] = np.round((standings.loc[owner, 'PTS'] + pts_to_add), 2)
    
    standings_sorted = standings.sort_values(by=['WINS', 'TIES', 'PTS'], ascending=[False, False, False])

    return standings_sorted
def run_imports_cleaning_and_player_projections(drop_ffl_fa_players=False):
    '''
    Imports all_weeks_data, cleans it, projects player stats and scores in future weeks. Returns projections_df, def_factor_dict

    Args:
        drop_ffl_fa_players (bool, optional): if True, players without a listed ffl owner are dropped. 
        
    Returns:
        pd.DataFrame: player projections for future weeks
        dictionary: {OPPONENT: {POS: {STAT: factor}}}
    '''
    global debug_mode
    global valid_weeks
    global weight_of_def_factor
    global stats

    # -- Initial Imports and Data Cleaning--
    print('Running initial imports...')
    # Imports 
    player_team_map = fdi.import_nfl_team_pos_mappings()
    all_weeks_data = fdi.import_full_team_data('all_valid')

    if debug_mode:
        print('Before: ')
        print(all_weeks_data[all_weeks_data['PLAYER'] == debug_player])

    # Process all_weeks_data
    all_weeks_data = process_all_weeks_data(all_weeks_data)

    if debug_mode:
        print('After processing: ')
        print(all_weeks_data[all_weeks_data['PLAYER'] == debug_player])

    # Slice out the last three weeks only
    last_three_data = all_weeks_data.loc[all_weeks_data['WEEK'].isin(valid_weeks[len(valid_weeks)-3:])]

    # -- Player Projection Calculations --
    print('Running projection calculations...')

    # Return a weighted average dataframe one row per player
    player_stats = calculate_player_stat_wavg(all_weeks_data, last_three_data, stats)
    player_stats = player_stats.reset_index()

    if debug_mode:
        print('After aggregating: ')
        print(player_stats[player_stats['PLAYER'] == debug_player])

    # Drop players not on current rosters for efficiency
    if drop_ffl_fa_players:
        player_stats = player_stats.drop(player_stats[(player_stats['OWNER'] == 'FA') | (player_stats['OWNER'] == 0)].index)

    if debug_mode:
        print('After dropping FFL free agents: ')
        print(player_stats[player_stats['PLAYER'] == debug_player])

    # Add column for most recent NFL team mapping to be used for projections
    player_stats['TEAM'] = player_stats.apply(lambda row: player_team_map[row['PLAYER']][0], axis=1)

    # Return a weighted average dataframe one row per team, pos pair 
    opp_stats = calculate_opp_stat_wavg(all_weeks_data, last_three_data, stats)
    opp_stats = opp_stats.reset_index()

    # Return a dictionary of def_factors formatted {OPPONENT: {POS: {STAT: factor}}}
    def_factor_dict = calculate_def_factor(opp_stats, stats)

    # Sanity check on def factors summing to ~ 0
    for stat in stats:
        for pos in positions:
            sum = 0
            for opponent, value1 in def_factor_dict.items():
                sum += value1[pos][stat]
            assert (sum < 0.00001) & (sum > -0.00001)

    # Project player scores by week in PROJ_FPTS
    projections_df = calculate_player_projections(player_stats, def_factor_dict, weight_of_def_factor, verbose=False)
    return projections_df, def_factor_dict
def run_final_standings_projections():
    '''
    Run final_standings_projections functionality and show a table graphic of the final standings. 
    '''
    global debug_mode
    global valid_weeks
    global weight_of_def_factor
    global stats
    global file_path_dict

    projections_df = run_imports_cleaning_and_player_projections(drop_ffl_fa_players=True) 

    # -- Calculate FFL Matchup Results --
    # Project final scores by team for each week in proj_final_score_dict formatted {OWNER: {WEEK: {'PTS': proj_fpts}}
    proj_final_score_dict = calculate_weekly_final_scores(projections_df)

    # Compare owner scores to their matchup, results in {OWNER: {WEEK: {'RESULT': result}}, pt diff in {OWNER: {WEEK: {'DIFF': diff}}
    proj_final_score_dict = add_matchup_result_info(proj_final_score_dict)

    # Add info from proj_final_score_dict to the current standings and sort.
    standings = project_final_standings(proj_final_score_dict)
    standings = standings.reset_index()

    #projected_additional = projections_df.groupby(['PLAYER']).agg({'PROJ_FPTS': 'sum'}) 

    fig, ax = plt.subplots()
    ax.axis('off')
    table = ax.table(cellText=standings.values, colLabels=standings.columns, loc='center')
    plt.show()

# Functions for Statistics Leaders
def run_current_statistic_leaders():
    '''
    Prompt the user for slicing inputs and return the proper slice of past player data.
    '''
    valid_positions = ['QB', 'RB', 'WR', 'TE']
    global teams
    global stats
    global valid_weeks
    global na_val
    global file_path_dict

    valid_stats = stats + ['FPTS']

    pos_list = []
    team_list = []
    week_list = []
    stat_list = []
    opponent_list = []

    print('Enter selections to filter players by. \nEnter one selection at each prompt, will re-prompt for additional selections.\nStatistic input is required. Enter at any other prompt to skip or proceed.')
    quit = False
    done = False
    first = True
    while done == False:
        if first:
            stat_input = input('Select a Statistic: ')
        else:
            stat_input = input('Select a Tiebreaker: ')
        stat_input = stat_input.upper()
        if stat_input == '':
            done = True
            if first:    
                quit = True
        elif stat_input in valid_stats:
            stat_list.append(stat_input)
            first = False
            if len(stat_list) > 1:  # Primary and tiebreaker stat at most
                done = True
        else:
            print(f'Invalid selection. Select a statistic in {valid_stats}')
    if not(quit):
        # Position
        done = False
        first = True
        while done == False:
            if first:
                pos_input = input('Filter by position: ')
            else:
                pos_input = input('And: ')
            pos_input = pos_input.upper()
            if pos_input == '':
                done = True
            elif pos_input in valid_positions:
                pos_list.append(pos_input)
                first = False
            else:
                print(f'Invalid selection. Select a position in {valid_positions}')
        # Team
        done = False
        first = True
        while done == False:
            if first:
                team_input = input('Filter by team (enter initials): ')
            else:
                team_input = input('And: ')
            team_input = team_input.upper()
            if team_input == '':
                done = True
            elif team_input in teams:
                team_list.append(team_input)
                first = False
            else:
                print('Invalid selection. Select a team like "BUF", "LAR", or "SF".')
        # Opponent
        done = False
        first = True
        while done == False:
            if first:
                opp_input = input('Filter by opponent (enter initials): ')
            else:
                opp_input = input('And: ')
            opp_input = opp_input.upper()
            if opp_input == '':
                done = True
            elif opp_input in teams:
                opponent_list.append(opp_input)
                first = False
            else:
                print('Invalid selection. Select a team like "BUF", "LAR", or "SF".')
        # Week
        done = False
        first = True
        while done == False:
            if first:
                week_input = input('Select week to return data for (default: year to date): ')
            else:
                week_input = input('And: ')
            week_input = week_input.upper()
            if week_input == '':
                done = True
            elif week_input in valid_weeks:
                week_list.append(week_input)
                first = False
            else:
                print('Invalid selection. Select a week like "WK1", "WK2".')
        # How many?
        done = False
        while done == False:
            how_many = input('How many players do you want to return? ')
            if how_many.isdigit() and int(how_many) <= 25:
                how_many = int(how_many)
                done = True
            else:
                print('Invalid selection. Enter a number 25 or less.')
        
        player_data = fdi.import_player_data('all_valid', file_path_dict)
        agg_dict = {}
        ascending_list = []
        for stat in stat_list:
            
            player_data = player_data.drop(player_data[player_data[stat] == na_val].index)
            ascending_list.append(False)
            agg_dict[stat] = 'sum'
            player_data[stat] = player_data[stat].astype(float)
        
        slice = fdi.slice_of_player_data(player_data, team_input=team_list, pos_input=pos_list, opp_input=opponent_list, weeks_input=week_list)
        
        slice_summary = slice.groupby(['PLAYER', 'POS']).agg(agg_dict)
        slice_sorted = slice_summary.sort_values(by=stat_list, ascending=ascending_list).reset_index()
        print(slice_sorted.head(how_many))        

# Driver code:
done = False
while not(done):
    print('Menu: \n1 - Current Statistical Leaders\n2 - FFL Power Rankings Graph \n3 - FFL Final Standings Projections')
    selection = input('Enter the number of an item in the menu to run: ')
    if selection == '':
        done = True
    elif selection.isdigit() and int(selection) == 1:
        run_current_statistic_leaders()
        done = True
    elif selection.isdigit() and int(selection) == 2:
        run_graph_fptsclass_by_team_and_position()
        done = True
    elif selection.isdigit() and int(selection) == 3:
        run_final_standings_projections()
        done = True
    else:
        print('Please enter a valid selection.')
