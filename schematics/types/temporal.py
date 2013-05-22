from __future__ import absolute_import

import datetime
from time import mktime

try:
    from dateutil.tz import tzutc, tzlocal
except ImportError:
    raise ImportError(
        'Using the datetime fields requires the dateutil library. '
        'You can obtain dateutil from http://labix.org/python-dateutil'
    )

from .base import DateTimeType


class TimeStampType(DateTimeType):
    """Variant of a datetime field that saves itself as a unix timestamp (int)
    instead of a ISO-8601 string.
    """

    def __set__(self, instance, value):
        """Will try to parse the value as a timestamp.  If that fails it
        will fallback to DateTimeType's value parsing.

        A datetime may be used (and is encouraged).
        """
        if not value:
            return

        try:
            value = TimeStampType.timestamp_to_date(value)
        except TypeError:
            pass

        super(TimeStampType, self).__set__(instance, value)

    @classmethod
    def timestamp_to_date(cls, value):
        return datetime.datetime.fromtimestamp(value, tz=tzutc())

    @classmethod
    def date_to_timestamp(cls, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=tzlocal())
        return int(round(mktime(value.astimezone(tzutc()).timetuple())))

    def to_primitive(self, value):
        v = TimeStampType.date_to_timestamp(value)
        return v
