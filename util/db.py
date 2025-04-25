import sqlite3 as db
from util.logger import CLogger

log = CLogger().get_logger()


class DBInterface:
    '''
        Class to handle DB interactions.
    '''

    def __init__(self, DB: str):
        self.DB = DB

    def initialize_db(self, BUILD: str) -> None:
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
                FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID)
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS WorkEntry(
                WorkEntryID INTEGER PRIMARY KEY AUTOINCREMENT,
                PayPeriodID INTEGER NOT NULL,
                WorkDate TEXT NOT NULL,
                Hours REAL NOT NULL CHECK(Hours >= 0.0),
                UNIQUE(PayPeriodID, WorkDate),
                FOREIGN KEY (PayPeriodID) REFERENCES PayPeriod(PayPeriodID)
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
                FOREIGN KEY (PayPeriodID) REFERENCES PayPeriod(PayPeriodID),
                FOREIGN KEY (EmployeeID) REFERENCES Employee(EmployeeID)
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
            """
        ]

        self.__run_sql_batch(sql, BUILD)

    def save_employee(self, BUILD: str, args: tuple):
        """
            Adds a new employee if not already present.
        """

        sql = """
        INSERT OR IGNORE INTO Employee
        (FirstName, MiddleName, LastName, EmployeeGroup)
        VALUES (?, ?, ?, ?);
        """

        self.__run_sql(sql=sql,
                       args=args,
                       BUILD=BUILD)

    def _read_user_id(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT EmployeeID FROM Employee
        WHERE
        FirstName=? AND
        MiddleName=? AND
        LastName=? AND
        EmployeeGroup=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_pay_period_id(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT PayPeriodID FROM PayPeriod
        WHERE
        EmployeeID=? AND
        StartDate=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_pay_period_id_by_date(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT PayPeriodID FROM PayPeriod
        WHERE
        StartDate=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_work_entry_id(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT WorkEntryID FROM WorkEntry
        WHERE
        PayPeriodID=? AND
        WorkDate=? AND
        Hours=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def save_pay_period(self, BUILD: str, args: tuple):
        sql = """
        INSERT OR IGNORE INTO PayPeriod
        (EmployeeID, StartDate, EndDate)
        VALUES (?, ?, ?);
        """

        self.__run_sql(sql=sql,
                       args=args,
                       BUILD=BUILD)

    def save_work_entry(self, BUILD: str, args: tuple):
        sql = """
        INSERT OR IGNORE INTO WorkEntry
        (PayPeriodID, WorkDate, Hours)
        VALUES (?, ?, ?);
        """

        self.__run_sql(sql=sql,
                       args=args,
                       BUILD=BUILD)

    def save_comment(self, BUILD: str, args: tuple):
        sql = """
        INSERT OR IGNORE INTO PayPeriodComment
        (PayPeriodID, EmployeeID, WorkDate,
        PunchInComment, PunchOutComment, SpecialPayComment)
        VALUES (?, ?, ?, ?, ?, ?);
        """

        self.__run_sql(sql=sql,
                       args=args,
                       BUILD=BUILD)

    def _read_comment_id(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT CommentID FROM PayPeriodComment
        WHERE
        PayPeriodID=? AND
        EmployeeID=? AND
        WorkDate=?
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_pay_period_dates(self, BUILD: str) -> [tuple]:
        sql = """
        SELECT DISTINCT StartDate FROM PayPeriod
        WHERE EXISTS (SELECT DISTINCT StartDate FROM PayPeriod);
        """

        result = self.__run_sql_read(sql=sql,
                                     args=(),
                                     BUILD=BUILD)

        return result

    def _read_pay_period_ids(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT PayPeriodID FROM PayPeriod
        WHERE
        StartDate=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_employee_ids(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT EmployeeID FROM PayPeriod
        WHERE
        PayPeriodID=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_employee_id(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT EmployeeID FROM Employee
        WHERE
        FirstName=? AND
        MiddleName=? AND
        LastName=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_employee_name(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT FirstName, MiddleName, LastName FROM Employee
        WHERE
        EmployeeID=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _read_work_entries(self, BUILD: str, args: tuple) -> [tuple]:
        sql = """
        SELECT WorkDate, Hours FROM WorkEntry
        WHERE
        PayPeriodID=?;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=args,
                                     BUILD=BUILD)

        return result

    def _default_employee(self, BUILD: str) -> [tuple]:
        sql = """
        SELECT FirstName, MiddleName, LastName
        FROM Employee ORDER BY ROWID ASC LIMIT 1;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=(),
                                     BUILD=BUILD)

        return result

    def _default_date(self, BUILD: str) -> [tuple]:
        sql = """
        SELECT DISTINCT StartDate
        FROM PayPeriod
        ORDER BY StartDate
        LIMIT 1;
        """

        result = self.__run_sql_read(sql=sql,
                                     args=(),
                                     BUILD=BUILD)

        return result

    def __run_sql(self,
                  BUILD: str,
                  sql: str,
                  args: tuple
                  ) -> None:
        """
            Private method to execute SQL statements with parameters.
        """

        try:
            with db.connect(self.DB) as conn:
                conn.set_trace_callback(True)
                conn.execute("PRAGMA foreign_keys = ON;")
                if BUILD == "DEBUG":
                    log.info("Executing SQL: %s | Args: %s",
                             sql.strip().splitlines()[0], args)

                if args == ():
                    conn.execute(sql)
                else:
                    conn.execute(sql, args)

                conn.commit()

                if BUILD == "DEBUG":
                    log.info(
                        "__run_sql: SQL executed successfully.")

        except db.Error as e:
            log.exception("Failed to initialize database schema: %s", e)
            assert e.with_traceback

    def __run_sql_batch(self,
                        sql_statements: [str],
                        BUILD: str
                        ) -> None:
        '''
            Private method to execute SQL statements without parameters.
        '''

        try:

            with db.connect(self.DB) as conn:
                conn.set_trace_callback(True)
                conn.execute("PRAGMA foreign_keys = ON;")
                cur = conn.cursor()

                for statement in sql_statements:
                    if BUILD == "DEBUG":
                        log.warn("IN %s MODE", BUILD)
                        log.info("Executing SQL: %s",
                                 statement.strip().splitlines()[0])
                    cur.execute(statement)

            conn.commit()
            if BUILD == "DEBUG":
                log.warn("IN %s MODE", BUILD)
                log.info(
                    "__run_sql_batch: SQL executed successfully.\n")

        except db.Error as e:
            log.exception("Failed to initialize database schema: %s", e)
            assert e.with_traceback

    def __run_sql_read(self,
                       BUILD,
                       sql: str,
                       args: tuple
                       ) -> []:
        """
            Private method to execute SQL reads on DB.
        """

        try:
            with db.connect(self.DB) as conn:
                conn.set_trace_callback(True)
                conn.execute("PRAGMA foreign_keys = ON;")

                if BUILD == "DEBUG":
                    log.info("Executing SQL: %s | %s", sql, args)

                cursor = conn.cursor()

                if args == ():
                    cursor.execute(sql)
                elif not isinstance(args, tuple):
                    args = (args,) if isinstance(args, str) else tuple(args)

                    cursor.execute(sql, args)
                else:
                    cursor.execute(sql, args)

                employee_ids = cursor.fetchall()

                conn.commit()

                if BUILD == "DEBUG":
                    log.info(
                        "__run_sql: SQL executed successfully.")

                return employee_ids
        except db.Error as e:
            log.exception("Failed to read from db: %s | SQL: %s", e, sql)
            assert e.with_traceback
