import json
import math
import pymongo
from requests import get
from requests.auth import HTTPBasicAuth
import time

from credentials import api_key

# Test for existence of api_key variable
try:
    assert type(api_key) == str
except:
    print('Invalid API key. Please refer to README for usage instructions.')

# Establish DB connection and build "setlists" DB. Dependency here on whether user has MongoDB installed locally.
client = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = client["setlists"]

def build_artist_descriptions(record):
    """
    Reformats raw JSON response into dictionary containing artist information
    Returns dictionary in support of get_user_input function
    """

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


def get_user_input():
    """
    CLI interface for getting user input
    Returns tuple of artist id and artist name to be passed to write_to_db function
    """

    mb_base_url = 'https://musicbrainz.org/ws/2/artist?fmt=json&query={}&limit=5'

    # Call API and build dictionary describing artist records
    artist = input('Please enter an artist: ')
    response = get(mb_base_url.format(artist))
    artist_information = {idx+1:build_artist_descriptions(record) for idx, record in enumerate(response.json()['artists'])}

    # Prompt user to confirm artist
    print('-'*50)
    print('Following results found:')
    for k, v in artist_information.items():
        print('{}. Name: {} | Confidence score: {} | Origin: {}. Description: {}'.format(k, v['name'], v['confidence_score'], v['origin'], v['description']))

    print('-'*50)
    confirmation = input('Please confirm your artist by entering the number associated with your artist: ')

    return (artist_information[int(confirmation)]['id'],artist_information[int(confirmation)]['name'].lower().replace(' ','_'))

def parse_json(response):
    """
    Accepts a raw JSON response and reformats to fit a target schema for document insertion
    Returns a list of dictionaries to be inserted in write_to_db function
    """

    to_insert = []

    for setlist in response['setlist']:

        # Single level of index
        id = setlist.get('id', None)
        event_date = setlist.get('eventDate', None)
        last_updated = setlist.get('lastUpdated', None)

        # Multilayer index
        try:
            venue_id = setlist['venue']['id']
        except KeyError:
            venue_id = None
        try:
            venue_name = setlist['venue']['name']
        except KeyError:
            venue_name = None
        try:
            venue_city = setlist['venue']['city']['name']
        except:
            venue_city = None
        try:
            venue_state = setlist['venue']['city']['state']
        except:
            venue_state = None
        try:
            venue_state_code = setlist['venue']['city']['stateCode']
        except:
            venue_state_code = None
        try:
            venue_country = setlist['venue']['city']['country']['name']
        except:
            venue_country = None
        try:
            venue_country_code = setlist['venue']['city']['country']['code']
        except:
            venue_country_code = None
        try:
            venue_lat = setlist['venue']['city']['coords']['lat']
        except:
            venue_lat = None
        try:
            venue_long = setlist['venue']['city']['coords']['long']
        except:
            venue_long = None


        to_add_raw = {
        'id' : id,
        'event_date' : event_date,
        'last_updated' : last_updated,
        'venue_id' : venue_id,
        'venue_name' : venue_name,
        'venue_city' : venue_city,
        'venue_state' : venue_state,
        'venue_state_code' : venue_state_code,
        'venue_country' : venue_country,
        'venue_country_code' : venue_country_code,
        'venue_lat' : venue_lat,
        'venue_long' : venue_long
        }

        to_add = {k:v for k,v in to_add_raw.items() if v is not None}

        songs = []
        for set in setlist['sets']['set']:
            for song in set['song']:
                songs.append(song['name'])

        to_add['setlist'] = songs

        to_insert.append(to_add)

    return to_insert


def write_to_db(user_input,db):
    """
    The meat and potatoes function. Accepts input from get_user_input and writes to DB
    Returns a logging message with number of records inserted
    """

    # Assign name to collection from get_user_input() step
    mycollection = db[user_input[1]]

    setlist_base_url = 'https://api.setlist.fm/rest/1.0/artist/{}/setlists?p={}'
    headers = {'x-api-key': api_key, 'Accept': 'application/json'}

    # Get number of pages for loop
    first_response = get('https://api.setlist.fm/rest/1.0/artist/{}/setlists'.format(user_input[0]), headers=headers)
    items_per_page = first_response.json()['itemsPerPage']
    num_setlists = first_response.json()['total']
    num_pages = math.ceil(num_setlists/items_per_page)

    for page in range(num_pages):
        start_time = time.time()
        response = get(setlist_base_url.format(user_input[0],page+1), headers=headers)
        response_dict = response.json()

        try:
            if response_dict['message'] == 'Too Many Requests':
                print('Overloaded API. Sleeping for 30 seconds.')
                time.sleep(30)
        except:
            to_add = parse_json(response_dict)
            mycollection.insert_many(to_add)

            print('Page {} complete. Wrote {} records to DB.'.format(page+1,len(to_add)))

            if time.time() - start_time < 2:
                time.sleep(2)
            else:
                continue


user_input = get_user_input()
write_to_db(user_input,mydb)
