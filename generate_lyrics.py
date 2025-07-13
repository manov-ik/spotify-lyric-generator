import requests
import re
import urllib.parse
from bs4 import Tag
from bs4 import BeautifulSoup
from sqlmodel import SQLModel, Session, create_engine, select
from models import LyricsCreate, Lyrics
import os
from dotenv import load_dotenv
import gzip
import base64


def compress_text(text: str) -> str:
    return base64.b64encode(gzip.compress(text.encode('utf-8'))).decode('utf-8')

def decompress_text(compressed: str) -> str:
    try:
        # Add padding if necessary
        padding = len(compressed) % 4
        if padding:
            compressed += '=' * (4 - padding)
        return gzip.decompress(base64.b64decode(compressed.encode('utf-8'))).decode('utf-8')
    except Exception as e:
        print(f"Error decompressing text: {e}")
        return "Error decompressing lyrics"


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, echo=False)

def get_link_tam(song_name,artist_name,max_results=3):
    query = "tamil2lyrics" + " lyrics " + song_name + " by " + artist_name
    # print(query)
    headers = {'User-Agent': 'Mozilla/5.0'}
    query_encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={query_encoded}"
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for result in soup.find_all('a', {'class': 'result__a'}, limit=max_results):
        results.append(result.get('href'))
    if not results:
        return "Lyrics not found."
    raw_link = results[0]
    parsed = urllib.parse.urlparse("https:" + raw_link)
    query_params = urllib.parse.parse_qs(parsed.query)  
    real_url = query_params.get('uddg', [None])[0]
    # print(real_url)
    
    return real_url
    
    
def get_lyric_tam(song_name, artist_name):
    url = get_link_tam(song_name=song_name, artist_name=artist_name)
    if not url or "Lyrics not found." in url:
        return "Lyrics not found.", None

    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', id='English')

    if content_div:
        lyrics_text = content_div.get_text(separator="\n", strip=True)
        match = re.search(r'(Male :|Female :|Chorus :)', lyrics_text)
        if not match:
            return "Lyrics not found.", url
        lyrics_start = lyrics_text[match.start():]
        formatted_lyrics = re.sub(r'(?<!^)(?=[A-Z])', '\n', lyrics_start)
        return formatted_lyrics, url
    else:
        return "Lyrics not found.", url


def get_lyric_eng(artist_name, song_name):
    baseUrl = "https://api.lyrics.ovh/v1/"
    url = f"{baseUrl}{artist_name}/{song_name}"
    response = requests.get(url)
    
    try:
        data = response.json()
        if "lyrics" in data and data["lyrics"]:
            return data["lyrics"], url
    except Exception:
        pass
    
    return "Lyrics not found.", url

def get_lyric(song_name, artist_name, spotifyTrackId):
    # print("Getting lyrics for:", song_name, "by", artist_name)
    with Session(engine) as session:
        statement = select(Lyrics).where(Lyrics.spotify_track_id == spotifyTrackId)
        result = session.exec(statement).first()
        # print("checking db")
        if result:
            return decompress_text(result.lyrics)
    # print("Lyrics not found in database. Fetching from source.")
    lyrics, source_url = get_lyric_tam(song_name, artist_name)
    # print("Lyrics found:", lyrics)
    
    if lyrics == "Lyrics not found.":
        lyrics, source_url = get_lyric_eng(artist_name, song_name)

    if lyrics == "Lyrics not found.":
        return lyrics

    compressed = compress_text(lyrics)
    lyrics_data = LyricsCreate(
        artist_name=artist_name,
        song_title=song_name,
        spotify_track_id=spotifyTrackId,
        lyrics=compressed,
        lyric_got_from_url=source_url
    )

    with Session(engine) as session:
        session.add(Lyrics(**lyrics_data.dict()))
        session.commit()

    return lyrics
