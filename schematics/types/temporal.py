import datetime

try:
    from dateutil.tz import tzutc, tzlocal
except ImportError:  # pragma: no cover
    raise ImportError(
        'Using the datetime fields requires the dateutil library. '
        'You can obtain dateutil from http://labix.org/python-dateutil'
    )

from .base import DateTimeType

EPOCH = datetime.datetime.utcfromtimestamp(0).replace(tzinfo=tzutc())


class TimeStampType(DateTimeType):

    """Variant of a datetime field that saves itself as a unix timestamp (int)
    instead of a ISO-8601 string.
    """

    @classmethod
    def timestamp_to_date(cls, value):
        return datetime.datetime.fromtimestamp(value, tz=tzutc())

    @classmethod
    def date_to_timestamp(cls, value):
        if value.tzinfo is None:
            value = value.replace(tzinfo=tzlocal())
        delta = value - EPOCH
        return (delta.days * 24 * 3600) + delta.seconds + delta.microseconds

    def to_primitive(self, value, context=None):
        return TimeStampType.date_to_timestamp(value)
