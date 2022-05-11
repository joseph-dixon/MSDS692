import json
import math
import pymongo
from requests import get
from requests.auth import HTTPBasicAuth

from credentials import api_key

# Establish DB connection and initialize collection
myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["setlists"]

def build_artist_descriptions(record):
    artist_id = record['id']
    artist_name = record['name']
    artist_confidence_score = record['score']
    try:
        artist_origin = '{}, {}'.format(record['begin-area']['name'], record['area']['name'])
    except:
        try:
            artist_origin = record['area']['name']
        except:
            artist_origin = 'Unknown'

    try:
        artist_description = record['disambiguation']
    except:
        artist_description = 'Unknown'

    return {'id': artist_id,
            'name': artist_name,
            'confidence_score': artist_confidence_score,
            'origin': artist_origin,
            'description': artist_description
            }

def add_db_collection(client,db,artist_name):
    artist_name_recoded = artist_name.lower().replace(' ','_')
    mycol = mydb[artist_name_recoded]

def get_user_input():
    mb_base_url = 'https://musicbrainz.org/ws/2/artist?fmt=json&query={}&limit=5'

    # Call API and build dictionary describing artist records
    artist = input('Please enter an artist: ')
    response = get(mb_base_url.format(artist))
    artist_information = {idx+1:build_artist_descriptions(record) for idx, record in enumerate(response.json()['artists'])}

    # Prompt user to confirm artist
    print('Following results found:')
    for k, v in artist_information.items():
        print('{}. Name: {} | Confidence score: {} | Origin: {}. Description: {}'.format(k, v['name'], v['confidence_score'], v['origin'], v['description']))

    confirmation = input('Please confirm your artist by entering the number associated with your artist: ')

    return artist_information[int(confirmation)]['id']


setlist_base_url = 'https://api.setlist.fm/rest/1.0/artist/{}/setlists?p={}'
headers = {'x-api-key': api_key, 'Accept': 'application/json'}
first_response = get('https://api.setlist.fm/rest/1.0/artist/6faa7ca7-0d99-4a5e-bfa6-1fd5037520c6/setlists', headers=headers)

items_per_page = first_response.json()['itemsPerPage']
num_setlists = first_response.json()['total']
num_pages = math.ceil(num_setlists/items_per_page)

for page in range(num_pages):
    try:
        response = get(setlist_base_url.format('6faa7ca7-0d99-4a5e-bfa6-1fd5037520c6',page), headers = headers)
        print(response.json())
    except:
        print('Error caught at Page {}'.format(page))

#print(json.dumps(response.json(), indent=4))

# INITIALIZE MONGODB DB
# PASS MBID TO SETLIST.FM API
    # GET NUMBER OF PAGES, STORE AS VARIABLE
    # IN FOR LOOP, CALL EACH PAGE AND WRITE TO DB
    # REST BETWEEN LOOPS, MAYBE PROCESS OF MANIPULATION AND LOADING WILL ELIMINATE EXPLICIT REST CALLS
# INITIALIZE MONGODB DB
#   NOT SURE HOW TO MAKE THIS BROADLY APPLICABLE
# COLLECTION FOR SETLISTS, MAYBE TOURS IF SETLIST.FM CAN SUPPORT IT
# ITERATE THROUGH SETLISTS OBJECT, BUILD DOCUMENT FOR EACH WITH ALL FIELDS API SUPPORTS
