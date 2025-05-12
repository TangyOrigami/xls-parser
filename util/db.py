import gzip
import os
import shutil
import sqlite3 as db
import threading
from datetime import date
from pathlib import Path
from typing import Union

from structs.result import Result as r
from util.logger import CLogger

log = CLogger().get_logger()


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

    def connect(self, db_name: str, force: bool = False):
        if self.connection and not force:
            return
        if self.connection:
            self.connection.close()
        self.connection = db.connect(db_name)
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

    def __init__(self, DB: str = "app.db"):
        log.warn("CURRENT DB: %s", DB)
        if not hasattr(self, "DB") or self.DB is None:
            self.DB = DB
            self.connect(DB)
        elif self.DB != DB:
            log.warning(
                f"Ignored attempt to reinitialize DBInterface with a different path: {DB}"
            )

    def initialize_db(self, BUILD: str = "TEST") -> r:
        SCHEMA_VERSION = "1.0"

        sql = [
            """
            CREATE TABLE IF NOT EXISTS Employee(
                EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
                FirstName TEXT NOT NULL,
                MiddleName TEXT,
                LastName TEXT NOT NULL,
                EmployeeGroup TEXT,
                UNIQUE(FirstName, MiddleName, LastName)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS PayPeriod(
                PayPeriodID INTEGER PRIMARY KEY AUTOINCREMENT,
                EmployeeID INTEGER NOT NULL,
                StartDate TEXT NOT NULL,
                EndDate TEXT NOT NULL,
                UNIQUE(EmployeeID, StartDate, EndDate),
                FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS WorkEntry(
                WorkEntryID INTEGER PRIMARY KEY AUTOINCREMENT,
                PayPeriodID INTEGER NOT NULL,
                WorkDate TEXT NOT NULL,
                Hours REAL NOT NULL CHECK(Hours >= 0.0),
                UNIQUE(PayPeriodID, WorkDate),
                FOREIGN KEY (PayPeriodID) REFERENCES PayPeriod(PayPeriodID) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS PayPeriodComment(
                CommentID INTEGER PRIMARY KEY AUTOINCREMENT,
                PayPeriodID INTEGER NOT NULL,
                EmployeeID INTEGER NOT NULL,
                WorkDate TEXT NOT NULL,
                PunchInComment TEXT,
                PunchOutComment TEXT,
                SpecialPayComment TEXT,
                FOREIGN KEY (PayPeriodID) REFERENCES PayPeriod(PayPeriodID) ON DELETE CASCADE,
                FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS Meta(
                Key TEXT PRIMARY KEY,
                Value TEXT
            )
            """,
            f"""
            INSERT OR REPLACE INTO Meta (Key, Value)
            VALUES ('SchemaVersion', '{SCHEMA_VERSION}')
            """,
        ]

        project_root = Path(__file__).resolve().parent.parent
        target_db_path = project_root / "app.db"
        backup_db_path = project_root / "app_backup.db"

        try:
            self.__ensure_connection()

            result = self.__run_sql_batch(sql_statements=sql, BUILD=BUILD)
            if result != r.SUCCESS:
                log.error("Failed to initialize db")
                raise Exception("Schema initialization failed")

            result = self.create_backup(
                target_db_path=target_db_path, backup_db_path=backup_db_path
            )
            if result == r.ERROR:
                log.error("Failed to create backup")
                raise Exception("Failed to create backup")

            log.info("Database schema initialized successfully.")
            return r.SUCCESS

        except Exception as e:
            log.error(
                "Failed to initialize DB schema: %s | %s", type(e).__name__, e.args
            )
            return self.restore_from_backup(backup_db_path, target_db_path)

    def create_backup(self, target_db_path, backup_db_path):
        try:
            if target_db_path.exists():
                if backup_db_path.exists():
                    backup_db_path.unlink()
                shutil.copy2(target_db_path, backup_db_path)
                log.info("Backed up app.db to app_backup.db")
            return r.SUCCESS
        except Exception as e:
            log.error("Failed to create backup: %s | %s", type(e).__name__, e.args)
            return r.ERROR

    def initialize_db_from_dump_file(self, path_to_file: str) -> r:
        project_root = Path(__file__).resolve().parent.parent
        target_db_path = project_root / "app.db"
        backup_db_path = project_root / "app_backup.db"

        try:
            dump_path = Path(str(path_to_file)).resolve(strict=True)
            log.info("Found dump file: %s", dump_path)

            # Backup existing database if it exists
            if target_db_path.exists():
                try:
                    if backup_db_path.exists():
                        backup_db_path.unlink()
                    shutil.copy2(target_db_path, backup_db_path)
                    log.info("Created backup: %s", backup_db_path.name)
                    target_db_path.unlink()
                except Exception as backup_err:
                    log.error(
                        "Backup process failed: %s | %s",
                        type(backup_err).__name__,
                        backup_err.args,
                    )
                    return r.ERROR
            else:
                log.info("No existing database to backup. Skipping.")

            # Read and execute dump SQL
            with gzip.open(dump_path, mode="rt", encoding="utf-8") as f:
                sql_script = f.read()

            self._reconnect_to(target_db_path)
            self.connection.executescript(sql_script)
            self.connection.commit()
            self.DB = str(target_db_path)

            log.info("Successfully initialized DB from dump: %s", dump_path.name)
            return r.SUCCESS

        except FileNotFoundError:
            log.error("Dump file not found: %s", path_to_file)

        except (OSError, db.DatabaseError) as e:
            log.error(
                "Failed to restore DB from dump: %s | %s", type(e).__name__, e.args
            )

        except Exception as e:
            log.exception("Unexpected error during DB initialization from dump: %s", e)

        return self.restore_from_backup(backup_db_path, target_db_path)

    def restore_from_backup(self, backup_db_path: Path, target_db_path: Path) -> r:
        try:
            log.warn("BACKUP PATH: %s", backup_db_path)
            if backup_db_path.exists():
                log.warning("Attempting to restore app.db from app_backup.db")

                if self.connection:
                    self.connection.close()
                    self.connection = None
                    self.cursor = None

                shutil.copy2(backup_db_path, target_db_path)

                self.connection = db.connect(str(target_db_path))
                self.cursor = self.connection.cursor()
                self.connection.execute("PRAGMA foreign_keys = ON;")
                self.connection.set_trace_callback(True)
                self.DB = str(target_db_path)

                log.info("Successfully restored app.db from app_backup.db")
                return r.ERROR
            else:
                log.critical("Backup DB not found. Manual recovery required.")
        except Exception as restore_error:
            log.critical(
                "Failed to restore backup DB: %s | %s",
                type(restore_error).__name__,
                restore_error.args,
            )
        return r.ERROR

    def dump_db_and_compress(
        self, BUILD: str = "TEST", path_to_file: str = "temp"
    ) -> Union[list[str, r], r]:
        self.__ensure_connection()

        output_dir = Path(path_to_file)
        output_dir.mkdir(parents=True, exist_ok=True)

        today = date.today().isoformat()
        filename = f"{BUILD.lower()}_dump_{today}.sql.gz"
        output_path = output_dir / filename

        try:
            with gzip.open(output_path, "wt", encoding="utf-8") as gz_file:
                for line in self.connection.iterdump():
                    log.info(line)
                    gz_file.write(f"{line}\n")

            return [str(output_path), r.SUCCESS]

        except Exception as e:
            log.error(
                "Error during dump and compression: %s | %s",
                type(e).__name__,
                e.args,
            )
            return r.ERROR

    def save_employee(self, args: tuple, BUILD: str = "TEST") -> r:
        sql = """
        INSERT OR IGNORE INTO Employee
        (FirstName, MiddleName, LastName, EmployeeGroup)
        VALUES (?, ?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def save_pay_period(self, args: tuple, BUILD: str = "TEST") -> r:
        sql = """
        INSERT OR IGNORE INTO PayPeriod
        (EmployeeID, StartDate, EndDate)
        VALUES (?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def save_work_entry(self, args: tuple, BUILD: str = "TEST") -> r:
        sql = """
        INSERT OR IGNORE INTO WorkEntry
        (PayPeriodID, WorkDate, Hours)
        VALUES (?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def save_comment(self, args: tuple, BUILD: str = "TEST") -> r:
        sql = """
        INSERT OR IGNORE INTO PayPeriodComment
        (PayPeriodID, EmployeeID, WorkDate,
        PunchInComment, PunchOutComment, SpecialPayComment)
        VALUES (?, ?, ?, ?, ?, ?);
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def delete_employee(self, args: tuple, BUILD: str = "TEST") -> r:
        sql = """
        DELETE FROM Employee
        WHERE
        FirstName=? AND MiddleName=? AND LastName=? AND EmployeeGroup=?;
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def delete_work_entry(self, args: tuple, BUILD: str = "TEST") -> r:
        sql = """
        DELETE FROM WorkEntry
        WHERE
        PayPeriodID=?;
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    def _reconnect_to(self, db_path: Path):
        """Reconnects the database to a new target path."""
        if self.connection:
            self.connection.close()
        self.connection = db.connect(str(db_path))
        self.cursor = self.connection.cursor()
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.connection.set_trace_callback(True)

    # READ METHODS

    def _read_employee_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT EmployeeID
        FROM Employee
        WHERE FirstName=? AND MiddleName=? AND LastName=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_employee_name(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee
        WHERE EmployeeID=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
            SELECT PayPeriodID
            FROM PayPeriod
            WHERE EmployeeID=? AND StartDate=?;
            """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_id_by_date(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT PayPeriodID
        FROM PayPeriod
        WHERE StartDate=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_work_entry_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT WorkEntryID
        FROM WorkEntry
        WHERE PayPeriodID=? AND WorkDate=? AND Hours=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_comment_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT CommentID
        FROM PayPeriodComment
        WHERE PayPeriodID=? AND EmployeeID=? AND WorkDate=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_ids(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT PayPeriodID
        FROM PayPeriod
        WHERE StartDate=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_employee_ids(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT EmployeeID
        FROM PayPeriod
        WHERE PayPeriodID=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_work_entries(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = """
        SELECT WorkDate, Hours
        FROM WorkEntry
        WHERE PayPeriodID=?;
        """
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_dates(self, BUILD: str = "TEST") -> Union[list[tuple], r]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod
        WHERE EXISTS (SELECT DISTINCT StartDate FROM PayPeriod);
        """

        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def _default_employee(self, BUILD: str = "TEST") -> Union[list[tuple], r]:
        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee ORDER BY ROWID ASC LIMIT 1;
        """
        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def _default_date(self, BUILD: str = "TEST") -> Union[list[tuple], r]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod ORDER BY StartDate LIMIT 1;
        """
        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def __run_sql(self, sql: str, args: tuple, BUILD: str = "TEST") -> r:
        self.__ensure_connection()

        try:
            self.cursor.execute(sql, args or ())
            self.connection.commit()
            return r.SUCCESS
        except db.Error as e:
            log.error("__run_sql error: %s | %s", type(e).__name__, e.args)
            return r.ERROR

    def __run_sql_batch(self, sql_statements: list[str], BUILD: str = "TEST") -> r:
        self.__ensure_connection()

        try:
            for statement in sql_statements:
                self.cursor.execute(statement)
            self.connection.commit()
            return r.SUCCESS
        except db.Error as e:
            log.error("__run_sql error: %s | %s", type(e).__name__, e.args)
            return r.ERROR

    def __run_sql_read(
        self, sql: str, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        self.__ensure_connection()

        try:
            self.cursor.execute(sql, args or ())
            results = self.cursor.fetchall()
            self.connection.commit()
            return results
        except db.Error as e:
            log.error("__run_sql error: %s | %s", type(e).__name__, e.args)
            return r.ERROR

    def __ensure_connection(self):
        if not self.connection:
            if not getattr(self, "DB", None):
                raise ValueError("No DB path specified. Cannot establish connection.")
            self.connect(self.DB)
