"""Database Verification: connect to DB and verify data after UI tests."""

import json
from utils.logger import log


class DBVerifier:
    """Verifies database state after test execution."""

    SUPPORTED_DRIVERS = {
        "sqlite": "sqlite3",
        "mysql": "pymysql",
        "postgresql": "psycopg2",
        "mssql": "pyodbc",
    }

    def __init__(self):
        self.connection = None
        self.db_type = ""
        self.connection_string = ""

    def connect(self, db_type: str, host: str = "", port: int = 0,
                database: str = "", username: str = "", password: str = "",
                connection_string: str = "") -> bool:
        """Connect to a database.

        Args:
            db_type: sqlite, mysql, postgresql, or mssql
            host, port, database, username, password: Connection params
            connection_string: Full connection string (overrides individual params)
        """
        self.db_type = db_type.lower()

        try:
            if self.db_type == "sqlite":
                import sqlite3
                self.connection = sqlite3.connect(database)
                log.info(f"[DB] Da ket noi SQLite: {database}")

            elif self.db_type == "mysql":
                import pymysql
                self.connection = pymysql.connect(
                    host=host, port=port or 3306,
                    user=username, password=password,
                    database=database, charset="utf8mb4",
                )
                log.info(f"[DB] Da ket noi MySQL: {host}:{port}/{database}")

            elif self.db_type == "postgresql":
                import psycopg2
                self.connection = psycopg2.connect(
                    host=host, port=port or 5432,
                    user=username, password=password,
                    dbname=database,
                )
                log.info(f"[DB] Da ket noi PostgreSQL: {host}:{port}/{database}")

            elif self.db_type == "mssql":
                import pyodbc
                if connection_string:
                    self.connection = pyodbc.connect(connection_string)
                else:
                    conn_str = (
                        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                        f"SERVER={host},{port or 1433};"
                        f"DATABASE={database};"
                        f"UID={username};PWD={password}"
                    )
                    self.connection = pyodbc.connect(conn_str)
                log.info(f"[DB] Da ket noi MSSQL: {host}/{database}")

            else:
                log.error(f"[DB] Loai DB khong duoc ho tro: {db_type}")
                return False

            return True

        except Exception as e:
            log.error(f"[DB] Loi ket noi: {e}")
            return False

    def disconnect(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            log.info("[DB] Da dong ket noi.")

    def execute_query(self, query: str, params: tuple = None) -> list:
        """Execute a SELECT query and return results as list of dicts."""
        if not self.connection:
            log.error("[DB] Chua ket noi database.")
            return []

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            log.info(f"[DB] Query tra ve {len(result)} dong.")
            return result

        except Exception as e:
            log.error(f"[DB] Loi query: {e}")
            return []

    def verify_record_exists(self, table: str, conditions: dict) -> bool:
        """Check if a record exists matching the given conditions."""
        where_parts = [f"{k} = ?" for k in conditions.keys()]
        where_clause = " AND ".join(where_parts)
        query = f"SELECT COUNT(*) as cnt FROM {table} WHERE {where_clause}"

        # Adjust placeholder syntax per DB
        if self.db_type in ("mysql", "postgresql"):
            query = query.replace("?", "%s")

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(conditions.values()))
            row = cursor.fetchone()
            count = row[0] if row else 0
            exists = count > 0
            log.info(f"[DB] Verify record in {table}: {'TON TAI' if exists else 'KHONG TIM THAY'}")
            return exists
        except Exception as e:
            log.error(f"[DB] Loi verify: {e}")
            return False

    def verify_field_value(self, table: str, conditions: dict,
                           field: str, expected_value) -> bool:
        """Verify a specific field value for a matching record."""
        where_parts = [f"{k} = ?" for k in conditions.keys()]
        where_clause = " AND ".join(where_parts)
        query = f"SELECT {field} FROM {table} WHERE {where_clause} LIMIT 1"

        if self.db_type in ("mysql", "postgresql"):
            query = query.replace("?", "%s")

        try:
            cursor = self.connection.cursor()
            cursor.execute(query, tuple(conditions.values()))
            row = cursor.fetchone()
            if row is None:
                log.warning(f"[DB] Khong tim thay record trong {table}")
                return False
            actual = row[0]
            match = str(actual) == str(expected_value)
            log.info(
                f"[DB] Verify {table}.{field}: "
                f"ky vong='{expected_value}', thuc te='{actual}' -> "
                f"{'KHOP' if match else 'KHONG KHOP'}"
            )
            return match
        except Exception as e:
            log.error(f"[DB] Loi verify field: {e}")
            return False

    def verify_row_count(self, table: str, conditions: dict = None,
                         expected_count: int = 0) -> bool:
        """Verify the number of rows matching conditions."""
        if conditions:
            where_parts = [f"{k} = ?" for k in conditions.keys()]
            where_clause = " AND ".join(where_parts)
            query = f"SELECT COUNT(*) FROM {table} WHERE {where_clause}"
            if self.db_type in ("mysql", "postgresql"):
                query = query.replace("?", "%s")
            params = tuple(conditions.values())
        else:
            query = f"SELECT COUNT(*) FROM {table}"
            params = None

        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            row = cursor.fetchone()
            actual = row[0] if row else 0
            match = actual == expected_count
            log.info(
                f"[DB] Row count {table}: "
                f"ky vong={expected_count}, thuc te={actual} -> "
                f"{'KHOP' if match else 'KHONG KHOP'}"
            )
            return match
        except Exception as e:
            log.error(f"[DB] Loi row count: {e}")
            return False

    def run_verification_script(self, script: list) -> list:
        """Run a list of verification steps.

        Each step is a dict:
        {
            "type": "record_exists" | "field_value" | "row_count" | "custom_query",
            "table": "table_name",
            "conditions": {"col": "val"},
            "field": "field_name",  # for field_value
            "expected": value,
            "query": "SELECT ..."  # for custom_query
        }
        """
        results = []
        for step in script:
            step_type = step.get("type", "")
            passed = False

            if step_type == "record_exists":
                passed = self.verify_record_exists(
                    step.get("table", ""), step.get("conditions", {})
                )
            elif step_type == "field_value":
                passed = self.verify_field_value(
                    step.get("table", ""), step.get("conditions", {}),
                    step.get("field", ""), step.get("expected")
                )
            elif step_type == "row_count":
                passed = self.verify_row_count(
                    step.get("table", ""), step.get("conditions"),
                    step.get("expected", 0)
                )
            elif step_type == "custom_query":
                rows = self.execute_query(step.get("query", ""))
                expected = step.get("expected")
                if isinstance(expected, int):
                    passed = len(rows) == expected
                elif isinstance(expected, str):
                    passed = expected in json.dumps(rows)
                else:
                    passed = len(rows) > 0

            results.append({
                "step": step,
                "passed": passed,
            })

        return results
