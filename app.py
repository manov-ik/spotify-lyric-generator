from flask import Flask, redirect, request, session, render_template
import requests
import os
import urllib.parse
from datetime import datetime
from generate_lyrics import generate_lyrics
from dotenv import load_dotenv

load_dotenv()  
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')  # Used to sign session cookies

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
BASE_URL = 'https://api.spotify.com/v1/'
SCOPE = 'user-read-playback-state user-read-currently-playing'

@app.route("/")
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'redirect_uri': REDIRECT_URI,
        'scope': SCOPE
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return f"Error: {request.args['error']}"

    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'redirect_uri': REDIRECT_URI,
            'grant_type': 'authorization_code',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)

        if response.status_code != 200:
            return f"Error exchanging code: {response.json()}"

        token_info = response.json()

        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return redirect('/home')
    
    return "No code received, something went wrong."

@app.route('/home')
def home():
    if 'access_token' not in session:
        return redirect('/login')

    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')

    return render_template('home.html')

@app.route('/refresh_token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': session['refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()
    session['access_token'] = new_token_info ['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info ['expires_in']
    
    return redirect('/home')

@app.route('/get-lyrics',methods=['POST'])
def get_lyrics():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')
    
    headers = {'Authorization': f'Bearer {access_token}'}
    spotify_response = requests.get(f"{BASE_URL}me/player/currently-playing", headers=headers)
    print(spotify_response.status_code)
    if spotify_response.status_code == 204:
        lyrics="No song is currently playing."
        return render_template("home.html", lyrics=lyrics)
    
    if spotify_response.status_code != 200:
        return f"Spotify API Error: {spotify_response.status_code} - {spotify_response.text}", 400
    
    data = spotify_response.json()
    # print(data)
    if not data or 'item' not in data or data['item'] is None:
        return "No song is currently playing.", 400

    song_name = data['item']['name']
    artist_name = data['item']['artists'][0]['name']
    try:
        lyrics = generate_lyrics(song_name)
        return render_template("home.html", lyrics=lyrics , song_name=song_name ,artist_name=artist_name)
    except Exception as e:
        return render_template("home.html", lyrics=f"Error generating lyrics: {str(e)}", song_name=song_name ,artist_name=artist_name)
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)