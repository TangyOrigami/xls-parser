import sqlite3 as db
from typing import Optional, List
from util.logger import CLogger

logger = CLogger().get_logger()


class DBInterface:
    '''
        Class to handle DB interactions.
    '''

    def __init__(self, DB):
        self.DB = DB

    def initialize_db(self, BUILD) -> None:
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
                TimeType TEXT NOT NULL CHECK(TimeType IN
                ('RT', 'OT', 'SICK', 'VAC')),
                FOREIGN KEY (PayPeriodID) REFERENCES PayPeriod(PayPeriodID)
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS PayPeriodComment(
                CommentID INTEGER PRIMARY KEY AUTOINCREMENT,
                PayPeriodID INTEGER NOT NULL,
                WorkDate TEXT NOT NULL,
                PunchInComment TEXT,
                PunchOutComment TEXT,
                SpecialPayComment TEXT,
                FOREIGN KEY (PayPeriodID) REFERENCES PayPeriod(PayPeriodID)
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS Meta(
                Key TEXT PRIMARY KEY,
                Value TEXT
            )
            """,

            f'''
            INSERT OR REPLACE INTO Meta (Key, Value)
            VALUES ("SchemaVersion", "{SCHEMA_VERSION}")
            '''
        ]

        self.__run_sql_batch(sql, BUILD)

    def save_employee(self, BUILD, args: tuple = ()):
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

    def _read_user_id(self, BUILD, args: tuple = ()) -> [tuple, ...]:
        sql = """
        SELECT EmployeeID FROM Employee
        WHERE
        FirstName=? AND
        MiddleName=? AND
        LastName=? AND
        EmployeeGroup=?;
        """

        result = self.__run_sql_read(sql=sql, args=args, BUILD=BUILD)

        return result

    def save_pay_period(self, BUILD, args: tuple = ()):
        sql = """
        INSERT OR IGNORE INTO PayPeriod
        (EmployeeID, StartDate, EndDate)
        VALUES (?, ?, ?);
        """

        self.__run_sql(sql=sql,
                       args=args,
                       BUILD=BUILD)

    def save_work_entry(self, BUILD, args: tuple = ()):
        sql = """
        INSERT OR IGNORE INTO PayPeriod
        (EmployeeID, StartDate, EndDate)
        VALUES (?, ?, ?);
        """

        self.__run_sql(sql=sql,
                       args=args,
                       BUILD=BUILD)

    def __run_sql_batch(self,
                        sql_statements: List[str],
                        BUILD
                        ) -> None:
        """
            Private method to execute SQL statements without parameters.
        """

        try:

            with db.connect(self.DB) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                cur = conn.cursor()

                for statement in sql_statements:
                    if BUILD == "DEBUG":
                        logger.warn("IN %s MODE", BUILD)
                        logger.info("Executing SQL: %s",
                                    statement.strip().splitlines()[0])
                    cur.execute(statement)

            conn.commit()
            if BUILD == "DEBUG":
                logger.warn("IN %s MODE", BUILD)
                logger.info(
                    "__run_sql_batch: SQL executed successfully.\n")

        except db.Error as e:
            logger.exception("Failed to initialize database schema: %s", e)
            raise

    def __run_sql(self,
                  BUILD,
                  sql: str,
                  args: tuple = (),
                  ) -> None:
        """
            Private method to execute SQL statements with parameters.
        """

        try:
            with db.connect(self.DB) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                if BUILD == "DEBUG":
                    logger.info("Executing SQL: %s | Args: %s",
                                sql.strip().splitlines()[0], args)

                conn.execute(sql, args)
                conn.commit()

                if BUILD == "DEBUG":
                    logger.info(
                        "__run_sql: SQL executed successfully.")

        except db.Error as e:
            logger.exception("Failed to initialize database schema: %s", e)
            raise

    def __run_sql_read(self,
                       BUILD,
                       sql: str,
                       args: tuple = ()
                       ) -> []:
        """
            Private method to execute SQL reads on DB.
        """

        with db.connect(self.DB) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")

            if BUILD == "DEBUG":
                logger.warn("IN %s MODE", BUILD)
                logger.info("Executing SQL: %s", sql)

            cursor = conn.cursor()

            if args != ():
                cursor.execute(sql, args)
            else:
                cursor.execute(sql)

            employee_ids = cursor.fetchall()

            conn.commit()

            if BUILD == "DEBUG":
                logger.info(
                    "__run_sql: SQL executed successfully.")

            return employee_ids

    def __run_sql_fetch(self):
        pass
