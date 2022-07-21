from sqlalchemy import DateTime as sqlalchemyDateTime
from sqlalchemy import TypeDecorator
from datetime import datetime
import pytz

utc = pytz.utc
local_tz = pytz.timezone("Asia/Seoul")


class DateTime(TypeDecorator):
    impl = sqlalchemyDateTime

    def process_bind_param(self, value, engine):
        return value

    def process_result_value(self, value: datetime, engine):
        return value.replace(tzinfo=utc).astimezone(local_tz)
