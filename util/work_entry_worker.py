import re
from datetime import datetime, timedelta

from structs.work_entry import WorkEntry
from util.logger import CLogger

log = CLogger().get_logger()


class WorkEntryWorker:
    """
    Async Worker to handle Work Entries for a given pay period.
    """

    def __init__(self, pay_period_id: int, report: list, start_date: datetime, build: str):
        self.pay_period_id = pay_period_id
        self.report = report
        self.start_date = start_date
        self.end_date = start_date + timedelta(days=14)
        self.build = build

    def __extract_hrs(self) -> list[int]:
        return [row[1] for row in self.report if re.search(r"\d", row[0])]

    def __extract_report_dates(self) -> list[datetime.date]:
        dates = []
        for row in self.report:
            if re.search(r"\d", row[0]):
                date_str = row[0].split(" ", 1)[1] + f"/{self.start_date.year}"
                dates.append(datetime.strptime(date_str, "%m/%d/%Y").date())
        return dates

    def __weekday_filter(self) -> list[datetime.date]:
        days = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
        return [d for d in self.pay_period_dates() if d.strftime("%A") in days]

    def __weekend_filter(self) -> list[datetime.date]:
        days = {"Saturday", "Sunday"}
        return [d for d in self.pay_period_dates() if d.strftime("%A") in days]

    def __date_name(self, dates: list[datetime.date]) -> list[str]:
        return [d.strftime("%A") for d in dates]

    def extract_hrs_wrked(self) -> dict[datetime.date, int]:
        dates = self.__extract_report_dates()
        hrs = self.__extract_hrs()
        return {dates[i]: hrs[i] for i in range(len(dates))}

    async def extract_work_entries(self):
        """
        Asynchronously creates and returns WorkEntry objects.
        """
        raw_hrs = self.extract_hrs_wrked()
        counter = 0

        for work_date, hours in raw_hrs.items():
            counter += hours

            try:
                await WorkEntry.create(
                    pay_period_id=self.pay_period_id,
                    work_date=work_date,
                    hours=hours,
                    BUILD=self.build
                )

            except Exception as e:
                log.error(f"Failed to create WorkEntry: {e}")
                continue

    def extract_weekday_hrs(self) -> dict[datetime.date, int]:
        all_dates = self.extract_hrs_wrked()
        weekdays = self.__weekday_filter()
        return {d: all_dates[d] for d in weekdays if d in all_dates}

    def extract_weekend_hrs(self) -> dict[datetime.date, int]:
        all_dates = self.extract_hrs_wrked()
        weekends = self.__weekend_filter()
        return {d: all_dates[d] for d in weekends if d in all_dates}

    def extract_ot_logged(self) -> dict[datetime.date, int]:
        all_hrs = self.extract_hrs_wrked()
        total = sum(all_hrs.values())

        if total < 80.0:
            return {}

        overtime = {}
        weekday_hrs = self.extract_weekday_hrs()

        for d, hrs in weekday_hrs.items():
            excess = hrs - 8.0
            if excess > 0:
                overtime[d] = excess

        return overtime

    def pay_period_dates(self) -> list[datetime.date]:
        return [self.start_date + timedelta(days=i) for i in range(14)]
