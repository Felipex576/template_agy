"""Unit tests for FormatDate transformation component."""

from datetime import date, datetime
import pytest

from src.transformations.format_date import FormatDate, to_date


@pytest.fixture
def format_date():
    return FormatDate()


def test_to_date():
    assert to_date("2026-01-09") == date(2026, 1, 9)


def test_is_business_day(format_date):
    # Friday, Jan 9 2026 is business day
    assert format_date.is_business_day(date(2026, 1, 9)) is True

    # Saturday, Jan 10 2026 is weekend
    assert format_date.is_business_day(date(2026, 1, 10)) is False

    # Sunday, Jan 11 2026 is weekend
    assert format_date.is_business_day(date(2026, 1, 11)) is False

    # Jan 1 2026 is holiday (New Year)
    assert format_date.is_business_day(date(2026, 1, 1)) is False


def test_is_friday_or_month_end(format_date):
    # Friday
    assert format_date.is_friday_or_month_end(date(2026, 1, 9)) is True

    # Thursday not month end
    assert format_date.is_friday_or_month_end(date(2026, 1, 8)) is False

    # Month end (Jan 31 2026 is Saturday -> next day is Feb 1)
    assert format_date.is_friday_or_month_end(date(2026, 1, 31)) is True


def test_parse_report_date(format_date):
    parsed = format_date.parse_report_date("2026-01-09T05:00:00.000Z")
    assert parsed == date(2026, 1, 9)

    parsed_simple = format_date.parse_report_date("2026-01-09")
    assert parsed_simple == date(2026, 1, 9)


def test_get_business_days(format_date):
    next_day, prev_day = format_date.get_business_days(date(2026, 1, 9))
    assert isinstance(next_day, date)
    assert isinstance(prev_day, date)
    assert prev_day == date(2026, 1, 8)
    assert format_date.is_business_day(next_day) is True
    assert format_date.is_business_day(prev_day) is True


def test_get_last_business_days(format_date):
    # Default count is 4, which returns 4 previous business days + report_date = 5 items
    days = format_date.get_last_business_days(date(2026, 1, 9))
    assert len(days) == 5
    assert days[-1] == date(2026, 1, 9)
    for d in days:
        assert format_date.is_business_day(d) is True

    days_two = format_date.get_last_business_days(date(2026, 1, 9), count=2)
    assert len(days_two) == 3


def test_get_all_dates(format_date):
    date_list = [date(2026, 1, 9), date(2026, 1, 8)]
    prev_list, next_list = format_date.get_all_dates(date_list)

    assert len(prev_list) == 2
    assert len(next_list) == 2
    assert prev_list[0] == date(2026, 1, 8)
    assert prev_list[1] == date(2026, 1, 7)
