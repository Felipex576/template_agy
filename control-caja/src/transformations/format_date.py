from datetime import datetime, date, timedelta
import holidays_co as hc
from typing import List, Tuple

@staticmethod
def to_date(value: str) -> date:
    """Converts a formatted string to date object."""
    return datetime.strptime(value, '%Y-%m-%d').date()

class FormatDate:
    """Normalize report dates to the last day of the month."""

    @staticmethod
    def parse_report_date(report_date: str) -> date:
        """
        Convert an ISO date or timestamp string into a date object.

        Args:
            report_date (str): Report date as an ISO date or timestamp string.

        Returns:
            date: Parsed report date.
        """
        return datetime.fromisoformat(report_date.replace("Z", "+00:00")).date()

    @staticmethod
    def is_business_day(target_date: date) -> bool:
        """Check if a given date is a business day (weekday and non-holiday in Colombia)."""
        if target_date.weekday() >= 5:
            return False
        if hasattr(hc, "is_holiday_date"):
            return not hc.is_holiday_date(target_date)
        elif hasattr(hc, "get_colombia_holidays_by_year"):
            holidays = [
                h.date if hasattr(h, "date") else h
                for h in hc.get_colombia_holidays_by_year(target_date.year)
            ]
            return target_date not in holidays
        return True

    @staticmethod
    def get_business_days(report_date: date) -> tuple[date, date]:
        """
        Calculate the next business day and previous business day for a given date.

        Args:
            report_date (date): Target report date.

        Returns:
            tuple[date, date]: Next business day and previous business day.
        """
        if isinstance(report_date, date) and not isinstance(report_date, date):
            report_date = report_date.isoformat()

        # Calculate next business day
        next_day = report_date + timedelta(days=1)
        while not FormatDate.is_business_day(next_day):
            next_day += timedelta(days=1)

        # Calculate previous business day
        prev_day = report_date - timedelta(days=1)
        while not FormatDate.is_business_day(prev_day):
            prev_day -= timedelta(days=1)

        return next_day, prev_day

    @staticmethod
    def is_friday_or_month_end(report_date: date) -> bool:
        """Check if the given report date is a Friday or the end of the month."""
        is_friday = report_date.weekday() == 4
        is_month_end = (report_date + timedelta(days=1)).month != report_date.month
        return is_friday or is_month_end

    @staticmethod
    def get_last_business_days(report_date: date, count: int = 4) -> list[date]:
        """
        Calculate the last business days prior to report_date and return them in chronological order.

        Args:
            report_date (date): Target report date.
            count (int, optional): Number of previous business days. Defaults to 4.

        Returns:
            list[date]: List containing previous business days and report_date.
        """
        previous_days = []
        current_day = report_date - timedelta(days=1)
        while len(previous_days) < count:
            if FormatDate.is_business_day(current_day):
                previous_days.append(current_day)
            current_day -= timedelta(days=1)

        previous_days.reverse()
        previous_days.append(report_date)
        return previous_days

    def get_all_dates(self, date_lists: List) -> Tuple[List, List]:
        """
        Calculates lists of previous and next business days for a given list of dates.

        Args:
            date_lists (List): List of target business dates.

        Returns:
            Tuple[List, List]: List of previous business days and list of next business days.
        """
        previous_list = []
        next_list = []
        
        for item_date in date_lists: 
            next_date, previous_date = self.get_business_days(item_date)
            next_list.append(next_date)
            previous_list.append(previous_date)
        
        return previous_list, next_list 
        
        
