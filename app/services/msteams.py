import pymsteams

from ..config import get_settings


class Teams:
    url: str

    def __init__(self):
        settings = get_settings()
        self.url = settings.pipeline_webhook

    def info(self, msg: str):
        teams_msg = pymsteams.connectorcard(self.url)
        teams_msg.text(msg)
        teams_msg.color("0080ff")
        teams_msg.send()

    def error(self, msg: str):
        teams_msg = pymsteams.connectorcard(self.url)
        teams_msg.text(msg)
        teams_msg.color("ff00ff")
        teams_msg.send()
