import time
from celery import Celery
from .awx import AnsibleCrawler
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
    time.sleep(1)
    ret = crawler.make_inventory()

    return ret


if __name__ == "__main__":
    print(f'Test Code')
