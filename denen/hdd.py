import cloudscraper
from bs4 import BeautifulSoup
import re
import html
import base64
import time

BASE_URL = "https://www.hdfilmcehennemi.nl"
scraper = cloudscraper.create_scraper()

def get_latest_movies(limit=10):
    url = f"{BASE_URL}/load/page/1/home/"
    response = scraper.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    items = soup.select("a[href*='/film/']")[:limit]
    return [BASE_URL + a.get("href") for a in items]

def get_video_id(detail_url):
    response = scraper.get(detail_url)
    soup = BeautifulSoup(response.text, "html.parser")
    div = soup.select_one("div.alternative-links button.alternative-link")
    if not div:
        return None
    return div.get("data-video")

def get_iframe(video_id, referer):
    url = f"{BASE_URL}/video/{video_id}/"
    response = scraper.get(url, headers={
        "X-Requested-With": "fetch",
        "Referer": referer
    })
    match = re.search(r'data-src=\\?"(https:\\/\\/[^"]+)', response.text)
    if match:
        return html.unescape(match.group(1).replace("\\", ""))
    return None

def get_final_video_url(iframe_url):
    response = scraper.get(iframe_url, headers={"Referer": BASE_URL + "/"})
    match = re.search(r'file_link="([^"]+)"', response.text)
    if match:
        try:
            return base64.b64decode(match.group(1)).decode("utf-8")
        except:
            return None
    return None

def get_poster_and_title(detail_url):
    response = scraper.get(detail_url)
    soup = BeautifulSoup(response.text, "html.parser")
    title = soup.select_one("h1.section-title")
    poster = soup.select_one("aside.post-info-poster img.lazyload")
    return (title.text.strip() if title else "Film"), (poster.get("data-src") if poster else "")

def create_m3u_file(movies, output_file="output.m3u"):
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        for movie in movies:
            f.write(f'#EXTINF:-1 tvg-logo="{movie["poster"]}",{movie["title"]}\n')
            f.write(f'{movie["url"]}\n')
    print(f"\n✅ {len(movies)} film için M3U dosyası oluşturuldu: {output_file}")

def process_latest_movies():
    print("📥 En son eklenen 10 film işleniyor...")
    urls = get_latest_movies()
    result = []

    for idx, detail_url in enumerate(urls, 1):
        print(f"🔄 [{idx}] {detail_url}")
        try:
            video_id = get_video_id(detail_url)
            if not video_id:
                print("⚠ Video ID atlandı.")
                continue

            iframe_url = get_iframe(video_id, referer=detail_url)
            if not iframe_url:
                print("⚠ Iframe atlandı.")
                continue

            video_url = get_final_video_url(iframe_url)
            if not video_url:
                print("⚠ Video linki atlandı.")
                continue

            title, poster = get_poster_and_title(detail_url)
            result.append({"title": title, "poster": poster, "url": video_url})
            time.sleep(1)
        except Exception as e:
            print("⚠ Hata:", e)

    if result:
        create_m3u_file(result)
    else:
        print("❌ Uygun film bulunamadı.")

# ÇALIŞTIR
if __name__ == "__main__":
    process_latest_movies()
