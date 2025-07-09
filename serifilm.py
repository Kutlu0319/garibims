import requests
import re

# M3U dosyasının URL'si
m3u_url = "https://raw.githubusercontent.com/GitLatte/patr0n/refs/heads/site/lists/power-sinema.m3u"

# M3U içeriğini indir
response = requests.get(m3u_url)
original_content = response.text

new_lines = []
include_next = False

for line in original_content.splitlines():
    # Eğer satır SERI FILM grubundaysa
    if re.search(r'group-title=".*SERI FILM.*"', line):
        # "⚡SERI FILM⚡ Stargate" → "Stargate"
        match = re.search(r'group-title=".*SERI FILM.*?\s*(.+?)"', line)
        group_name = match.group(1).strip() if match else "Film"
        simplified_line = re.sub(r'group-title=".*SERI FILM.*?"', f'group-title="{group_name}"', line)
        new_lines.append(simplified_line)
        include_next = True

    # Eğer sonraki satır linkse, dönüştür
    elif line.startswith("http") and include_next:
        match = re.search(r'(https://vidmody\.com/.+?/tt\d+)', line)
        if match:
            base = match.group(1).replace('/mm', '/vs').split('/main')[0].rstrip('/')
            transformed = f"https://2.nejyoner19.workers.dev/?url={base}/"
            new_lines.append(transformed)
        else:
            new_lines.append(line)
        include_next = False

    else:
        include_next = False

# Yeni dosyayı kaydet
with open("serifilm.m3u", "w", encoding="utf-8") as file:
    file.write("\n".join(new_lines))

print("✅ Tamamlandı: SERI FILM grubu filtrelendi, group-title sadeleştirildi ve linkler dönüştürüldü.")