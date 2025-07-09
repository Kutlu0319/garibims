import requests
import re

# Kaynak M3U dosyasının URL'si
m3u_url = "https://raw.githubusercontent.com/GitLatte/patr0n/refs/heads/site/lists/power-sinema.m3u"

# M3U içeriğini indir
response = requests.get(m3u_url)
original_content = response.text

# Linkleri tespit et ve dönüştür
def transform_link(line):
    match = re.search(r'(https://vidmody\.com/.+?/tt\d+)', line)
    if match:
        base = match.group(1).replace('/mm', '/vs').split('/main')[0].rstrip('/')
        transformed = f"https://2.nejyoner19.workers.dev/?url={base}/"
        return transformed
    return line

# Yeni içeriği oluştur
new_lines = []
for line in original_content.splitlines():
    if line.startswith("http"):
        new_lines.append(transform_link(line))
    else:
        new_lines.append(line)

# Dosyayı kaydet
with open("yedek_movie.m3u", "w", encoding="utf-8") as file:
    file.write("\n".join(new_lines))

print("✅ Dönüştürülmüş M3U dosyası: yedek_movie.m3u")