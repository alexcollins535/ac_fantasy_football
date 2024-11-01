import numpy as np
import pandas as pd
import ffl_data_importing as fdi

# Import values
weeks = fdi.valid_sheet_names
positions = fdi.positions
teams = fdi.teams
na_val = fdi.na_val

# Standard Globals
stats_w_opp_dict = {'QB': ['FPTS', 'PATD', 'PAYDS', 'RUTD', 'RUYDS'], 
                    'RB': ['FPTS', 'RUTD', 'RUYDS', 'REC', 'RETD', 'REYDS'], 
                    'WR': ['FPTS', 'RUTD', 'RUYDS', 'REC', 'RETD', 'REYDS'],
                    'TE': ['FPTS', 'REC', 'RETD', 'REYDS']}
stats_wo_opp_dict = {'QB': ['RUSH %', 'TOUCH %'], 
                    'RB': ['SNAP %', 'RUSH %', 'TGT %'], 
                    'WR': ['SNAP %', 'TOUCH %', 'TGT %'],
                    'TE': ['SNAP %', 'TOUCH %', 'TGT %']}

# Utility Functions
def process_result_weeks(result_weeks, include_result_week):
    '''
    Processes the result week inputs to add_retro_data. Returns list.
    
    Args:
        result_weeks (bool, str, or list): input to be processed
        include_result (bool): input to be processed
        
    Returns:
        list: relevant result_weeks based on inputs 
    
    '''
    global weeks

    if isinstance(result_weeks, bool):
        if include_result_week:
            result_weeks = weeks
        else:
            result_weeks = weeks[1:]
    elif isinstance(result_weeks, str):
        if include_result_week:
            result_weeks = [result_weeks]
        elif result_weeks == 'WK1':
            raise ValueError('include_result_week must be set to True if result_week is set to WK1')
        else:
            result_weeks = weeks[(weeks.index(result_weeks) - 1)]
    elif isinstance(result_weeks, list):
        # Do nothing if include_result_week is True
        if not(include_result_week):
            for index, week in enumerate(result_weeks):
                if week == 'WK1':
                    raise ValueError('include_result_week must be set to True if result_week includes to WK1')
                # Set the value to one week to the left of the 
                result_weeks[index] = weeks[(weeks.index(week) - 1)]
    return result_weeks

# Functions for creating predictive model features
def add_retro_data(df_to_add_to, ref_data=False, stat='FPTS', w_opp_data=False, span='L3', include_result_week=False, type='AVG', result_weeks=False):
    '''
    df_to_add_to is the dataframe to add columns to, ref_data is the reference dataframe to pull data from.
    Adds columns for stat average by player for previous weeks or last 3 weeks, and stat average 
    sum by player's position against this opponent (Ex: stat is points, player is a WR against NYG, we add the average total 
    points scored against NYG by WRs). Returns dataframe with additional columns. w_opp_data is a boolean determining if 
    the opponent information is also added. span is either 'L3' for last three weeks or 'ALL' for all previous weeks (process
    intensive). For average, weeks in which a player does not play (out or on bye) are not counted in the denominator.
    include_result_week is a boolean determining if "this weeks" resulting stat is included in the average. 
    result_weeks can be set to a string or list of result weeks to calculate retro data before. Use with include_result_week 

    Args:
        df_to_add_to (pd.DataFrame): dataframe to add columns to
        ref_data (bool or pd.DataFrame, optional): if included, dataframe to pull retro data from. Default: False
        stat (str, optional): column in data to calculate retro data for. Default: 'FPTS'
        w_opp_data (bool, optional): include calculation of data against opponent. More performance intensive. Default: False
        span (str, optional): 'L3' or 'ALL', calculate data over the previous 3 weeks or all previous weeks. Default: 'L3'
        include_result_week (bool, optional): include this weeks result in the calculation. False more useful for predictive modeling. Default: False
        type (str, optional): 'AVG' or 'SUM', type of calculation to return. Default: 'AVG
        result_weeks (bool, str, or list, optional): if included, result weeks to calculate data for. Default: False

    Returns:
        pd.DataFrame: dataframe with added columns
    

    '''
    if isinstance(ref_data, bool):
        ref_data = df_to_add_to.copy()
    assert (span.upper() == 'L3')|(span.upper() == 'ALL') 
    global weeks
    if w_opp_data:
        cache = {} # creating a cache for retro opponent data
    
    result_weeks = process_result_weeks(result_weeks, include_result_week)

    for result_week in result_weeks:
        prev_weeks = []
        for week in weeks:
            if week == result_week:
                if include_result_week:
                   prev_weeks.append(week) 
                break
            prev_weeks.append(week)
        # Do nothing if span is 'ALL'
        if span.upper() == 'L3':
            if len(prev_weeks) > 3:
                prev_weeks = prev_weeks[(len(prev_weeks)-3):]
            
        rel_ref_data = ref_data[ref_data['WEEK'] == result_week]
        retro_data = ref_data[ref_data['WEEK'].isin(prev_weeks)]
        
        # Do this for every player with a value where week is result_week
        for index, row in rel_ref_data.iterrows():
            opp =  row['OPPONENT']
            if opp == 'BYE WEEK': 
                continue    # We don't care about predicting values for players on BYE
            player = row['PLAYER']
            pos = row['POS']
            player_avg_prev = get_player_avg(retro_data, player, stat, prev_weeks, type)
            df_to_add_to.loc[index, (type.upper()+span.upper()+"_"+stat.upper())] = player_avg_prev
            if w_opp_data:
                # Key order for cache: result_week, opp, pos
                if result_week in cache.keys():
                    if opp in cache[result_week].keys():
                        if pos in cache[result_week][opp].keys():
                            opp_avg_prev = cache[result_week][opp][pos]
                        else:
                            opp_avg_prev = get_pos_sum_avg_v_opp(retro_data, pos, opp, stat, type)
                            cache[result_week][opp][pos] = opp_avg_prev
                    else:
                        opp_avg_prev = get_pos_sum_avg_v_opp(retro_data, pos, opp, stat, type)
                        cache[result_week][opp] = {pos: opp_avg_prev}
                else:
                    opp_avg_prev = get_pos_sum_avg_v_opp(retro_data, pos, opp, stat, type)
                    cache[result_week] = {opp: {pos: opp_avg_prev}}       
                
                opp_avg_prev = get_pos_sum_avg_v_opp(retro_data, pos, opp, stat, type)
                df_to_add_to.loc[index, ('OPP'+type.upper()+span.upper()+"_"+stat.upper())] = opp_avg_prev
                    
    return df_to_add_to
