from flask import Flask, jsonify, request
import requests

app = Flask(__name__)

BASE_URL = "https://ythls.kekikakademi.org"

@app.route("/search/<query>")
def search(query):
    try:
        resp = requests.get(f"{BASE_URL}/sinewix/search/{query}")
        resp.raise_for_status()
        results = []

        for item in resp.json().get("search", []):
            results.append({
                "title": item.get("name"),
                "type": item.get("type"),
                "id": item.get("id"),
                "poster": item.get("posterPath")
            })

        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/details/<item_type>/<item_id>")
def get_details(item_type, item_id):
    try:
        url = f"{BASE_URL}/sinewix/{item_type}/{item_id}"
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()

        title = data.get("title") or data.get("name")
        alt_title = data.get("originalName")
        final_title = f"{title} - {alt_title}" if alt_title and alt_title != title else title
        year = data.get("releaseDate") or data.get("firstAirDate", "")
        genre_list = [genre.get("name") for genre in data.get("genres", [])]

        info = {
            "title": final_title,
            "year": year.split("-")[0] if year else None,
            "description": data.get("overview"),
            "poster": data.get("posterPath"),
            "rating": data.get("voteAverage"),
            "genres": genre_list,
            "actors": [{"name": a["name"], "photo": a.get("profilePath")} for a in data.get("casterslist", [])],
            "videos": [v["link"] for v in data.get("videos", [])],
        }

        return jsonify(info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)