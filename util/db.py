import sqlite3
import sqlite3 as db
import threading
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
        return cls._instance

    @classmethod
    def reset_instance(cls):
        if cls._instance and cls._instance.connection:
            cls._instance.connection.close()
        cls._instance = None

    def connect(self, db_name: str):
        if not self.connection:
            self.connection = sqlite3.connect(db_name)
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

    def __init__(self, DB: str = "app.db"):
        if not hasattr(self, "DB"):
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
        return self.__run_sql_batch(sql, BUILD)

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
        WHERE FirstName=? AND MiddleName=? AND LastName=? AND EmployeeGroup=?;
        """
        return self.__run_sql(sql=sql, args=args, BUILD=BUILD)

    # READ METHODS

    def _read_employee_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT EmployeeID FROM Employee WHERE FirstName=? AND MiddleName=? AND LastName=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_employee_name(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT FirstName, MiddleName, LastName FROM Employee WHERE EmployeeID=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT PayPeriodID FROM PayPeriod WHERE EmployeeID=? AND StartDate=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_id_by_date(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT PayPeriodID FROM PayPeriod WHERE StartDate=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_work_entry_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT WorkEntryID FROM WorkEntry WHERE PayPeriodID=? AND WorkDate=? AND Hours=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_comment_id(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT CommentID FROM PayPeriodComment WHERE PayPeriodID=? AND EmployeeID=? AND WorkDate=?"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_ids(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT PayPeriodID FROM PayPeriod WHERE StartDate=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_employee_ids(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT EmployeeID FROM PayPeriod WHERE PayPeriodID=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_work_entries(
        self, args: tuple, BUILD: str = "TEST"
    ) -> Union[list[tuple], r]:
        sql = "SELECT WorkDate, Hours FROM WorkEntry WHERE PayPeriodID=?;"
        return self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

    def _read_pay_period_dates(self, BUILD: str = "TEST") -> Union[list[tuple], r]:
        sql = "SELECT DISTINCT StartDate FROM PayPeriod WHERE EXISTS (SELECT DISTINCT StartDate FROM PayPeriod);"

        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def _default_employee(self, BUILD: str = "TEST") -> Union[list[tuple], r]:
        sql = "SELECT FirstName, MiddleName, LastName FROM Employee ORDER BY ROWID ASC LIMIT 1;"
        return self.__run_sql_read(sql=sql, args=(), BUILD=BUILD)

    def _default_date(self, BUILD: str = "TEST") -> Union[list[tuple], r]:
        sql = "SELECT DISTINCT StartDate FROM PayPeriod ORDER BY StartDate LIMIT 1;"
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

        log.info("SQL: %s | ARGS: %s", sql, args)

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
            self.connect(self.DB)