def get_pos_sum_avg_v_opp(retro_data, position, opponent, stat, type):
    '''
    Calculate the average sum of a stat (FPTS, PATD, RUYDS, etc.) across players of a given position 
    against a certain opponent. Assumes non-relevant data is filtered out of retro_data (weeks that
    would not yet be available). Returns rounded float. type is AVG or SUM to determine type of output.
    
    Args:
        retro_data (pd.DataFrame): dataframe containing previous weeks data
        position (str): position to calculate stat for
        opponent (str): opponent to calculate stat for
        stat (str): stat to calculate
        type (str): 'AVG' or 'SUM', what to calculate
        
    Returns:
        float: calculation of previous stat for position against opponent 
    '''
    assert position in positions
    assert opponent in teams
    assert stat in retro_data.columns
    if not(isinstance(retro_data[stat], float)):
        retro_data.loc[:,stat] = retro_data.loc[:,stat].astype(float)
    rel_subset = retro_data[(retro_data['POS'] == position) & (retro_data['OPPONENT'] == opponent)]
    summary = rel_subset.groupby(by='WEEK')[stat].sum()
    if type == 'AVG':
        value = summary.mean()
    else:
        value = summary.sum()
    return np.round(value, 2)
def get_player_avg(retro_data, player, stat, weeks, type):
    '''
    Calculate the average of a stat (FPTS, PATD, RUYDS, etc.) for a player, factoring out weeks the player
    was out injured or on bye. Assumes non-relevant data is filtered out of retro_data (weeks that would 
    not yet be available). Returns rounded float. type is AVG or SUM to determine type of output.
    
    Args:
        retro_data (pd.DataFrame): dataframe containing previous weeks data
        player (str): player to calculate stat for
        stat (str): stat to calculate
        weeks (str): weeks to calculate stat for
        type (str): 'AVG' or 'SUM', what to calculate
        
    Returns:
        float: calculation of previous stat for position against opponent 
    '''
    assert stat in retro_data.columns
    if not(isinstance(retro_data[stat], float)):
        retro_data.loc[:,stat] = retro_data.loc[:,stat].astype(float)
    rel_subset = retro_data[retro_data['PLAYER'] == player]
    #rel_subset.loc[:,stat] = rel_subset.loc[:,stat].astype(float)
    player_status = fdi.import_player_status(weeks)
    try: 
        player_status = player_status[player_status['PLAYER'] == player]
    except:
        raise ValueError(f'Error when player = {player}, weeks = {weeks}')

    # If player is listed in player status (was out), remove those weeks from denominator
    if type == 'SUM':
        value = rel_subset[stat].sum()
    else:
        if player_status.empty:
            num = rel_subset[stat].sum()
            denom = len(weeks)
        else:
            num = rel_subset[stat].sum()
            denom = len(weeks) - player_status['WEEK'].nunique()
        
        if denom != 0:
            value = num / denom
        else:
            value = 0
    return np.round(value)
def import_model_data(pos):
    '''
    Import data set with engineered retro features for a specific position (pos). Features vary by position.
    Returns dataframe.

    Args:
        pos (str): position to import model data for
        
    Returns:
        pd.DataFrame: model data     
    '''
    global stats_w_opp_dict
    global stats_wo_opp_dict
    global positions
    
    assert pos in positions

    print('Importing player data...')
    player_stats = fdi.import_player_with_util_data('all_valid')
    ref_data = player_stats[player_stats['POS'] == pos]
    model_data = ref_data.loc[(ref_data['WEEK'] != 'WK1'), ['PLAYER', 'TEAM', 'POS', 'WEEK', 'OPPONENT', 'FPTS']]
    stats_to_add_w_opp = stats_w_opp_dict[pos]
    stats_to_add_wo_opp = stats_wo_opp_dict[pos]

    for stat in stats_to_add_w_opp:
        print(f'Adding {stat} retro data...')
        model_data = add_retro_data(model_data, ref_data, stat, w_opp_data=True, span='L3')
    for stat in stats_to_add_wo_opp:
        print(f'Adding {stat} retro data...')
        model_data = add_retro_data(model_data, ref_data, stat, w_opp_data=False, span='L3')
    # Drop off players without FPTS data
    model_data = model_data.dropna(subset=['FPTS'])
    # Add FPTS_CLASS to be used as a target variable
    model_data = add_FPTS_CLASS(model_data)
    return model_data

