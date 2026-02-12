from flask import Flask, render_template, request, send_file
import requests
import os

app = Flask(__name__)

bad_words = ["damn", "hell", "shit", "fuck"]

BOOKS = {
    "pride": 1342,
    "moby": 2701,
    "frankenstein": 84,
    "dracula": 345,
    "sherlock": 1661,
    "alice": 11,
    "tomsawyer": 74,
    "montecristo": 1184,
    "doriangray": 174
}

CACHE_FOLDER = "cache"

if not os.path.exists(CACHE_FOLDER):
    os.makedirs(CACHE_FOLDER)


def clean_text(text):
    total_words = len(text.split())
    bad_count = 0

    for word in bad_words:
        occurrences = text.lower().count(word)
        bad_count += occurrences
        text = text.replace(word, "*" * len(word))

    percentage = 0
    if total_words > 0:
        percentage = round((bad_count / total_words) * 100, 4)

    return text, bad_count, total_words, percentage



def fetch_and_cache_book(book_id, book_key):
    cache_path = os.path.join(CACHE_FOLDER, f"{book_key}.txt")

    # ✅ If already cached → load from local
    if os.path.exists(cache_path):
        print("Loading from cache...")
        with open(cache_path, "r", encoding="utf-8") as f:
            return f.read()

    # ❌ If not cached → download
    print("Downloading from Gutenberg...")
    url = f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()

        content = response.text

        # Save to cache
        with open(cache_path, "w", encoding="utf-8") as f:
            f.write(content)

        return content

    except requests.exceptions.RequestException as e:
        print("Download error:", e)
        return None



@app.route("/", methods=["GET", "POST"])
def index():
    preview = ""
    message = ""
    stats = None

    if request.method == "POST":
        book_key = request.form["book_key"].lower()

        if book_key in BOOKS:
            book_id = BOOKS[book_key]
            content = fetch_and_cache_book(book_id, book_key)

            if content:
                cleaned, bad_count, total_words, percentage = clean_text(content)

                stats = {
                    "bad_count": bad_count,
                    "total_words": total_words,
                    "percentage": percentage
                }
                # Save cleaned version for download
                cleaned_path = os.path.join(CACHE_FOLDER, f"cleaned_{book_key}.txt")
                with open(cleaned_path, "w", encoding="utf-8") as f:
                    f.write(cleaned)

                preview = cleaned[:3000]
                message = "✅ Book loaded successfully."
            else:
                message = "⚠️ Failed to download book."
        else:
            message = "❌ Book not found in list."

    return render_template("index.html", preview=preview, message=message, stats=stats)



@app.route("/download/<book_key>")
def download(book_key):
    cleaned_path = os.path.join(CACHE_FOLDER, f"cleaned_{book_key}.txt")

    if os.path.exists(cleaned_path):
        return send_file(cleaned_path, as_attachment=True)

    return "File not found."


if __name__ == "__main__":
    app.run(debug=True, port=5050)
