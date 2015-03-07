from datetime import datetime

import pytest

try:
    from dateutil.tz import gettz, tzutc
except ImportError:
    gettz = tzutc = None
else:
    from schematics.types.temporal import TimeStampType

    EPOCH = datetime(1970, 1, 1, 0, 0, tzinfo=tzutc())

pytestmark = pytest.mark.skipif(tzutc is None,
                                reason='requires python-dateutil')


def test_timezone_to_date():
    date = TimeStampType.timestamp_to_date(0)
    assert date == EPOCH

    date = TimeStampType.timestamp_to_date(1399588840)
    assert date == datetime(2014, 5, 8, 22, 40, 40, tzinfo=tzutc())


def test_date_to_timestamp():
    assert TimeStampType.date_to_timestamp(EPOCH) == 0

    ts = TimeStampType.date_to_timestamp(datetime(2014, 5, 8, 22, 40, 40, tzinfo=tzutc()))
    assert ts == 1399588840.0

    ts = TimeStampType.date_to_timestamp(
        datetime(2014, 5, 8, 22, 40, 40, tzinfo=gettz('PST8PDT')))
    assert ts == 1399614040.0


def test_date_to_primitive():
    tsobj = TimeStampType()

    assert tsobj.to_primitive(EPOCH) == 0

    ts = tsobj.to_primitive(datetime(2014, 5, 8, 22, 40, 40, tzinfo=tzutc()))
    assert ts == 1399588840.0

    ts = tsobj.to_primitive(datetime(2014, 5, 8, 22, 40, 40, tzinfo=gettz('PST8PDT')))
    assert ts == 1399614040.0
