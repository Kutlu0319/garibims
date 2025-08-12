import sys
import requests
import re
import base64
from bs4 import BeautifulSoup

# Windows terminalde emoji uyumu
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    "User-Agent": "Mozilla/5.0"
}

def decode_link(encoded):
    key = 'K9L'
    reversed_str = encoded[::-1]
    try:
        step1 = base64.b64decode(reversed_str).decode('utf-8', errors='ignore')
    except:
        return None

    output = ''
    for i in range(len(step1)):
        r = key[i % 3]
        n = ord(step1[i]) - (ord(r) % 5 + 1)
        output += chr(n)

    try:
        return base64.b64decode(output).decode('utf-8', errors='ignore')
    except:
        return None

def format_title(slug):
    words = slug.replace("-", " ").title().split()
    mid = len(words) // 2
    return " ".join(words[:mid]) + " – " + " ".join(words[mid:]) if len(words) > 3 else " ".join(words)

def get_film_slugs_from_page(page_num):
    url = f"https://www.fullhdfilmizlesene.so/yeni-filmler/{page_num}"
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        slugs = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            match = re.search(r'/film/([^/]+)', href)
            if match:
                slugs.add(match.group(1))
        return list(slugs)
    except:
        return []

def get_video_and_subtitles(slug):
    try:
        film_page = requests.get(f"https://www.fullhdfilmizlesene.so/film/{slug}", headers=headers).text

        vidid = re.search(r"vidid\s*=\s*'([^']+)'", film_page)
        poster = re.search(r"vidimg\s*=\s*'([^']+)'", film_page)

        if not vidid:
            return None, [], None

        vid = vidid.group(1)
        poster_url = poster.group(1) if poster else None

        api_url = f"https://www.fullhdfilmizlesene.so/player/api.php?id={vid}&type=t&name=atom&get=video&format=json"
        api_response = requests.get(api_url, headers=headers).text.replace('\\', '')
        html_match = re.search(r'"html":"(.*?)"', api_response)
        if not html_match:
            return None, [], poster_url

        iframe_url = html_match.group(1)
        iframe_page = requests.get(iframe_url, headers=headers).text

        file_match = re.search(r'"file":\s*av\([\'"]([^\'"]+)[\'"]\)', iframe_page)
        video_url = decode_link(file_match.group(1)) if file_match else None

        tracks = re.findall(r'<track[^>]+src=[\'"]([^\'"]+)[\'"][^>]*label=[\'"]([^\'"]+)[\'"]', iframe_page)

        return video_url, tracks, poster_url
    except:
        return None, [], None

def write_m3u_entry(f, slug, video_url, subtitles, poster_url):
    title = format_title(slug)
    f.write(f'#EXTINF:-1 tvg-id="{slug}" tvg-name="{title}"')
    if poster_url:
        f.write(f' tvg-logo="{poster_url}"')
    f.write(f' group-title="FullHD", {title}\n')

    sorted_subs = sorted(subtitles, key=lambda x: ("Türkçe" not in x[1], x[1]))
    for sub_url, label in sorted_subs:
        f.write(f'#EXTVLCOPT:sub-file={sub_url}\n')

    f.write(video_url + "\n")

def build_m3u(pages=5, output_file="playlist.m3u"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for page_num in range(1, pages + 1):
            print(f"🔍 Sayfa {page_num} taranıyor...")
            slugs = get_film_slugs_from_page(page_num)
            for slug in slugs:
                video_url, subtitles, poster_url = get_video_and_subtitles(slug)
                if video_url:
                    write_m3u_entry(f, slug, video_url, subtitles, poster_url)
                    print(f"✅ {format_title(slug)} eklendi")
                else:
                    print(f"⚠️ {slug} çözümlenemedi")

if __name__ == "__main__":
    build_m3u(pages=1)