import glob
import zipfile
import os
import sqlite3 as db
import threading
from datetime import date
from pathlib import Path
from typing import Union

from structs.result import Result
from util.logger import CLogger

ERROR = Result.ERROR
SUCCESS = Result.SUCCESS

log = CLogger().get_logger()

project_root = Path(__file__).resolve().parent.parent
default_db = str(project_root / "app.db")
backups_dir = project_root / "backups"
db_schema = project_root / "schema.sql"
today = date.today().isoformat()


class DBInterface:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
                    cls._instance.connection = None
                    cls._instance.cursor = None
                    cls._instance.DB = None
        return cls._instance

    @classmethod
    def reset_instance(cls):
        if cls._instance:
            if cls._instance.connection:
                cls._instance.connection.close()
            cls._instance.connection = None
            cls._instance.cursor = None
            cls._instance.DB = None
        cls._instance = None

    def connect(self, db_name: str = default_db, force: bool = False):
        if self.connection and not force:
            return
        if self.connection:
            self.connection.close()
        self.connection = db.connect(db_name)
        log.info("Successfully connected to db")
        self.cursor = self.connection.cursor()
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.connection.set_trace_callback(True)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    def __init__(self):
        if self.DB is None:
            self.DB = default_db
            self.initialize_db()

        elif self.DB != default_db:
            log.warning(
                f"Ignored attempt to reinitialize DBInterface with a different path: {self.DB}"
            )

    def initialize_db(self) -> Result:
        """
        Fault tolerant database initializer.
        If `app.db` is not found the last saved backup will be used.
        If there are no backups, it'll create an empty database with
        the default schema.
        """

        sql = self.__read_db_schema()

        if not Path(default_db).exists():
            log.warning(
                "Default DB not found. Attempting restore from backup...")
            result = self.__restore_from_backup()

            if result == ERROR:
                log.error("No backups found. Starting blank database...")
                return self.__db_not_found(sql=sql)

            return result

        else:
            self.connect(db_name=self.DB)

            return SUCCESS

    def __read_db_schema(self) -> Union[list[str], Result]:
        try:
            with open(str(db_schema), "r") as sql_file:
                sql_script = sql_file.read()

            sql_commands = sql_script.split(";")

            return sql_commands

        except Exception as e:
            log.error(
                "Failed to read DB schema: %s | %s",
                type(e).__name__, e.args
            )
            return ERROR

    def __db_not_found(self, sql) -> Result:
        result = self.__run_sql_batch(sql_statements=sql)
        if result == ERROR:
            log.error("Failed to initialize db")
            return ERROR

        log.info("Database schema initialized successfully.")

        self.connect(db_name=default_db)

        return SUCCESS

    def initialize_db_from_zip(self, path_to_zip: str) -> Result:
        """
        Takes path to compressed dump file and hot swaps db from it (*.zip).
        """
        dump_path = Path(path_to_zip)

        try:
            if dump_path.exists():
                log.info("Found dump file: %s", dump_path)

            else:
                raise FileNotFoundError

            self.reset_instance()

            if Path(default_db).exists():
                os.remove(Path(default_db))

            with zipfile.ZipFile(dump_path, 'r') as zip_ref:
                file_names = zip_ref.namelist()

                if len(file_names) != 1:
                    raise zipfile.BadZipFile

                sql_filename = file_names[0]

                # Read the .sql file content
                with zip_ref.open(sql_filename) as sql_file:
                    sql_script = sql_file.read().decode('utf-8')

            self.connect()
            self.connection.executescript(sql_script)
            self.connection.commit()
            self.DB = default_db

            log.info("Successfully initialized DB from dump file: %s",
                     dump_path.name)

            return SUCCESS

        except FileNotFoundError:
            log.error("Dump file not found: %s", path_to_zip)
            return ERROR

        except zipfile.BadZipFile as e:
            log.error(
                "Failed to open zip file: %s | %s",
                type(e).__name__, e.args
            )
            return ERROR

        except (OSError, db.DatabaseError) as e:
            log.error(
                "Failed to restore DB from dump: %s | %s",
                type(e).__name__, e.args
            )
            return ERROR

        except Exception as e:
            log.exception(
                "Unexpected error during DB initialization from dump: %s", e)
            return ERROR

    def __restore_from_backup(self) -> Union[list[str, Result], Result]:
        try:
            log.warning("Attempting to restore app.db from latest backup")

            # Get latest backup from `backup` directory.
            latest_backup_path = self.__get_latest_backup_path()

            if latest_backup_path == ERROR:
                log.critical("Failed to find a backup.")
                raise FileNotFoundError

            self.initialize_db_from_zip(path_to_zip=latest_backup_path)

            log.info("Successfully restored app.db")
            return ["Restored database from last backup", SUCCESS]

        except Exception as restore_error:
            log.critical(
                "Failed to restore backup DB: %s | %s",
                type(restore_error).__name__,
                restore_error.args,
            )

            return ERROR

    def __get_latest_backup_path(self) -> Union[Path, Result]:
        try:
            list_of_files = glob.glob(os.path.join(backups_dir, "*"))

            if not list_of_files:
                log.critical("No backups were found in: %s", backups_dir)
                raise ERROR

            latest_file = max(list_of_files, key=os.path.getmtime)

            if len(list_of_files) > 26:
                earliest_file = min(list_of_files, key=os.path.getmtime)
                os.remove(earliest_file)

            if latest_file and self.check_file_extension(latest_file, ".zip"):
                log.info("LATEST BACKUP: %s", latest_file)
                return Path(latest_file)

            else:
                raise ERROR

        except OSError as e:
            log.critical(
                "Failed to get latest backup: %s | %s",
                type(e).__name__,
                e.args,
            )
            return ERROR

    def check_file_extension(path_to_file: Path, extension: str):
        filename = str(path_to_file.name)
        return filename.split(".")[1].lower() == extension.lower()

    def dump_db_and_zip(self,
                        output_dir: str = backups_dir) -> Union[str, Result]:
        """
        Creates a dump file from the database and compresses
        the file to the specified directory.
        """

        self.__ensure_connection()

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        archive_name = f"backup_for_{today}.zip"
        output_path = output_dir / archive_name
        dump = ""

        try:
            list_of_files = glob.glob(os.path.join(backups_dir, "*"))

            if not list_of_files:
                raise FileNotFoundError(list_of_files)

            if len(list_of_files)+25 > 26:
                earliest_file = min(list_of_files, key=os.path.getmtime)
                os.remove(earliest_file)

        except Exception as e:
            log.critical(
                "Couldn't find any backups: %s | %s",
                type(e).__name__,
                e.args,
            )

        try:
            for line in self.connection.iterdump():
                dump += line + "\n"

            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("dump.sql", dump)

            return str(output_path)

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )
            return ERROR

    def save_employee(self, args: tuple, BUILD: str = "TEST") -> Result:
        sql = """
        INSERT OR IGNORE INTO Employee
        (FirstName, MiddleName, LastName, EmployeeGroup)
        VALUES (?, ?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def save_pay_period(self, args: tuple, BUILD: str = "TEST") -> Result:
        sql = """
        INSERT OR IGNORE INTO PayPeriod
        (EmployeeID, StartDate, EndDate)
        VALUES (?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def save_work_entry(self, args: tuple, BUILD: str = "TEST") -> Result:
        sql = """
        INSERT OR IGNORE INTO WorkEntry
        (PayPeriodID, WorkDate, Hours)
        VALUES (?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def save_comment(self, args: tuple, BUILD: str = "TEST") -> Result:
        """
        This saves an entry even if it already exists.
        """
        sql = """
        INSERT OR IGNORE INTO PayPeriodComment
        (PayPeriodID, EmployeeID, WorkDate, PunchInComment, PunchOutComment, SpecialPayComment)
        VALUES (?, ?, ?, ?, ?, ?);
        """

        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def delete_employee(self, args: tuple, BUILD: str = "TEST") -> Result:
        sql = """
        DELETE FROM Employee
        WHERE
        FirstName=? AND MiddleName=? AND LastName=? AND EmployeeGroup=?;
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def delete_work_entry(self, args: tuple, BUILD: str = "TEST") -> Result:
        sql = """
        DELETE FROM WorkEntry
        WHERE
        PayPeriodID=?;
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    # READ METHODS

    def _read_employee_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT EmployeeID
        FROM Employee
        WHERE FirstName=? AND MiddleName=? AND LastName=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_employee_name(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee
        WHERE EmployeeID=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
            SELECT PayPeriodID
            FROM PayPeriod
            WHERE EmployeeID=? AND StartDate=?;
            """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_id_by_date(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT PayPeriodID
        FROM PayPeriod
        WHERE StartDate=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_work_entry_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT WorkEntryID
        FROM WorkEntry
        WHERE PayPeriodID=? AND WorkDate=? AND Hours=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_comment_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT CommentID
        FROM PayPeriodComment
        WHERE PayPeriodID=? AND EmployeeID=? AND WorkDate=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_ids(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT PayPeriodID
        FROM PayPeriod
        WHERE StartDate=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_employee_ids(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT EmployeeID
        FROM PayPeriod
        WHERE PayPeriodID=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_work_entries(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        sql = """
        SELECT WorkDate, Hours
        FROM WorkEntry
        WHERE PayPeriodID=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_dates(self, BUILD: str = "TEST") -> Union[list[tuple], Result]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod
        WHERE EXISTS (SELECT DISTINCT StartDate FROM PayPeriod);
        """

        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def _default_employee(self, BUILD: str = "TEST") -> Union[list[tuple], Result]:
        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee ORDER BY ROWID ASC LIMIT 1;
        """
        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def _default_date(self, BUILD: str = "TEST") -> Union[list[tuple], Result]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod ORDER BY StartDate LIMIT 1;
        """
        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def __run_sql(self, sql: str, args: tuple, BUILD: str = "TEST") -> Result:
        self.__ensure_connection()

        try:
            self.cursor.execute(sql, args or ())
            self.connection.commit()
            return SUCCESS

        except db.Error as e:
            log.error(
                "__run_sql error: %s | %s | %s | %s",
                type(e).__name__,
                e.args,
                sql,
                args,
            )
            return ERROR

    def __run_sql_batch(self, sql_statements: list[str], BUILD: str = "TEST") -> Result:
        self.__ensure_connection()

        try:
            for statement in sql_statements:
                self.cursor.execute(statement)
            self.connection.commit()
            return SUCCESS
        except db.Error as e:
            log.error("__run_sql error: %s | %s", type(e).__name__, e.args)
            return ERROR

    def __run_sql_read(
        self, sql: str, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], Result]:
        self.__ensure_connection()

        try:
            self.cursor.execute(sql, args or ())
            results = self.cursor.fetchall()
            self.connection.commit()
            return results
        except db.Error as e:
            log.error("__run_sql error: %s | %s | %s",
                      type(e).__name__, e.args, sql)
            return ERROR

    def __ensure_connection(self):
        if not self.connection:
            if not getattr(self, "DB", None):
                raise ValueError(
                    "No DB path specified. Cannot establish connection.")
            self.connect(self.DB)
