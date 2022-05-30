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

    return df

#mycol = get_user_input()
df = build_df(mydb, 'king_gizzard_&_the_lizard_wizard')
for row in df.iterrows():
    print(row)

## COMPARISON FUNCTION
"""
Accepts DF as argument. Maybe is a class method, IDK
Iterates through rows. For each row, it stores that row as a series and eliminates that row and all prior rows in temporary DF variable.
Applies a map/apply function that scores each row against the canonical series, sums the columns, and counts the number of twos. Divides by the number of non-zero column totals.
Search for maximum value in new "comparison_score" column and extracts the ID associated with it. NaN if all zero. Writes ID to source-of-truth DF in "closest_setlist" column.
"""
## SUBCOMPARISON FUNCTION
"""
Accepts two series as arguments. Sums them column-wise, extracts count of twos, count of non-zeros.
"""

## Class everything up as a 'Corpus' object? With .compare_setlists method? Maybe optional time parameters?

# print(mydb.list_collection_names())
