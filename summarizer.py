import anthropic
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DATA_FILE = Path(__file__).parent / "data" / "news.json"

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def summarize_article(title: str, content: str) -> str:
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": (
                    f"请用简洁的中文（100字以内）总结以下 AI 资讯，"
                    f"直接给出摘要，不要说'这篇文章'或'本文'之类的开头：\n\n"
                    f"标题：{title}\n内容：{content}"
                ),
            }
        ],
    )
    return message.content[0].text.strip()


def summarize_pending():
    if not DATA_FILE.exists():
        print("还没有数据，请先运行 scraper.py")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        articles = json.load(f)

    pending = [a for a in articles if not a.get("summary_zh")]
    print(f"需要生成摘要：{len(pending)} 条")

    for i, article in enumerate(articles):
        if article.get("summary_zh"):
            continue
        try:
            zh = summarize_article(article["title"], article["summary_en"])
            article["summary_zh"] = zh
            print(f"[{i+1}/{len(pending)}] {article['title'][:40]}...")
        except Exception as e:
            print(f"[ERR] {article['title'][:40]}: {e}")
            article["summary_zh"] = ""

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print("摘要生成完成")


if __name__ == "__main__":
    summarize_pending()
