import requests
import re
import urllib.parse
from bs4 import BeautifulSoup

def format_lyrics(t):
    # print(t)
    match = re.search(r'(Male :|Female :|Chorus :)', t)
    if not match:
        return "Unable to parse lyrics structure."
    lyrics_start = t[match.start():]
    formatted_lyrics = re.sub(r'(?<!^)(?=[A-Z])', '\n', lyrics_start)
    return formatted_lyrics

def get_link(query,max_results=3):
    query = "tamil2lyrics lyrics "+query
    headers = {'User-Agent': 'Mozilla/5.0'}
    query_encoded = urllib.parse.quote_plus(query)
    url = f"https://html.duckduckgo.com/html/?q={query_encoded}"

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    results = []
    for result in soup.find_all('a', {'class': 'result__a'}, limit=max_results):
        title = result.get_text()
        link = result.get('href')
        results.append({'title': title, 'link': link})

    raw_link = results[0]["link"]
    parsed = urllib.parse.urlparse("https:" + raw_link)
    query_params = urllib.parse.parse_qs(parsed.query)

    real_url = query_params.get('uddg', [None])[0]
    return real_url


def generate_lyric_eng(artist_name,song_name):
    try:
        song_name = re.sub('[\W_]+', '', song_name).lower()
        artist_name = re.sub('[\W_]+', '', artist_name).lower()
        url = "https://www.azlyrics.com/lyrics/{aname}/{sname}.html".format(aname=artist_name, sname=song_name)
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'lxml')
        divs = soup.find_all("div", {"class": ""})
        try:
            lyrics = divs[1].text
            lyrics = lyrics[2: -1]
            return {"lyrics": lyrics}
        except Exception as e:
            print(e)
            return {"Error": "Not found"}
        
    except Exception as e:
        print(e)
        return {"Error": e}

def generate_lyrics(song_name):
    url = get_link(query=song_name)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', id='English')  #Change soup based on actual website structure
    if content_div:
        lyrics_text = content_div.get_text(separator="\n", strip=True)
        lyrics = format_lyrics(lyrics_text)
    else:
        lyrics = "Lyrics section not found on the lyrics page."
    return lyrics