import json
import logging
import os
import threading
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

app = Flask(__name__)
DATA_FILE = Path(__file__).parent / "data" / "news.json"

BADGE_CLASSES = {
    "OpenAI Blog":               "badge-openai",
    "HuggingFace Blog":          "badge-hugging",
    "Google DeepMind":           "badge-deepmind",
    "MIT Technology Review AI":  "badge-mit",
    "VentureBeat AI":            "badge-venture",
    "The Verge AI":              "badge-verge",
    "Ars Technica AI":           "badge-ars",
    "36氪 AI":                   "badge-36kr",
    "量子位":                     "badge-qbit",
}

@app.template_global()
def badge_class(source):
    return BADGE_CLASSES.get(source, "badge-default")


def load_articles(source_filter=None, search=None):
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)
    if source_filter:
        articles = [a for a in articles if a["source"] == source_filter]
    if search:
        q = search.lower()
        articles = [
            a for a in articles
            if q in a["title"].lower() or q in a.get("summary_zh", "").lower()
        ]
    return articles


def update_job():
    log.info("定时更新开始...")
    from scraper import scrape_all
    from summarizer import summarize_pending
    new = scrape_all()
    summarize_pending()
    log.info(f"定时更新完成，新增 {len(new)} 条")


@app.route("/")
def index():
    articles = load_articles()
    sources = sorted({a["source"] for a in articles})
    return render_template("index.html", articles=articles, sources=sources)


@app.route("/api/articles")
def api_articles():
    source = request.args.get("source")
    search = request.args.get("q")
    articles = load_articles(source_filter=source, search=search)
    return jsonify(articles)


@app.route("/api/update", methods=["POST"])
def api_update():
    threading.Thread(target=update_job, daemon=True).start()
    return jsonify({"status": "started"})


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_job, "interval", hours=6, id="update", replace_existing=True)
    scheduler.start()
    log.info("定时器已启动，每 6 小时更新一次")
    return scheduler


start_scheduler()
if not DATA_FILE.exists():
    log.info("首次启动，后台抓取数据...")
    threading.Thread(target=update_job, daemon=True).start()


if __name__ == "__main__":
    app.run(debug=False, port=5000, use_reloader=False)
