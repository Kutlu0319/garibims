import requests

MOVIE_URL = "https://m.prectv49.sbs/api/movie/by/filtres/0/created/{page}/4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452"

def get_all_movies():
    all_movies = []
    page = 0

    while True:
        url = MOVIE_URL.format(page=page)
        print(f"🔍 Sayfa {page} çekiliyor: {url}")
        response = requests.get(url, headers={
            "user-agent": "okhttp/4.12.0"
        })

        if response.status_code != 200:
            print(f"❌ HTTP {response.status_code}")
            break

        data = response.json()
        if not data:
            print(f"✅ Tüm filmler alındı. Toplam sayfa: {page}")
            break

        all_movies.extend(data)
        page += 1

    return all_movies


def extract_movie_links(movies):
    playlist_lines = ['#EXTM3U']

    for movie in movies:
        title = movie.get("title", "Bilinmeyen")
        logo = movie.get("image", "")
        movie_id = str(movie.get("id", ""))
        sources = movie.get("sources", [])
        year = movie.get("year", "")
        group = "Filmler"

        for source in sources:
            url = source.get("url")
            if url and url.endswith(".m3u8"):
                quality = source.get("quality", "")
                quality_str = f" [{quality}]" if quality else ""
                entry = (
                    f'#EXTINF:-1 tvg-id="{movie_id}" tvg-logo="{logo}" tvg-name="{title}" group-title="{group}",{title} ({year}){quality_str}',
                    '#EXTVLCOPT:http-user-agent=okhttp/4.12.0',
                    '#EXTVLCOPT:http-referrer=https://twitter.com',
                    url
                )
                playlist_lines.extend(entry)

    return '\n'.join(playlist_lines)


def save_to_file(content, filename="rectv_movies.m3u"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📁 M3U dosyası kaydedildi: {filename}")


if __name__ == "__main__":
    movies = get_all_movies()
    print(f"🎬 Toplam {len(movies)} film bulundu.")
    m3u_content = extract_movie_links(movies)
    save_to_file(m3u_content)
