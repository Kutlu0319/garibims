import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import json
import sys
import re

sys.path.insert(0, '../../utilities')
from jsontom3u import create_single_m3u, create_m3us

pattern = r'"apiUrl\\":\\"(.*?)\\"'
base_url = "https://www.startv.com.tr"
img_base_url = "https://media.startv.com.tr/star-tv"

dizi_url = "https://www.startv.com.tr/dizi"

api_params = {
    "sort": "episodeNo asc",
    "limit": "100"
}

session = requests.Session()  # Performans için oturum başlatıldı.

def get_items_page(url):
    item_list = []
    r = session.get(url)
    soup = BeautifulSoup(r.content, "html.parser")
    items = soup.find_all("div", {"class": "poster-card"})
    
    for item in items:
        item_name_tag = item.find("div", {"class": "text-left"})
        item_name = item_name_tag.get_text().strip() if item_name_tag else "Bilinmeyen"

        item_img_tag = item.find("img")
        item_img = item_img_tag.get("src") if item_img_tag else ""

        item_url_tag = item.find("a")
        item_url = base_url + item_url_tag.get("href") if item_url_tag else ""

        temp_item = {
            "name": item_name,
            "img": item_img,
            "url": item_url
        }
        item_list.append(temp_item)

    return item_list

def get_item_api_url(url):
    api_path = ""
    url += "/bolumler"
    r = session.get(url)
    results = re.findall(pattern, r.text)
    if results:
        api_path = results[0]
    return api_path

def get_item_api(path):
    item_list = []
    params = api_params
    flag = True
    url = base_url + path
    skip = 0
    
    while flag:
        params["skip"] = skip
        try:
            r = session.get(url, params=params)
            data = r.json()
            items = data.get("items", [])  # Hata önleme için get() kullanıldı.
            
            for item in items:
                name = item.get("heading", "") + " - " + item.get("title", "")
                img = img_base_url + item["image"]["fullPath"] if item.get("image") else ""

                stream_url = ""
                if "video" in item:
                    ref_id = item["video"].get("referenceId", "")
                    stream_url = f"https://dygvideo.dygdigital.com/api/redirect?PublisherId=1&ReferenceId=StarTV_{ref_id}&SecretKey=NtvApiSecret2014*&.m3u8"
                
                if stream_url:
                    item_list.append({"name": name, "img": img, "stream_url": stream_url})
            
            flag = len(items) == 100  # Devam koşulu

            skip += 100 if flag else 0  # Döngü kontrolü

        except Exception as e:
            print(f"Hata: {e}")
            flag = False
    
    return item_list

def main(start=0, end=0):
    data = []
    series_list = get_items_page(dizi_url)
    
    end_index = end if end else len(series_list)
    
    for i in tqdm(range(start, end_index)):
        serie = series_list[i]
        print(i, serie["name"])
        api_path = get_item_api_url(serie["url"])
        episodes = get_item_api(api_path)

        temp_serie = serie.copy()
        temp_serie["episodes"] = episodes
        data.append(temp_serie)

    with open("www-startv-com-tr-arsiv.json", "w+", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    create_single_m3u("../../lists/video/sources/www-startv-com-tr", data, "arsiv")
    create_m3us("../../lists/video/sources/www-startv-com-tr/arsiv", data)

if __name__ == "__main__":
    main()