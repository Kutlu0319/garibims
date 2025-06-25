from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time, re

# Vidmody bağlantılarını buraya ekle
vs_links = [
    "https://vidmody.com/vs/tt13622970/",
    "https://vidmody.com/vs/tt5834410/"
]

m3u8_links = []

def extract_m3u8(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")

    # ✅ Güncel Service kullanımı
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print(f"Açılıyor: {url}")
        driver.get(url)
        time.sleep(5)  # Sayfanın yüklenmesini bekle
        html = driver.page_source
        match = re.search(r'https[^"]+\.m3u8', html)
        if match:
            found = match.group(0)
            print(f"🔗 Bulundu: {found}")
            m3u8_links.append(found)
        else:
            print("⚠️ M3U8 bulunamadı.")
    except Exception as e:
        print(f"❌ Hata: {e}")
    finally:
        driver.quit()

# Tüm bağlantıları işle
for link in vs_links:
    extract_m3u8(link)

# M3U dosyasına yaz
with open("vidmody_playlist.m3u", "w", encoding="utf-8") as f:
    f.write("#EXTM3U\n")
    for i, m3u in enumerate(m3u8_links, 1):
        f.write(f"#EXTINF:-1, Vidmody Video {i}\n{m3u}\n")

print("\n✅ M3U dosyası oluşturuldu: vidmody_playlist.m3u")