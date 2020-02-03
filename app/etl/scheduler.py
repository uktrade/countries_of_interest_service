import atexit

from apscheduler.schedulers.background import BackgroundScheduler


class Scheduler:
    def __init__(self, populate_database_task):
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(
            populate_database_task, 'cron', hour='21',
        )
        atexit.register(lambda: self.scheduler.shutdown(wait=False))

    def start(self):
        self.scheduler.start()
