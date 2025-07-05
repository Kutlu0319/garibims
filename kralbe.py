import requests
import re
from bs4 import BeautifulSoup

KRAL_BET = "https://lll.istekbet3.tv"
BASE_URL = "https://royalvipcanlimac.com/channels.php"
PROXY_PREFIX = "https://vettelchannelowner-kralbet.hf.space/proxy/m3u?url="
LINK_PREFIX = "https://1029kralbettv.com"
M3U_FILE = "kralbe.m3u"

r = requests.get(PROXY_PREFIX + BASE_URL)
soup = BeautifulSoup(r.text, "html.parser")

channels = soup.find_all("a", href=re.compile(r"channel\?id="))
titles = soup.find_all("div", class_="home")
images = soup.find_all("img", src=True)

with open(M3U_FILE, "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n\n")
    for idx, channel in enumerate(channels):
        href = channel.get("href")
        if "channel?id=" in href:
            kanal_id = href.split("id=")[-1]  # Sadece ID alınır
            stream_url = f"{PROXY_PREFIX}{KRAL_BET}/{kanal_id}.m3u8"  # .m3u8 uzantısı eklenir
        else:
            continue  # Beklenmeyen format varsa atla

        tvg_name = titles[idx].text.strip() if idx < len(titles) else f"Kanal_{idx}"
        logo_url = f"{LINK_PREFIX}/{images[idx]['src'].lstrip('/')}" if idx < len(images) else ""

        f.write(
            f'#EXTINF:-1 tvg-name="{tvg_name}" tvg-language="Türkçe" tvg-country="Türkiye" '
            f'tvg-id="{kanal_id}" tvg-logo="{logo_url}" group-title="Genel Kanallar",{tvg_name}\n'
        )
        f.write(f"{stream_url}\n\n")
