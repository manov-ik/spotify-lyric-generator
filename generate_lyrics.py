import requests
import re
import urllib.parse
from bs4 import Tag
from bs4 import BeautifulSoup
from sqlmodel import SQLModel, Session, create_engine, select
from models import LyricsCreate, Lyrics
import os
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL, echo=False)

def get_link_tam(song_name,artist_name,max_results=3):
    query = "tamil2lyrics" + " lyrics " + song_name + " by " + artist_name
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
    
    return real_url
    
    
def get_lyric_tam(song_name,artist_name,spotifyTrackId):
    url = get_link_tam(song_name=song_name,artist_name=artist_name)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', id='English')
    
    if content_div:
        lyrics_text = content_div.get_text(separator="\n", strip=True)
        match = re.search(r'(Male :|Female :|Chorus :)', lyrics_text)
        if not match:
            return "Unable to parse lyrics structure."
        lyrics_start = lyrics_text[match.start():]
        formatted_lyrics = re.sub(r'(?<!^)(?=[A-Z])', '\n', lyrics_start)
        #print(formatted_lyrics)
        lyrics = formatted_lyrics
        lyrics_data = LyricsCreate(
            artistName=artist_name,
            songTitle=song_name,
            spotifyTrackId=spotifyTrackId,
            lyrics=lyrics,
            lyricGotFromUrl=url
        )
        new_lyrics = Lyrics(**lyrics_data.dict())
        with Session(engine) as session:
            session.add(new_lyrics)
            session.commit()
            session.refresh(new_lyrics)
    else:
        lyrics = "Lyrics not found."
    return lyrics

def get_lyric_eng(artist_name, song_name,spotifyTrackId):
    baseUrl = "https://api.lyrics.ovh/v1/"
    url = baseUrl + artist_name + "/" + song_name
    response = requests.get(url)
    
    data = response.json()
    if data["lyrics"]:
        lyrics = data.get("lyrics")
        lyrics_data = LyricsCreate(
            artistName=artist_name,
            songTitle=song_name,
            spotifyTrackId=spotifyTrackId,
            lyrics=lyrics,
            lyricGotFromUrl=url
        )
        new_lyrics = Lyrics(**lyrics_data.dict())
        with Session(engine) as session:
            session.add(new_lyrics)
            session.commit()
            session.refresh(new_lyrics)
    else:
        lyrics = "Lyrics not found."
    return lyrics

def get_lyric(song_name, artist_name, spotifyTrackId):
    
    with Session(engine) as session:
        statement = select(Lyrics).where(Lyrics.spotifyTrackId == spotifyTrackId)
        result = session.exec(statement).first()
        if result:
            return result.lyrics

    lyrics = get_lyric_tam(
        song_name=song_name,
        artist_name=artist_name,
        spotifyTrackId=spotifyTrackId
    )
    
    if lyrics == "Lyrics not found.":
        lyrics = get_lyric_eng(
            song_name=song_name,
            artist_name=artist_name,
            spotifyTrackId=spotifyTrackId
        )

    return lyrics


