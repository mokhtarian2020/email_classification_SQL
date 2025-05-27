# scheduler.py
from apscheduler.schedulers.blocking import BlockingScheduler
from email_reader import check_and_classify

def start_scheduler():
    scheduler = BlockingScheduler()
    scheduler.add_job(check_and_classify, "interval", minutes=5)
    print("🕐 Scheduler running (every 5 minutes).")
    scheduler.start()
