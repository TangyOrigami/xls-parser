import aiosqlite
import os
import zipfile
import glob
from datetime import date
from pathlib import Path
from typing import Union

from structs.result import Result
from util.logger import CLogger

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS

log = CLogger().get_logger()

project_root = Path(__file__).resolve().parent.parent
default_db = project_root / "app.db"
backups_dir = project_root / "backups"
db_schema = project_root / "schema.sql"
today = date.today().isoformat()


class AsyncDBInterface:
    def __init__(self):
        self.db_path = str(default_db)
        self.connection = None

    async def __aenter__(self):
        self.connection = await aiosqlite.connect(self.db_path)
        await self.connection.execute("PRAGMA foreign_keys = ON;")
        self.connection.row_factory = aiosqlite.Row
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.connection:
            await self.connection.close()

    async def __run_sql(self, sql: str, args: tuple = ()) -> Result:
        try:
            async with self.connection.execute(sql, args):
                await self.connection.commit()

            return SUCCESS

        except Exception as e:
            log.error("__run_sql error: %s | %s", sql, e)
            return ERROR

    async def __run_sql_read(self, sql: str, args: tuple = ()) -> Union[list[tuple], Result]:
        try:
            async with self.connection.execute(sql, args) as cursor:
                rows = await cursor.fetchall()

            return [tuple(row) for row in rows]

        except Exception as e:
            log.error("__run_sql_read error: %s | %s", sql, e)
            return ERROR

    async def close(self):
        try:
            if self.connection:
                await self.connection.close()
                self.connection = None

            return SUCCESS

        except Exception as e:
            log.error("__run_sql_read error: %s", e)
            return ERROR

    @staticmethod
    def db_file_exists_and_valid(path: Union[str, Path]) -> bool:
        path = Path(path)
        if not path.exists():
            return False

        try:
            import sqlite3
            with sqlite3.connect(path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table';")
                tables = {row[0] for row in cursor.fetchall()}
                expected = {"Employee", "PayPeriod",
                            "WorkEntry", "PayPeriodComment", "Meta"}
                return expected.issubset(tables)
        except Exception as e:
            log.error("Validation error: %s", e)
            return False

    async def initialize_db(self) -> Result:
        if not self.db_file_exists_and_valid(self.db_path):
            log.warning("Invalid or missing DB. Attempting recovery...")

            result = await self.restore_from_backup()
            if result == ERROR:
                log.warning("No backups found. Starting blank database...")
                async with aiosqlite.connect(self.db_path) as conn:
                    with open(str(db_schema), "r") as f:
                        script = f.read()
                    await conn.executescript(script)
                    await conn.commit()
                    log.info("Database schema initialized successfully.")
                return SUCCESS

            return result

        return SUCCESS

    async def create_from_schema(self) -> Result:
        log.info("Running DB schema script:\n%s", db_schema)

        try:
            with open(str(db_schema), "r") as f:
                script = f.read()
                log.info("Running DB schema script:\n%s", script)

            if self.connection:
                await self.connection.close()
                self.connection = None

                await self.connection.executescript(script)
                await self.connection.commit()

                log.info("Database schema initialized successfully.")
                return SUCCESS

        except Exception as e:
            log.error("Failed to initialize DB from schema: %s", e)
            return ERROR

    async def restore_from_backup(self) -> Result:
        log.info("RESTORING")

        try:
            latest = self.get_latest_backup_path()
            log.info(latest)
            if latest == ERROR:
                raise FileNotFoundError("No backup found.")

            await self.initialize_db_from_zip(latest)
            return SUCCESS

        except Exception as e:
            log.critical("restore_from_backup failed: %s | %s",
                         type(e).__name__, e.args)
            return ERROR

    def get_latest_backup_path(self) -> Union[Path, Result]:
        try:
            files = glob.glob(os.path.join(backups_dir, "*.zip"))
            if not files:
                return ERROR

            latest = max(files, key=os.path.getmtime)

            # Trim oldest backups if over limit
            if len(files) > 26:
                os.remove(min(files, key=os.path.getmtime))

            return Path(latest)

        except Exception as e:
            log.critical("get_latest_backup_path error: %s | %s",
                         type(e).__name__, e.args)
            return ERROR

    async def initialize_db_from_zip(
            self,
            zip_path: Union[str, Path]
    ) -> Result:
        try:
            if self.connection:
                await self.connection.close()
                self.connection = None

            if Path(self.db_path).exists():
                os.remove(self.db_path)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                dump_files = zf.namelist()

                if not dump_files:
                    raise ValueError("Zip archive is empty.")

                if len(dump_files) > 1:
                    raise ValueError("Zip archive is not valid.")

                log.info("Executing: %s", dump_files[0])
                sql = zf.read(dump_files[0]).decode("utf-8")

            async with aiosqlite.connect(self.db_path) as conn:
                await conn.executescript(sql)
                await conn.commit()

            log.info("Successfully initialized DB from dump.")

            return SUCCESS

        except Exception as e:
            log.error("initialize_db_from_zip failed: %s | %s",
                      type(e).__name__, e.args)
            return ERROR

    async def dump_db_and_zip(
            self,
            output_dir: Union[str, Path] = backups_dir
    ) -> Union[str, Result]:

        log.info("%s", output_dir)
        output_dir = Path(output_dir).absolute()
        output_dir.mkdir(parents=True, exist_ok=True)
        archive_path = output_dir / f"backup_for_{today}.zip"
        dump = ""

        try:
            async for line in self.connection.iterdump():
                dump += f"{line}\n"

        except Exception as e:
            log.error("dump_db_and_zip error: %s | %s",
                      type(e).__name__, e.args)
            return ERROR

        finally:

            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("dump.sql", dump)

            return str(archive_path)

    async def save_employee(self, args: tuple) -> Result:
        sql = """
        INSERT OR IGNORE INTO Employee
        (FirstName, MiddleName, LastName, EmployeeGroup)
        VALUES (?, ?, ?, ?);
        """
        return await self.__run_sql(sql=sql, args=args)

    async def save_pay_period(self, args: tuple) -> Result:
        sql = """
        INSERT OR IGNORE INTO PayPeriod
        (EmployeeID, StartDate, EndDate)
        VALUES (?, ?, ?);
        """
        return await self.__run_sql(sql=sql, args=args)

    async def save_work_entry(self, args: tuple) -> Result:
        sql = """
        INSERT OR IGNORE INTO WorkEntry
        (PayPeriodID, WorkDate, Hours)
        VALUES (?, ?, ?);
        """
        return await self.__run_sql(sql=sql, args=args)

    async def save_comment(self, args: tuple) -> Result:
        """
        This saves an entry even if it already exists.
        """
        sql = """
        INSERT OR IGNORE INTO PayPeriodComment (
            PayPeriodID, EmployeeID, WorkDate,
            PunchInComment, PunchOutComment, SpecialPayComment
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(EmployeeID, WorkDate, PunchInComment, PunchOutComment, SpecialPayComment)
        DO NOTHING;
        """

        return await self.__run_sql(sql=sql, args=args)

    async def delete_employee(self, args: tuple) -> Result:
        sql = """
        DELETE FROM Employee
        WHERE
        FirstName=? AND MiddleName=? AND LastName=? AND EmployeeGroup=?;
        """
        return await self.__run_sql(sql=sql, args=args)

    async def delete_work_entry(self, args: tuple) -> Result:
        sql = """
        DELETE FROM WorkEntry
        WHERE
        PayPeriodID=?;
        """
        return await self.__run_sql(sql=sql, args=args)

    # READ METHODS

    async def _read_employee_id(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT EmployeeID
        FROM Employee
        WHERE FirstName=? AND MiddleName=? AND LastName=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_employee_name(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee
        WHERE EmployeeID=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_pay_period_id(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
            SELECT PayPeriodID
            FROM PayPeriod
            WHERE EmployeeID=? AND StartDate=?;
            """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_pay_period_id_by_date(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT PayPeriodID
        FROM PayPeriod
        WHERE StartDate=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_work_entry_id(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT WorkEntryID
        FROM WorkEntry
        WHERE PayPeriodID=? AND WorkDate=? AND Hours=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_comment_id(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT CommentID
        FROM PayPeriodComment
        WHERE PayPeriodID=? AND EmployeeID=? AND WorkDate=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_pay_period_ids(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT PayPeriodID
        FROM PayPeriod
        WHERE StartDate=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_employee_ids(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT EmployeeID
        FROM PayPeriod
        WHERE PayPeriodID=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_work_entries(
        self, args: tuple
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT WorkDate, Hours
        FROM WorkEntry
        WHERE PayPeriodID=?;
        """
        return await self.__run_sql_read(sql=sql, args=args)

    async def _read_pay_period_dates(self) -> Union[list[tuple], Result]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod
        WHERE EXISTS (SELECT DISTINCT StartDate FROM PayPeriod);
        """

        return await self.__run_sql_read(sql=sql, args=())

    async def _default_employee(self) -> Union[list[tuple], Result]:

        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee ORDER BY ROWID ASC LIMIT 1;
        """

        result = await self.__run_sql_read(sql=sql, args=())

        log.info("HIIMBEINGCALLED: %s", ' '.join(result[0]))

        return result

    async def _default_date(self) -> Union[list[tuple], Result]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod ORDER BY StartDate LIMIT 1;
        """
        return await self.__run_sql_read(sql=sql, args=())

    async def test_method(self, args: str = "ANGEL A ALANIZ"):
        return [i.lower() for i in args]
