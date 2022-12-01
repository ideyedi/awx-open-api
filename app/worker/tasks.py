import time

from celery import Celery, states

from .awx import AnsibleCrawler
from app.errors import AWXLoginFailException

celery = Celery('task',
                broker='redis://localhost:6379/0',
                backend='redis://localhost:6379/0'
                )


@celery.task
def add(x, y):
    time.sleep(10)
    return x + y


@celery.task
def make_sourced_inventory(app_name, profile, project):
    crawler = AnsibleCrawler(app_name, profile, project)
    crawler.driver.get(crawler.target_url)

    # Web refresh time
    time.sleep(1)

    response = crawler.make_inventory()

    if not response:
        raise AWXLoginFailException

    return response
