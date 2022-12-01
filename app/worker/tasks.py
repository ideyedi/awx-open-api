import time

<<<<<<< HEAD
from celery import Celery, states

from .awx import AnsibleCrawler
from app.errors import AWXLoginFailException
=======
from celery import Celery

from .awx import AnsibleCrawler
>>>>>>> 59b144e169f077cadef673161dcf97775c1f0a10

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

<<<<<<< HEAD
    response = crawler.make_inventory()

    if not response:
        raise AWXLoginFailException

    return response
=======
    return ret
>>>>>>> 59b144e169f077cadef673161dcf97775c1f0a10
