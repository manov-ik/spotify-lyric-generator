import requests
import re
import urllib.parse
from bs4 import Tag
from bs4 import BeautifulSoup

def format_lyrics(t):
    # print(t)
    match = re.search(r'(Male :|Female :|Chorus :)', t)
    if not match:
        return "Unable to parse lyrics structure."
    lyrics_start = t[match.start():]
    formatted_lyrics = re.sub(r'(?<!^)(?=[A-Z])', '\n', lyrics_start)
    return formatted_lyrics

def get_link(song_name,artist_name,max_results=3,domian="tamil2lyrics"):
    query = domian +" lyrics "+ song_name +" by "+artist_name
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
    print(real_url)
    return real_url


def generate_lyric_eng(artist_name,song_name):
    url = get_link(song_name=song_name,artist_name=artist_name,domian="azlyrics")
    # print(url)
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'lxml')
    divs = soup.find_all("div", {"class": ""})
    # print(divs)
    for div in divs:
        if not isinstance(div, Tag) or div.name != 'div':
            continue

        # Skip ads, scripts, and images
        if div.get('id', '').startswith('freestar'):
            continue
        if div.has_attr('data-freestar-ad'):
            continue
        if div.find('script') or div.find('img'):
            continue

        # Heuristic: block with many <br/> and long enough text is likely lyrics
        if str(div).count("<br") > 5 and len(div.get_text(strip=True)) > 100:
            # Replace <br/> tags with newlines
            for br in div.find_all("br"):
                br.replace_with("\n")
            text = div.get_text(strip=True)
            
            text = re.sub(r'(?<!\n)(?<!^)(?=[A-Z])', '\n', text)
            # print(text)
    if text:
        lyrics=text
    else:
        lyrics = "Lyrics section not found on the lyrics page."
    return lyrics

def generate_lyrics(song_name,artist_name):
    url = get_link(song_name=song_name,artist_name=artist_name)
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.text, 'html.parser')
    content_div = soup.find('div', id='English')  #Change soup based on actual website structure
    if content_div:
        lyrics_text = content_div.get_text(separator="\n", strip=True)
        lyrics = format_lyrics(lyrics_text)
    else:
        lyrics=generate_lyric_eng(song_name=song_name,artist_name=artist_name)
        # lyrics = "Lyrics section not found on the lyrics page."
    return lyrics