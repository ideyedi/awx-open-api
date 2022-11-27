import time
from celery import (Celery,
                    Task,
                    )
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


@celery.task
class callbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print(f'on success: {retval}')
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print(f'on failure: {exc}')
        pass

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        print(f'on retry: {exc}')
        pass