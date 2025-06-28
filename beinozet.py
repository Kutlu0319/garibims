import requests
import concurrent.futures

sakusezon = {
    32: '2010/2011', 
    30: '2011/2012',
    25: '2012/2013',
    34: '2013/2014',
    37: '2014/2015',
    24: '2015/2016',
    29: '2016/2017',
    23: '2017/2018',
    20: '2018/2019',
    994: '2019/2020',
    3189: '2020/2021',
    3308: '2021/2022',
    3438: '2022/2023',
    3580: '2023/2024',
    3746: '2024/2025',
}

sezonhafta = {
    32: range(1, 35),
    30: range(1, 35),
    25: range(1, 35),
    34: range(1, 35),
    37: range(1, 35),
    24: range(1, 35),
    29: range(1, 35),
    23: range(1, 35),
    20: range(1, 35),
    994: range(1, 35),
    3189: range(1, 43),
}

sezona = {
    30: 2899,
}

def fetch_and_parse(url_info):
    url, sezonss = url_info
    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        events = data.get('Data', {}).get('events', [])
        result = []
        for event in events:
            home = event.get('homeTeam', {}).get('name', 'Ev')
            home_score = event.get('homeTeam', {}).get('matchScore', '-')
            away = event.get('awayTeam', {}).get('name', 'Deplasman')
            away_score = event.get('awayTeam', {}).get('matchScore', '-')
            logo = event.get('highlightThumbnail', '')
            match_id = event.get('matchId', '')

            # --- EN YÜKSEK ÇÖZÜNÜRLÜK --- #
            video_url = None
            # Öncelik: highlightVideoUrls (liste varsa)
            if event.get('highlightVideoUrls'):
                videos = event['highlightVideoUrls']
                # Kaliteyi sıralayıp en yükseği al
                def parse_quality(x):
                    # 1080p/720p gibi olabilir, yoksa 0
                    try:
                        return int(''.join(filter(str.isdigit, x.get('quality',''))))
                    except: return 0
                # Listede varsa kaliteye göre sırala
                best_video = sorted(videos, key=parse_quality, reverse=True)
                if best_video:
                    video_url = best_video[0]['url']
            # Yoksa eski sistem: highlightVideoUrl
            elif event.get('highlightVideoUrl'):
                video_url = event['highlightVideoUrl']

            if video_url:
                title = f"{home} {home_score}-{away_score} {away}"
                line1 = f'#EXTINF:-1 tvg-id="{match_id}" tvg-logo="{logo}" group-title="{sezonss}",{title}\n'
                line2 = f"{video_url}\n"
                result.append((sezonss, line1, line2))
        return result
    except Exception:
        return []

tmurlfull = []
for sezonss_id, sezonss_name in sakusezon.items():
    weeks = sezonhafta.get(sezonss_id, range(1, 39))
    st = sezona.get(sezonss_id, 0)
    for week in weeks:
        url = f"https://beinsports.com.tr/api/highlights/events?sp=1&o=18&s={sezonss_id}&r={week}&st={st}"
        tmurlfull.append((url, sezonss_name))

all_lines = []

with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
    futures = executor.map(fetch_and_parse, tmurlfull)
    for result in futures:
        for sezonss, line1, line2 in result:
            all_lines.append((sezonss, line1, line2))

all_lines.sort(key=lambda x: x[0])

all_m3u_path = "all.m3u"
with open(all_m3u_path, 'w', encoding='utf-8') as f:
    f.write("#EXTM3U\n\n")
    for sezonss, line1, line2 in all_lines:
        f.write(line1)
        f.write(line2)

print("Tek bir all.m3u dosyası oluşturuldu ve tüm maçlar en yüksek çözünürlükle yazıldı.")
