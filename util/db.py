import sqlite3 as db
from typing import Optional, List
from util.logger import CLogger

logger = CLogger().get_logger()


class DBInterface:
    '''
        Class to handle DB interactions.
    '''

    def __init__(self, db_name, log_level):
        self.db_name = db_name
        self.log_level = log_level

    def initialize_db(self) -> None:
        SCHEMA_VERSION = "1.0"

        sql = [
            """
            CREATE TABLE IF NOT EXISTS Employee(
                EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
                EmployeeName TEXT NOT NULL,
                EmployeeGroup TEXT
            )
            """,

            """
            CREATE TABLE IF NOT EXISTS PayPeriod(
                PayPeriodID INTEGER PRIMARY KEY AUTOINCREMENT,
                EmployeeID INTEGER NOT NULL,
                StartDate TEXT NOT NULL,
                EndDate TEXT NOT NULL,
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

        self.__run_sql_batch(sql, self.log_level)

    def save_employee(self, employee_name: str,
                      employee_group: Optional[str] = None):
        """
            Adds a new employee if not already present.
        """

        sql = [
            """
        INSERT OR IGNORE INTO Employee (EmployeeName, EmployeeGroup)
        VALUES (?, ?)
        """
        ]

        self.__run_sql(sql=sql, args=(
            employee_name, employee_group), log_level=self.log_level)

    def __run_sql_batch(self,
                        sql_statements: List[str],
                        log_level: str = "PROD"
                        ) -> None:
        """
            Private method to execute SQL statements without parameters.
        """

        try:

            with db.connect(self.db_name) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                cur = conn.cursor()

                for statement in sql_statements:
                    if log_level == "DEBUG":
                        logger.info("Executing SQL: %s",
                                    statement.strip().splitlines()[0])
                    cur.execute(statement)

            conn.commit()
            if log_level == "DEBUG":
                logger.info(
                    "__run_sql_batch: SQL executed successfully.\n")

        except db.Error as e:
            logger.exception("Failed to initialize database schema: %s", e)
            raise

    def __run_sql(self,
                  sql: str,
                  args: tuple = (),
                  log_level: str = "PROD"
                  ) -> None:
        """
            Private method to execute SQL statements with parameters.
        """

        try:
            with db.connect(self.db_name) as conn:
                conn.execute("PRAGMA foreign_keys = ON;")
                if log_level == "DEBUG":
                    logger.info("Executing SQL: %s | Args: %s",
                                sql.strip().splitlines()[0], args)
                conn.execute(sql, args)
                conn.commit()
                if log_level == "DEBUG":
                    logger.info(
                        "__run_sql: SQL executed successfully.")

        except db.Error as e:
            logger.exception("Failed to initialize database schema: %s", e)
            raise

    def __run_sql_fetch(self):
        pass
