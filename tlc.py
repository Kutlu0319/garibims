#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import time
import logging
from typing import List, Tuple, Dict, Any, Optional

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from requests.adapters import HTTPAdapter, Retry

# ---------------------------------------------------------
# Opsiyonel: M3U yardımcıları mevcutsa kullan, yoksa pas geç
# ---------------------------------------------------------
HAS_M3U = True
try:
    sys.path.insert(0, '../../utilities')
    from jsontom3u import create_single_m3u, create_m3us
except Exception:
    HAS_M3U = False

# ---------------------------------------------------------
# Ayarlar
# ---------------------------------------------------------
AJAX_URL = "https://www.tlctv.com.tr/ajax/more"
SITE_REFERER = "https://www.tlctv.com.tr/"
# Not: Orijinal koddaki PublisherId farkını (27/20) çözümlemek için
# iki aday URL üreteceğiz; çoğu durumda server redirect ile .m3u8 döner.
STREAM_BASE = "https://dygvideo.dygdigital.com/api/redirect"
PUBLISHER_IDS = (20, 27)  # önce 20 dene, sonra 27
SECRET_KEY = "NtvApiSecret2014*"

REQUEST_TIMEOUT = 15  # saniye
REQUEST_PAUSE = 0.2   # istekler arası kısa mola (rate-limit azaltma)
BACKOFF_FACTOR = 0.6
MAX_RETRIES = 5

DEFAULT_HEADERS = {
    "Referer": SITE_REFERER,
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
}

# ---------------------------------------------------------
# Logger
# ---------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("tlctv-scraper")

# ---------------------------------------------------------
# HTTP Session (retry’li)
# ---------------------------------------------------------
SESSION = requests.Session()
retries = Retry(
    total=MAX_RETRIES,
    backoff_factor=BACKOFF_FACTOR,
    status_forcelist=(429, 500, 502, 503, 504),
    allowed_methods=frozenset(["GET", "POST"]),
    raise_on_status=False,
)
SESSION.mount("https://", HTTPAdapter(max_retries=retries))
SESSION.mount("http://", HTTPAdapter(max_retries=retries))
SESSION.headers.update(DEFAULT_HEADERS)


# ---------------------------------------------------------
# Yardımcılar
# ---------------------------------------------------------
def safe_soup_get(attr_getter, default=None):
    try:
        return attr_getter()
    except Exception:
        return default


