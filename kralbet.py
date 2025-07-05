import requests
import re
from bs4 import BeautifulSoup

# Temel ayarlar
KRAL_BET = "https://lll.istekbet3.tv"
BASE_URL = "https://royalvipcanlimac.com/channels.php"
PROXY_PREFIX = "https://vettelchannelowner-kralbet.hf.space/proxy/m3u?url="
LINK_PREFIX = "https://1029kralbettv.com"
M3U_FILE = "kralbet.m3u"

# Proxy üzerinden istek gönder
try:
    r = requests.get(PROXY_PREFIX + BASE_URL, timeout=10)
    print(f"İstek Durumu: {r.status_code}")
except Exception as e:
    print(f"Bağlantı hatası: {e}")
    exit()

# Sayfa parse ediliyor
soup = BeautifulSoup(r.text, "html.parser")

# Elemanları yakala
channels = soup.find_all("a", href=re.compile(r"channel\?id="))
titles = soup.find_all("div", class_="home")
images = soup.find_all("img", src=True)

print(f"Bulunan kanal sayısı: {len(channels)}")
print(f"Başlık sayısı: {len(titles)}")
print(f"Logo sayısı: {len(images)}")

# M3U dosyasını oluştur
with open(M3U_FILE, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n\n")
    for idx, channel in enumerate(channels):
        href = channel.get("href")
        if "channel?id=" not in href:
            continue

        kanal_id = href.split("id=")[-1]
        stream_url = f"{PROXY_PREFIX}{KRAL_BET}/{kanal_id}.m3u8"

        tvg_name = titles[idx].text.strip() if idx < len(titles) else f"Kanal_{idx}"
        logo_url = f"{LINK_PREFIX}/{images[idx]['src'].lstrip('/')}" if idx < len(images) else ""

        # Test çıktısı
        print(f"Yazılıyor: {tvg_name} - {stream_url}")

        f.write(
            f'#EXTINF:-1 tvg-name="{tvg_name}" tvg-language="Türkçe" tvg-country="Türkiye" '
            f'tvg-id="{kanal_id}" tvg-logo="{logo_url}" group-title="Genel Kanallar",{tvg_name}\n'
        )
        f.write(f"{stream_url}\n\n")

print("M3U dosyası başarıyla oluşturuldu.")