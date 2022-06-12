import numpy as np
import pandas as pd
import pymongo
from textwrap import dedent

client = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = client["setlists"]

def get_user_input(db):
    collections = db.list_collection_names()
    print("Following collections found. Please confirm which artist you'd like to analyze:")
    for idx, artist in enumerate(collections):
        print('{}: {}'.format(idx+1,artist))
    print('-' * 50)
    user_choice = input('Enter the number associated with your choice: ')

    return collections[int(user_choice)-1]

def build_df(mycol):
    """
    Accepts Collection name as function and retrieves all non-null setlists
    Returns sparse matrix of songs + n_grams as DataFrame to be passed to analysis function
    """

    results = mycol.find({"setlist.1": {"$exists": "true"}})

    # initialize empty dictionary
    df_dict = {}

    # build unique column names
    for show in results:
        setlist = show['setlist']
        columns = []
        for idx, song in enumerate(setlist):
            columns.append(song.lower().replace(' ','_'))
            if idx == 0:
                to_return = 'null__' + song.lower().replace(' ','_')
                columns.append(to_return)
            elif idx == len(setlist) - 1:
                prev_song = setlist[idx-1].lower().replace(' ','_') + '__' + song.lower().replace(' ','_')
                columns.append(prev_song)
                end_set = song.lower().replace(' ','_') + '__null'
                columns.append(end_set)
            else:
                to_return = setlist[idx-1].lower().replace(' ','_') + '__' + song.lower().replace(' ','_')
                columns.append(to_return)

        # create dictionary for specific set and add to larger dictionary to be written to DF
        row_add = {col:1 for col in columns}
        df_dict[show['id']] = row_add

    # write dictionary of dictionaries to DF and replace NaN values with 0
    df = pd.DataFrame.from_dict(df_dict, orient = 'index')
    df.fillna(0, inplace = True)
    df.rename_axis('show_id', inplace = True)
    df.reset_index(inplace = True)

    return df

def compare_series(a,b):
    """
    Accepts two series as arguments
    Returns similarity_score, defined as number of duplicates divided by number of hits
    """
    result = a.add(b)
    num_twos = 0
    num_hits = 0
    for item in result:
        if item == 2:
            num_twos += 1
            num_hits += 1
        elif item == 1:
            num_hits += 1

    return float(num_twos / num_hits)

#mycol = get_user_input()
def run_analysis(db):
    """
    Core analysis function.
    """

    collection = get_user_input(db)
    mycol = db[collection]

    df = build_df(mycol)
    df['most_similar_show'] = np.NaN
    df['similarity_score'] = np.NaN

    for idx, row in df.iterrows():

        if idx+1 == len(df):
            continue
        else:
            # Create new temporary DF and drop canonical row, as well as all prior rows
            temp_df = df.copy(deep=True)
            temp_df = temp_df[temp_df.index > idx]
            #temp_df.drop(idx, axis = 0, inplace = True)
            temp_df.drop('show_id', axis = 1, inplace = True)

            holdout = row.drop(labels = ['show_id'])
            temp_df['similarity_score'] = temp_df.apply(lambda x: compare_series(x,holdout), axis = 1)

            most_similar_show = temp_df[['similarity_score']].idxmax()
            similarity_score = temp_df['similarity_score'].loc[most_similar_show]

            df.at[idx,'most_similar_show'] = most_similar_show
            df.at[idx, 'similarity_score'] = similarity_score

            print('Similarities computed for row {}. Scanned {} rows.'.format(idx,temp_df.shape[0]))


    # WILL OMIT - JUST USING BECAUSE THERE ARE GRATEFUL DEAD DUPLICATES/ERRORS AND I'M CURIOUS
    #df.drop(df[df['similarity_score'] == 1.0].index, inplace = True)

    most_similar_shows_in_corpus = df[['similarity_score']].idxmax()
    primary_show = df['show_id'].loc[most_similar_shows_in_corpus].item()
    secondary_show_idx = int(df['most_similar_show'].loc[most_similar_shows_in_corpus].item())
    secondary_show = df['show_id'].loc[secondary_show_idx]
    similarity_score = df['similarity_score'].loc[most_similar_shows_in_corpus].item()

    primary_show_result = mycol.find({"id" : primary_show})
    secondary_show_result = mycol.find({"id" : secondary_show})

    # Display results
    print('-'*50)
    print('Most similar shows: {} and {}'.format(primary_show,secondary_show))
    print('-'*50)
    # Display primary show
    for result in primary_show_result:
        to_display = """
        Date: {}
        Location: {}, {}, {}, {}
        Setlist: {}
        """.format(result['event_date'],
                   result['venue_name'],result['venue_city'],result['venue_state'],result['venue_country'],
                   result['setlist'])

        print(dedent(to_display))
        print('-'*50)
    # Display secondary show
    for result in secondary_show_result:
        to_display = """
        Date: {}
        Location: {}, {}, {}, {}
        Setlist: {}
        """.format(result['event_date'],
                   result['venue_name'],result['venue_city'],result['venue_state'],result['venue_country'],
                   result['setlist'])

        print(dedent(to_display))
        print('-'*50)
    # Display similary score
    print('Similary score: {}'.format(similarity_score))
    print('-'*50)

run_analysis(mydb)
