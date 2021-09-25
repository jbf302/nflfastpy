import codecs
import numpy as np
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'

def convert_to_gsis_id(new_id):
    """
    Convert new player id columns to old gsis id
    """
    if type(new_id) == float:
        return new_id

    return codecs.decode(new_id[4:-8].replace('-', ''), "hex").decode('utf-8')


def agg_stats(pbp, by_team=True):

    list_of_teams = ['ARI', 'ATL', 'BAL', 'BUF', 'CAR', 'CHI', 'CIN', 'CLE', 'DAL', 'DEN', 'DET',
                     'GB', 'HOU', 'IND', 'JAX', 'KC', 'LAC', 'LA', 'LV', 'MIA', 'MIN', 'NE', 'NO',
                     'NYG', 'NYJ', 'PHI', 'PIT', 'SEA', 'SF', 'TB', 'TEN', 'WAS']

# https://github.com/nflverse/nflfastR/blob/master/R/aggregate_game_stats.R
    # output is a df inclluding the following columns:
    #     - team
    #     #passing
    #     - completions
    #     - attempts
    #     -passing yards
    #     -passing tds
    #     -ints
    #     -passing yards
    #     -sacks
    #     sack yards
    #     sack fumbles
    #     sack fumbles lost

    #     #for future air yard analysis
    #     passing air yards (qb)
    #     passing yac (qb)

    #     # doesn't penalize qb for receiver fumbles
    #     passing epa

    #     #rushing_yards

    #     - carries
    #     - rushing yards
    #     - rushing tds
    #     - rushing fumbles
    #     - rushing fumbles lost
    #     - rushing epa

    #     # receptions

    #     - targets
    #     - receiving yards
    #     - receving tds
    #     - r air yards
    #     - r yac
    #     - r fumbles
    #     - r fumbles lost        -

    ## filter to regular season games
    ## TODO: function argument to allow for postseason play

    pbp_df = pbp[pbp['season_type'] == "REG"]

    ####### PASSING STATS

    ## from pbp_df take only passing plays (filter out PENALTY, PAT2's)
    pass_pbp_df = pbp_df[(pbp_df['play_type_nfl'] == 'PASS') | (pbp_df['play_type_nfl'] == 'SACK')].copy()

    # Calculate additional stats from pbp data

    # sack fumbles (QB specific stat)
    sack_fumbles = pass_pbp_df.apply(
        lambda row: sack_fumble_calculator(row['sack'], row['fumble_lost']), axis=1).copy()
    
    # yards lost on a sack
    sack_yards_lost = pass_pbp_df.apply(
        lambda row: calc_sack_yards(row['sack'], row['yards_gained']), axis=1).copy()

    pass_pbp_df['sack_fumbles_lost'] = sack_fumbles
    pass_pbp_df['sack_yards'] = sack_yards_lost

    ## TODO: function argument to allow for grouping by player
    ## if by_team = False: .groupby(player_id)
    ## will require a player id -> name reindex

    passing_stats_to_aggregate = ['passing_yards', 'air_yards', 'pass_touchdown', 'interception', 'complete_pass', 'pass_attempt', 'epa',
                                'qb_epa', 'comp_air_epa', 'comp_yac_epa', 'air_epa', 'yac_epa', 'first_down_pass', 'sack', 'sack_fumbles_lost', 'sack_yards']

    # create passing stats df, collecting 
    pass_stats_df = pass_pbp_df.groupby(['posteam']).agg(pass_agg_func(passing_stats_to_aggregate))

    pass_stats_df.rename(columns={'sack': 'sacks_taken', 'pass_attempt': 'drop_backs', 'complete_pass': 'completions',
                                  'first_down_pass': 'pass_first_down', 'pass_touchdown': 'passing_tds'}, inplace=True)
    
    pass_stats_df['pass_attempts'] = pass_stats_df.drop_backs - pass_stats_df.sacks_taken
    pass_stats_df['net_passing_yards'] = pass_stats_df.passing_yards + pass_stats_df.sack_yards

    # net yards per passing play
    pass_stats_df['net_yards_pp'] = pass_stats_df.net_passing_yards / pass_stats_df.drop_backs

    ####### RUSHING STATS
    ## TODO
    ####### RECIVING STATS
    ## TODO
    ####### SPECIAL TEAMS STATS
    ## TODO
    
    ####### MERGE STAT DFs
    ## TODO

    return pass_stats_df # returning passing stats for now


####### HELPER FUNCTIONS
# functions in this section are applied to df's to help calculate stats

# helper function to calculate if there was a sack + fumble on pbp data
def sack_fumble_calculator(sack, fumble):
    sack_fumble = 0
    if ((sack == 1) & (fumble == 1)):
        sack_fumble = 1
    return sack_fumble

# helper function to calc QB net yards if there was a sack on pbp data
def calc_sack_yards(sack, yards):
    if (sack == 1):
        return yards

def pass_agg_func(stats_to_aggregate):
    agg_dict = {stats_to_aggregate[i]: 'sum' for i in range(0, len(stats_to_aggregate))}
    return agg_dict