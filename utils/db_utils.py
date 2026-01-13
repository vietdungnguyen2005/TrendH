"""
Database utilities for Trend Hunter
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
import pandas as pd
from datetime import datetime


class Database:
    """Database connection manager"""
    
    def __init__(self, db_path="data/trendhunter.db"):
        self.db_path = db_path
        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def execute_query(self, query, params=None):
        """Execute a query and return results"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
    
    def execute_many(self, query, params_list):
        """Execute many inserts/updates"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount
    
    def insert(self, table, data):
        """
        Insert a single record
        Args:
            table: Table name
            data: Dictionary of column: value
        Returns:
            Last inserted row ID
        """
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, list(data.values()))
            return cursor.lastrowid
    
    def insert_many(self, table, data_list):
        """
        Insert multiple records
        Args:
            table: Table name
            data_list: List of dictionaries
        Returns:
            Number of rows inserted
        """
        if not data_list:
            return 0
        
        columns = ', '.join(data_list[0].keys())
        placeholders = ', '.join(['?' for _ in data_list[0]])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        
        values_list = [list(data.values()) for data in data_list]
        return self.execute_many(query, values_list)
    
    def query_to_df(self, query, params=None):
        """
        Execute query and return pandas DataFrame
        """
        with self.get_connection() as conn:
            if params:
                df = pd.read_sql_query(query, conn, params=params)
            else:
                df = pd.read_sql_query(query, conn)
            return df
    
    def table_exists(self, table_name):
        """Check if table exists"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = self.execute_query(query, (table_name,))
        return len(result) > 0
    
    def get_table_count(self, table_name):
        """Get row count for a table"""
        query = f"SELECT COUNT(*) as count FROM {table_name}"
        result = self.execute_query(query)
        return result[0]['count'] if result else 0


# Global database instance
_db = None


def get_db(db_path="data/trendhunter.db"):
    """Get global database instance"""
    global _db
    if _db is None:
        _db = Database(db_path)
    return _db
