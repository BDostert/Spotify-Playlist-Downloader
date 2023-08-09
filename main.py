import spotipy
import requests
import base64
import datetime
import os

from pprint import pprint
from spotipy.oauth2 import SpotifyClientCredentials
from pytube import YouTube
from moviepy.editor import *
from googleapiclient.discovery import build
from urllib.parse import urlencode

sp = spotipy.Spotify


class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = 'https://accounts.spotify.com/api/token'

    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret

    def get_client_credentials(self):
        client_id = self.client_id
        client_secret = self.client_secret
        if client_id == None or client_secret == None:
            raise Exception('Your must set client_id and client_secret.')
        client_creds = f'{client_id}:{client_secret}'
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()

    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        return {
            'Authorization': f'Basic {client_creds_b64}'
        }
    def get_token_data(self):
        return {
            'grant_type': 'client_credentials'
        }

    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        r = requests.post(token_url, data= token_data, headers= token_headers)
        if r.status_code not in range(200, 299):
            raise Exception('Could not authenticate client.')
            #return False
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in']
        expires = now + datetime.timedelta(seconds= expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
        return True

    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token

    def get_user_playlists(self, username):
        endpoint = f'https://api.spotify.com/v1/users/{username}/playlists'
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        data = r.json()
        #pprint(data, indent=1)
        playlists = [[],[]]
        for i in range(len(data['items'])):
            playlists[0].append(data['items'][i]['id'])
            playlists[1].append(data['items'][i]['name'])          
        return playlists
    
    def get_playlist_tracks(self, playlist_id): 
        endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks'
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        data = r.json()
        #pprint(data, indent=1)
        tracks = []
        for i in range(len(data['items'])):
            tracks.append((data['items'][i]['track']['name'], data['items'][i]['track']['artists'][0]['name']))
        return tracks

    '''
    def get_resource(self, lookup_id, resource_type, version = 'v1'):
        endpoint = f'https://api.spotify.com/{version}/{lookup_id}/{resource_type}'
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        if r.status_code not in range(200, 299):
            return {}
        return r.json()
    '''

    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        return headers

    '''
    def search(self, query, search_type):
        access_token = self.get_access_token()
        headers = self.get_resource_header()
        endpoint = 'https//api.spotify.com/v1/search'
        data = urlencode({'q': query, 'type': search_type.lower()})
        lookup_url = f'{endpoint}?{data}'
        r = requests.get(lookup_url, headers= headers)
        if r.status_code not in range (200, 299):
            return {}
        return r.json()
    '''

class YoutubeAPI(object):
    YT_API_KEY = None
    serviceName = None
    version = None
    
    def __init__(self, YT_API_KEY, serviceName, version, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.YT_API_KEY = YT_API_KEY
        self.serviceName = serviceName
        self.version = version

        

    def get_links(self, vid_ids):
        completed = []
        for vid in vid_ids:
            endpoint = 'https://www.youtube.com/watch?v='
            completed.append(endpoint + vid)
        return completed


    def search_vids(self, queries):
        #endpoint = 'https://www.googleapis.com/youtube/v3/search'
        youtube = build(self.serviceName, self.version, developerKey=self.YT_API_KEY)
        vid_ids = []
        for query in queries:
            results = youtube.search().list(
                part = 'snippet',
                q = query,
                maxResults = 1,
                type = 'video'
            )
            response = results.execute()   
            vid_ids.append(response['items'][0]['id']['videoId'])
        #pprint(vid_ids)
        return vid_ids

    def video_to_audio_conversion(self, links, playlist_name):
        
        for link in links:
            yt = YouTube(link)
            yt.streams.filter(only_audio=True).first().download(output_path= playlist_name)
            #.order_by('resolution').desc().first().download()
            '''
            video_id = None
            try:
                yt = YouTube("https://www.youtube.com/watch?v=" + video_id)
                audio_stream = yt.streams.filter(only_audio=True).first()

                audio_file = audio_stream.download()

                audio_clip = AudioFileClip(audio_file)
                audio_clip.write_audiofile(audio_file[:-4] + ".mp3")

                os.remove(audio_file)

                print(f"Conversion complete for {link}!")
            except Exception as e:
                print(f"Error for {link}:", e)
            '''













def main():
    client_id = os.environ.get('SP_CLIENT_ID')
    client_secret   = os.environ.get('SP_CLIENT_SECRET')
    YT_API_KEY = os.environ.get('YT_API_KEY')
    #links = ['https://www.youtube.com/watch?v=fJ9rUzIMcZQ','https://www.youtube.com/watch?v=ZHwVBirqD2s']

    
    username = input('Spotify username: ')
    lists = SpotifyAPI(client_id, client_secret).get_user_playlists(username) 
    for i,name in enumerate(lists[1]):
        print(i + 1, name)
    playlist_number = int(input('Enter playlist number: ')) - 1
    song_titles = SpotifyAPI(client_id, client_secret).get_playlist_tracks(lists[0][playlist_number]) 
    vid_ids = YoutubeAPI(YT_API_KEY,'youtube','v3').search_vids(song_titles)
    links = YoutubeAPI(YT_API_KEY,'youtube','v3').get_links(vid_ids)
    YoutubeAPI(YT_API_KEY,'youtube','v3').video_to_audio_conversion(links, lists[1][playlist_number])


main()
