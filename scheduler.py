from apscheduler.schedulers.background import BackgroundScheduler
from scraper import scrape_all
from summarizer import summarize_pending
import time


def update_job():
    print("[Scheduler] 开始更新...")
    new = scrape_all()
    summarize_pending()
    print(f"[Scheduler] 完成，新增 {len(new)} 条")


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    # 每6小时自动更新一次
    scheduler.add_job(update_job, "interval", hours=6, id="update")
    scheduler.start()

    print("定时任务已启动，每6小时更新一次。按 Ctrl+C 停止。")
    print("立即执行一次...")
    update_job()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        scheduler.shutdown()
        print("已停止")
