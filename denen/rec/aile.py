
import requests

def fetch_data():
    all_items = []
    page = 0
    while True:
        url = "https://m.prectv49.sbs/api/movie/by/filtres/14/created/{page}/4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452/".format(page=page)
        print(f"📥 Sayfa {{page}} çekiliyor: {https://m.prectv49.sbs/api/movie/by/filtres/14/created/{page}/4F5A9C3D9A86FA54EACEDDD635185/c3c5bd17-e37b-4b94-a944-8a3688a30452/}")
        response = requests.get(url, headers={{"user-agent": "okhttp/4.12.0"}})
        if response.status_code != 200:
            print(f"❌ Hata: {{response.status_code}}")
            break
        data = response.json()
        if not data:
            print("✅ Tüm veriler alındı.")
            break
        all_items.extend(data)
        page += 1
    return all_items

if __name__ == "__main__":
    data = fetch_data()
    print(f"🎯 Toplam {{len(data)}} içerik bulundu.")
