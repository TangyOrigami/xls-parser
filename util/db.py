import sqlite3 as db
from typing import Optional
from util.logger import CLogger


logger = CLogger().get_logger()


class DBInterface:
    def __init__(self, db_name):
        self.db_name = db_name

    def initialize_db(self, verbose: Optional[bool] = False) -> None:
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

            """
            INSERT OR REPLACE INTO Meta (Key, Value)
            VALUES ("SchemaVersion", "1.0")
            """
        ]

        self.__sql_runner(sql, verbose)

    def save_employee(self, employee_name, employee_group):
        sql = [
            f"""
            INSERT INTO Employee (
                EmployeeName,
                EmployeeGroup
            )
            VALUES({employee_name}, {employee_group})
            """
        ]

        print(sql[0])

    def __sql_runner(self, sql: [], verbose: Optional[bool] = False) -> None:
        """
            Private method to execute SQL statements.
        """
        try:
            with db.connect(self.db_name) as conn:

                conn.execute("PRAGMA foreign_keys = ON;")

                cur = conn.cursor()

                for statement in sql:
                    if verbose:
                        logger.info("Executing SQL: %s",
                                    statement.strip().splitlines()[0])
                    cur.execute(statement)

                conn.commit()
                if verbose:
                    logger.info("Database schema initialized successfully.")

        except db.Error as e:
            logger.exception("Failed to initialize database schema: %s", e)
            raise
