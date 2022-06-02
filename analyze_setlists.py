import numpy as np
import pandas as pd
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = client["setlists"]

def get_user_input():
    collections = mydb.list_collection_names()
    print("Following collections found. Please confirm which artist you'd like to analyze:")
    for idx, artist in enumerate(collections):
        print('{}: {}'.format(idx+1,artist))
    print('-' * 25)
    user_choice = input('Enter the number associated with your choice: ')

    return collections[int(user_choice)-1]

def build_df(db,collection):
    """
    Accepts DB name as function and retrieves all non-null setlists
    Returns sparse matrix of songs + n_grams as DataFrame to be passed to analysis function
    """

    mycol = db[collection]
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
df = build_df(mydb, 'king_gizzard_&_the_lizard_wizard')
df['most_similar_show'] = np.NaN
df['similarity_score'] = np.NaN

for idx, row in df.iterrows():

    if idx+1 == len(df):
        continue
    else:
        # Create new temporary DF and drop canonical row, as well as all prior rows
        temp_df = df.copy(deep=True)
        #temp_df = temp_df[temp_df.index > idx]
        temp_df.drop(idx, axis = 0, inplace = True)
        temp_df.drop('show_id', axis = 1, inplace = True)

        holdout = row.drop(labels = ['show_id'])
        temp_df['similarity_score'] = temp_df.apply(lambda x: compare_series(x,holdout), axis = 1)

        most_similar_show = temp_df[['similarity_score']].idxmax()
        similarity_score = temp_df['similarity_score'].iloc[most_similar_show]

        df.at[idx,'most_similar_show'] = most_similar_show
        df.at[idx, 'similarity_score'] = similarity_score
        
        print('Similarities computed for row {}'.format(idx))

print(df)
