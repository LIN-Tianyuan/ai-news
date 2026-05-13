import feedparser
import json
import os
from datetime import datetime, timezone
from pathlib import Path

RSS_SOURCES = [
    {"name": "OpenAI Blog",              "url": "https://openai.com/blog/rss.xml"},
    {"name": "HuggingFace Blog",         "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "Google DeepMind",          "url": "https://deepmind.google/blog/rss.xml"},
    {"name": "MIT Technology Review AI", "url": "https://www.technologyreview.com/feed/"},
    {"name": "VentureBeat AI",           "url": "https://venturebeat.com/category/ai/feed/"},
    {"name": "The Verge AI",             "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"},
    {"name": "Ars Technica AI",          "url": "https://feeds.arstechnica.com/arstechnica/technology-lab"},
    {"name": "36氪 AI",                  "url": "https://36kr.com/feed"},
    {"name": "量子位",                    "url": "https://www.qbitai.com/feed"},
]

DATA_FILE = Path(__file__).parent / "data" / "news.json"


def fetch_feed(source: dict) -> list[dict]:
    feed = feedparser.parse(source["url"])
    articles = []
    for entry in feed.entries[:5]:  # 每个来源最多取5条
        pub = entry.get("published_parsed") or entry.get("updated_parsed")
        published = datetime(*pub[:6], tzinfo=timezone.utc).isoformat() if pub else datetime.now(timezone.utc).isoformat()
        articles.append({
            "id": entry.get("id", entry.get("link", "")),
            "title": entry.get("title", ""),
            "link": entry.get("link", ""),
            "source": source["name"],
            "published": published,
            "summary_en": entry.get("summary", "")[:500],
            "summary_zh": "",  # 由 summarizer.py 填充
        })
    return articles


def load_existing() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            articles = json.load(f)
        return {a["id"]: a for a in articles}
    return {}


def save_articles(articles: list[dict]):
    DATA_FILE.parent.mkdir(exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def scrape_all() -> list[dict]:
    existing = load_existing()
    new_articles = []

    for source in RSS_SOURCES:
        try:
            fetched = fetch_feed(source)
            for article in fetched:
                if article["id"] not in existing:
                    new_articles.append(article)
                    existing[article["id"]] = article
            print(f"[OK] {source['name']}: fetched {len(fetched)} articles")
        except Exception as e:
            print(f"[ERR] {source['name']}: {e}")

    # 按时间排序，保留最新200条
    all_articles = sorted(existing.values(), key=lambda x: x["published"], reverse=True)[:200]
    save_articles(all_articles)

    print(f"\n新增 {len(new_articles)} 条，共 {len(all_articles)} 条")
    return new_articles


if __name__ == "__main__":
    scrape_all()