def get_soup_from_post(url: str, data: Dict[str, Any]) -> Optional[BeautifulSoup]:
    time.sleep(REQUEST_PAUSE)
    try:
        r = SESSION.post(url, data=data, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        log.warning("POST %s hatası: %s", url, e)
        return None


def get_soup_from_get(url: str) -> Optional[BeautifulSoup]:
    time.sleep(REQUEST_PAUSE)
    try:
        r = SESSION.get(url, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.content, "html.parser")
    except Exception as e:
        log.warning("GET %s hatası: %s", url, e)
        return None


def build_candidate_stream_urls(reference_id: str) -> List[str]:
    # .m3u8 sonunu eklemiyoruz; çoğu durumda endpoint zaten redirect ile m3u8’e yönlendirir.
    # Eğer illa .m3u8 istenirse aşağıdaki satırı aktif edebilirsiniz.
    # f"{STREAM_BASE}?PublisherId={pid}&ReferenceId={reference_id}&SecretKey={SECRET_KEY}&.m3u8"
    return [
        f"{STREAM_BASE}?PublisherId={pid}&ReferenceId={reference_id}&SecretKey={SECRET_KEY}"
        for pid in PUBLISHER_IDS
    ]


# ---------------------------------------------------------
# 1) Program listesi (sayfa bazlı)
# ---------------------------------------------------------
def get_single_program_page(page: int = 0) -> List[Dict[str, str]]:
    all_programs: List[Dict[str, str]] = []
    data = {"type": "discover", "slug": "a-z", "page": page}
    soup = get_soup_from_post(AJAX_URL, data=data)
    if not soup:
        return all_programs

    programs = soup.find_all("div", {"class": "poster"})
    for program in programs:
        a = program.find("a")
        img_tag = program.find("img")

        program_url = safe_soup_get(lambda: a.get("href"), "")
        program_img = safe_soup_get(lambda: img_tag.get("src"), "")

        # Adı onclick’ten almaya çalış; yoksa alt/title dene
        program_name = safe_soup_get(
            lambda: a.get("onclick")
            .replace("GAEventTracker('DISCOVER_PAGE_EVENTS', 'POSTER_CLICKED', '", "")
            .replace("');", ""),
            None,
        )
        if not program_name:
            program_name = (
                safe_soup_get(lambda: img_tag.get("alt")) or
                safe_soup_get(lambda: a.get_text(strip=True)) or
                "İsimsiz Program"
            )

        all_programs.append(
            {"img": program_img, "url": program_url, "name": program_name}
        )

    return all_programs


# ---------------------------------------------------------
# 2) Tüm programları topla (paginated)
# ---------------------------------------------------------
def get_all_programs(max_empty_pages: int = 2) -> List[Dict[str, str]]:
    all_programs: List[Dict[str, str]] = []
    empty_seen = 0
    page = 0

    while True:
        page_programs = get_single_program_page(page)
        if not page_programs:
            empty_seen += 1
            log.info("Boş/hatali sayfa: %d (ardışık=%d)", page, empty_seen)
            if empty_seen >= max_empty_pages:
                log.info("Toplam sayfa: %d", page)
                break
        else:
            empty_seen = 0
            all_programs.extend(page_programs)
        page += 1

    return all_programs


# ---------------------------------------------------------
# 3) Program sayfasından program_id ve sezonlar
# ---------------------------------------------------------
def get_program_id(url: str) -> Tuple[str, List[str]]:
    season_list: List[str] = []
    soup = get_soup_from_get(url)
    if not soup:
        return "0", season_list

    dyn_link = soup.find("a", {"class": "dyn-link"})
    program_id = safe_soup_get(lambda: dyn_link.get("data-program-id"), "0")

    season_selector = soup.find("select", {"class": "custom-dropdown"})
    if season_selector:
        for opt in season_selector.find_all("option"):
            val = safe_soup_get(lambda: opt.get("value"), None)
            if val and val not in season_list:
                season_list.append(val)

    return program_id, season_list


# ---------------------------------------------------------
# 4) Belirli sezon + sayfadan bölüm listesi
# ---------------------------------------------------------
def parse_episodes_page(program_id: str, page: int, season: str, serie_name: str) -> List[Dict[str, str]]:
    all_episodes: List[Dict[str, str]] = []
    data = {
        "type": "episodes",
        "program_id": program_id,
        "page": page,
        "season": season,
    }
    soup = get_soup_from_post(AJAX_URL, data=data)
    if not soup:
        return all_episodes

    items = soup.find_all("div", {"class": "item"})
    for it in items:
        strong = it.find("strong")
        img_tag = it.find("img")
        a = it.find("a")

        ep_title = safe_soup_get(lambda: strong.get_text().strip(), "Bölüm")
        name = f"{serie_name} - {ep_title}"
        img = safe_soup_get(lambda: img_tag.get("src"), "")
        url = safe_soup_get(lambda: a.get("href"), "")

        if url:
            all_episodes.append({"name": name, "img": img, "url": url})

    return all_episodes


# ---------------------------------------------------------
# 5) Program ID + sezon listesi -> tüm bölümler
# ---------------------------------------------------------
def get_episodes_by_program_id(program_id: str, season_list: List[str], serie_name: str) -> List[Dict[str, str]]:
    all_episodes: List[Dict[str, str]] = []
    for season in tqdm(season_list, desc="Sezonlar", leave=False):
        page = 0
        empty_count = 0
        while True:
            page_eps = parse_episodes_page(program_id, page, season, serie_name)
            if not page_eps:
                empty_count += 1
                if empty_count >= 2:
                    break
            else:
                empty_count = 0
                all_episodes.extend(page_eps)
            page += 1

    # İstersen tarihe göre sıralama veya tersten çevirme burada yapılabilir
    return all_episodes


# ---------------------------------------------------------
# 6) Bölüm sayfasından video code -> stream URL adayları
# ---------------------------------------------------------
def get_stream_urls(episode_url: str) -> List[str]:
    soup = get_soup_from_get(episode_url)
    if not soup:
        return []
    player_div = soup.find("div", {"class": "video-player"})
    reference_id = safe_soup_get(lambda: player_div.get("data-video-code"), None)
    if not reference_id:
        return []

    return build_candidate_stream_urls(reference_id)


# ---------------------------------------------------------
# 7) Ana akış
# ---------------------------------------------------------
def run(start: int = 0, end: int = 0) -> Dict[str, Any]:
    output: List[Dict[str, Any]] = []
    programs_list = get_all_programs()

    if not programs_list:
        log.warning("Hiç program bulunamadı.")
        return {"programs": []}

    end_index = len(programs_list) if end == 0 else min(end, len(programs_list))
    start_index = max(0, start)

    for i in tqdm(range(start_index, end_index), desc="Programlar"):
        program = programs_list[i]
        log.info("%d | %s", i, program.get("name", ""))

        program_id, season_list = get_program_id(program["url"])
        if program_id == "0":
            log.warning("Program ID alınamadı: %s", program.get("name"))
            continue

        episodes = get_episodes_by_program_id(program_id, season_list, program["name"])
        if not episodes:
            continue

        temp_program = dict(program)
        temp_program["episodes"] = []

        for ep in tqdm(episodes, desc="Bölümler", leave=False):
            temp_episode = dict(ep)
            stream_candidates = get_stream_urls(ep["url"])
            if stream_candidates:
                # Tek alan isteyenler için ilk adayı koyuyoruz (geri kalanları da isterse kaydedebiliriz)
                temp_episode["stream_url"] = stream_candidates[0]
                temp_episode["stream_url_candidates"] = stream_candidates
                temp_program["episodes"].append(temp_episode)

        if temp_program["episodes"]:
            output.append(temp_program)

    return {"programs": output}


def save_outputs(data: Dict[str, Any]) -> None:
    # Ekrana JSON (UTF-8) yaz
    print(json.dumps(data, indent=4, ensure_ascii=False))

    # Dosyaya yaz
    json_path = "www-tlctv-com-tr-programlar.json"
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        log.info("JSON kaydedildi: %s", json_path)
    except Exception as e:
        log.error("JSON kaydedilemedi: %s", e)

    # M3U üret (opsiyonel)
    if HAS_M3U:
        try:
            # jsontom3u beklediğin eski şemaya daha yakın olsun diye dönüştürelim:
            # data["programs"] -> list[ program{img,url,name,episodes[list{...}]} ]
            programs = data.get("programs", [])
            create_single_m3u("../../lists/video/sources/www-tlctv-com-tr", programs, "all")
            create_m3us("../../lists/video/sources/www-tlctv-com-tr/programlar", programs)
            log.info("M3U dosyaları oluşturuldu.")
        except Exception as e:
            log.error("M3U oluşturma hatası: %s", e)
    else:
        log.info("jsontom3u bulunamadı; M3U adımı atlandı.")


def parse_args(argv: List[str]) -> Tuple[int, int]:
    # Kullanım:
    #   python script.py              -> tüm programlar
    #   python script.py 10           -> 10. indexten sona
    #   python script.py 10 50        -> 10..49 arası
    start, end = 0, 0
    if len(argv) >= 2:
        try:
            start = int(argv[1])
        except Exception:
            pass
    if len(argv) >= 3:
        try:
            end = int(argv[2])
        except Exception:
            pass
    return start, end


def main():
    start, end = parse_args(sys.argv)
    data = run(start=start, end=end)
    save_outputs(data)


if __name__ == "__main__":
    main()
