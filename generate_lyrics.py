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

def get_link(song_name,artist_name,max_results=3,domain="tamil2lyrics"):
    query = domain +" lyrics "+ song_name +" by "+artist_name
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


def generate_lyric_eng(artist_name, song_name):
    # Get the lyrics page URL
    url = get_link(song_name=song_name, artist_name=artist_name, domain="azlyrics")

    try:
        # Fetch the content from the URL
        res = requests.get(url)
        res.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL: {e}")
        return "Lyrics section not found on the lyrics page."

    # Parse the page content
    soup = BeautifulSoup(res.content, 'lxml')

    # Look for div with specific class for lyrics
    divs = soup.find_all("div", class_="col-xs-12 col-lg-8 text-center")  # Updated class

    lyrics = "Lyrics section not found on the lyrics page."  # Default if no lyrics found

    for div in divs:
        # Skip ads, scripts, and images
        if div.get('id', '').startswith('freestar'):
            continue
        if div.has_attr('data-freestar-ad'):
            continue
        if div.find('script') or div.find('img'):
            continue

        # Heuristic: Block with many <br> and long enough text
        if str(div).count("<br") > 5 and len(div.get_text(strip=True)) > 100:
            # Replace <br> tags with newlines
            for br in div.find_all("br"):
                br.replace_with("\n")
            text = div.get_text(separator='\n', strip=True)

            # Optional: Regex for formatting newlines between uppercase letters
            text = re.sub(r'(?<!\n)(?<!^)(?=[A-Z])', '\n', text)

            lyrics = text  # Set the found lyrics

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