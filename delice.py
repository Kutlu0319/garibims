import sys
import requests
import re
import base64
from bs4 import BeautifulSoup
import time

# Windows terminalde emoji uyumu
sys.stdout.reconfigure(encoding='utf-8')

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def decode_link(encoded):
    key = 'K9L'
    reversed_str = encoded[::-1]
    try:
        step1 = base64.b64decode(reversed_str).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ Base64 decode hatası: {str(e)}")
        return None

    output = ''
    for i in range(len(step1)):
        r = key[i % 3]
        n = ord(step1[i]) - (ord(r) % 5 + 1)
        output += chr(n)

    try:
        return base64.b64decode(output).decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"⚠️ İkinci Base64 decode hatası: {str(e)}")
        return None

def format_title(slug):
    words = slug.replace("-", " ").title().split()
    mid = len(words) // 2
    return " ".join(words[:mid]) + " – " + " ".join(words[mid:]) if len(words) > 3 else " ".join(words)

def get_film_slugs_from_page(page_num):
    url = f"https://www.fullhdfilmizlesene.so/yeni-filmler/{page_num}"
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        slugs = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            match = re.search(r'/film/([^/]+)', href)
            if match:
                slugs.add(match.group(1))
        if not slugs:
            print(f"⚠️ Sayfa {page_num}: Hiç slug bulunamadı")
        return list(slugs)
    except requests.RequestException as e:
        print(f"⚠️ Sayfa {page_num} alınamadı: {str(e)}")
        return []

def get_video_and_subtitles(slug):
    try:
        film_url = f"https://www.fullhdfilmizlesene.so/film/{slug}"
        response = requests.get(film_url, headers=headers, timeout=10)
        response.raise_for_status()
        film_page = response.text

        vidid = re.search(r"vidid\s*=\s*'([^']+)'", film_page)
        poster = re.search(r"vidimg\s*=\s*'([^']+)'", film_page)

        if not vidid:
            print(f"⚠️ {slug}: vidid bulunamadı")
            return None, [], None, None

        vid = vidid.group(1)
        poster_url = poster.group(1) if poster else None

        api_url = f"https://www.fullhdfilmizlesene.so/player/api.php?id={vid}&type=t&name=atom&get=video&format=json"
        api_response = requests.get(api_url, headers=headers, timeout=10).text.replace('\\', '')
        html_match = re.search(r'"html":"(.*?)"', api_response)
        if not html_match:
            print(f"⚠️ {slug}: API yanıtında iframe URL bulunamadı")
            return None, [], poster_url, None

        iframe_url = html_match.group(1)
        iframe_response = requests.get(iframe_url, headers=headers, timeout=10)
        iframe_response.raise_for_status()
        iframe_page = iframe_response.text

        file_match = re.search(r'"file":\s*av\([\'"]([^\'"]+)[\'"]\)', iframe_page)
        video_url = decode_link(file_match.group(1)) if file_match else None
        if not video_url:
            print(f"⚠️ {slug}: Video URL çözümlenemedi")
            return None, [], poster_url, None

        tracks = re.findall(r'<track[^>]+src=[\'"]([^\'"]+)[\'"][^>]*label=[\'"]([^\'"]+)[\'"]', iframe_page)
        turkish_tracks = [(url, label) for url, label in tracks if "Türkçe" in label]
        if not turkish_tracks and tracks:
            print(f"⚠️ {slug}: Türkçe altyazı bulunamadı, diğer altyazılar: {[label for _, label in tracks]}")
        elif not tracks:
            print(f"⚠️ {slug}: Hiç altyazı bulunamadı")

        # Ses parçası bilgisi için iframe içeriğini kontrol et
        audio_tracks = re.findall(r'<audio[^>]+src=[\'"]([^\'"]+)[\'"][^>]*label=[\'"]([^\'"]+)[\'"]', iframe_page)
        turkish_audio = None
        if audio_tracks:
            for audio_url, label in audio_tracks:
                if "Türkçe" in label:
                    turkish_audio = (audio_url, label)
                    break
            if not turkish_audio:
                print(f"⚠️ {slug}: Türkçe ses parçası bulunamadı, mevcut sesler: {[label for _, label in audio_tracks]}")

        return video_url, turkish_tracks, poster_url, turkish_audio
    except requests.RequestException as e:
        print(f"⚠️ {slug}: İstek hatası: {str(e)}")
        return None, [], None, None
    except Exception as e:
        print(f"⚠️ {slug}: Genel hata: {str(e)}")
        return None, [], None, None

def write_m3u_entry(f, slug, video_url, subtitles, poster_url, turkish_audio):
    title = format_title(slug)
    f.write(f'#EXTINF:-1 tvg-id="{slug}" tvg-name="{title}"')
    if poster_url:
        f.write(f' tvg-logo="{poster_url}"')
    f.write(f' group-title="FullHD", {title}\n')

    # Varsayılan olarak Türkçe sesi seç (index 0 varsayımı)
    f.write('#EXTVLCOPT:audio-track=0\n')

    # Türkçe altyazıları ekle
    for sub_url, label in subtitles:
        f.write(f'#EXTVLCOPT:sub-file={sub_url}\n')

    f.write(video_url + "\n")

def build_m3u(pages=5, output_file="playlist.m3u"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for page_num in range(1, pages + 1):
            print(f"🔍 Sayfa {page_num} taranıyor...")
            slugs = get_film_slugs_from_page(page_num)
            for slug in slugs:
                time.sleep(0.5)
                video_url, subtitles, poster_url, turkish_audio = get_video_and_subtitles(slug)
                if video_url:
                    write_m3u_entry(f, slug, video_url, subtitles, poster_url, turkish_audio)
                    print(f"✅ {format_title(slug)} eklendi")
                else:
                    print(f"⚠️ {slug} çözümlenemedi")
                time.sleep(0.5)

if __name__ == "__main__":
    build_m3u(pages=1)