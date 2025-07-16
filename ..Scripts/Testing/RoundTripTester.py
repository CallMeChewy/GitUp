# File: RoundTripTester.py
# Path: Scripts/Testing/RoundTripTester.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  06:35PM
"""
Description: SQLite ↔ MySQL round-trip testing utility for Project Himalaya
Validates data integrity during SQLite → MySQL → SQLite conversion cycles
"""

import sqlite3
import mysql.connector
import argparse
import json
import os
import sys
import hashlib
import time
from datetime import datetime
from typing import Dict, List, Tuple, Any

class RoundTripTester:
    def __init__(self, mysql_config: Dict[str, Any], use_sudo: bool = False, sudo_password: str = None):
        self.mysql_config = mysql_config
        self.use_sudo = use_sudo
        self.sudo_password = sudo_password
        self.test_results = {
            'test_id': int(time.time()),
            'timestamp': datetime.now().isoformat(),
            'tables_tested': [],
            'data_integrity': {},
            'performance_metrics': {},
            'errors': []
        }

    def GetMySQLConnection(self):
        """Get MySQL connection, using auth_socket for root user"""
        # For root user, always try auth_socket first since it uses auth_socket plugin
        if self.mysql_config.get('user') == 'root':
            try:
                # auth_socket plugin requires no password, just Unix socket
                return mysql.connector.connect(
                    unix_socket='/var/run/mysqld/mysqld.sock',
                    user='root'
                )
            except Exception as e:
                self.test_results['errors'].append(f"Socket authentication failed: {str(e)}")
        
        # Fall back to regular connection for other users
        return mysql.connector.connect(**self.mysql_config)

    def CalculateTableHash(self, db_path: str, table_name: str) -> str:
        """Calculate MD5 hash of table contents for integrity checking"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name} ORDER BY ROWID")
        rows = cursor.fetchall()
        
        # Convert to string and hash
        data_string = str(rows)
        hash_value = hashlib.md5(data_string.encode()).hexdigest()
        
        conn.close()
        return hash_value

    def GetTableRowCounts(self, db_path: str) -> Dict[str, int]:
        """Get row counts for all tables"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        row_counts = {}
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            row_counts[table] = cursor.fetchone()[0]
        
        conn.close()
        return row_counts

    def ConvertSQLiteToMySQL(self, sqlite_path: str, mysql_db_name: str) -> bool:
        """Convert SQLite database to MySQL"""
        try:
            start_time = time.time()
            
            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cur = sqlite_conn.cursor()

            # Connect to MySQL
            mysql_conn = self.GetMySQLConnection()
            mysql_cur = mysql_conn.cursor()

            # Create test database
            mysql_cur.execute(f"DROP DATABASE IF EXISTS {mysql_db_name}")
            mysql_cur.execute(f"CREATE DATABASE {mysql_db_name}")
            mysql_cur.execute(f"USE {mysql_db_name}")

            # Import comprehensive type mapping
            try:
                from TypeMappingValidator import GetSQLiteToMySQLType
                type_mapper = GetSQLiteToMySQLType
            except ImportError:
                # Fallback to basic mapping
                type_map = {
                    "INTEGER": "INT",
                    "TEXT": "LONGTEXT",
                    "REAL": "FLOAT",
                    "BLOB": "LONGBLOB",
                    "NUMERIC": "FLOAT"
                }
                type_mapper = lambda t: type_map.get(t.upper(), "LONGTEXT")

            # Get all tables
            sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [row[0] for row in sqlite_cur.fetchall()]

            for table in tables:
                print(f"Converting table: {table}")
                
                # Get table structure
                sqlite_cur.execute(f"PRAGMA table_info({table})")
                columns_info = sqlite_cur.fetchall()

                # Create table in MySQL
                column_defs = []
                primary_keys = []
                for col in columns_info:
                    col_name = col[1]
                    col_type = col[2]
                    col_type_mysql = type_mapper(col_type)
                    
                    # Handle special cases
                    if "INT" in col_type_mysql.upper() and col[5]:  # Primary key
                        col_type_mysql = col_type_mysql + " AUTO_INCREMENT"
                    
                    column_defs.append(f"`{col_name}` {col_type_mysql}")
                    if col[5]:  # Primary key flag
                        primary_keys.append(f"`{col_name}`")

                create_stmt = f"CREATE TABLE `{table}` ({', '.join(column_defs)}"
                if primary_keys:
                    create_stmt += f", PRIMARY KEY ({', '.join(primary_keys)})"
                create_stmt += ")"
                
                mysql_cur.execute(create_stmt)

                # Copy data
                columns = [col[1] for col in columns_info]
                col_list = ", ".join(f"`{c}`" for c in columns)
                placeholders = ", ".join(["%s"] * len(columns))

                sqlite_cur.execute(f"SELECT {col_list} FROM `{table}`")
                rows = sqlite_cur.fetchall()

                if rows:
                    insert_stmt = f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})"
                    mysql_cur.executemany(insert_stmt, rows)

                mysql_conn.commit()

            sqlite_conn.close()
            mysql_conn.close()
            
            conversion_time = time.time() - start_time
            self.test_results['performance_metrics']['sqlite_to_mysql_seconds'] = conversion_time
            return True
            
        except Exception as e:
            self.test_results['errors'].append(f"SQLite to MySQL conversion failed: {str(e)}")
            return False

    def ConvertMySQLToSQLite(self, mysql_db_name: str, sqlite_path: str) -> bool:
        """Convert MySQL database back to SQLite"""
        try:
            start_time = time.time()
            
            # Remove existing SQLite file
            if os.path.exists(sqlite_path):
                os.remove(sqlite_path)

            # Connect to MySQL
            mysql_conn = self.GetMySQLConnection()
            mysql_cur = mysql_conn.cursor()
            mysql_cur.execute(f"USE {mysql_db_name}")

            # Connect to SQLite
            sqlite_conn = sqlite3.connect(sqlite_path)
            sqlite_cur = sqlite_conn.cursor()

            # Get all tables from MySQL
            mysql_cur.execute("SHOW TABLES")
            tables = [row[0] for row in mysql_cur.fetchall()]

            for table in tables:
                print(f"Converting back table: {table}")
                
                # Get table structure from MySQL
                mysql_cur.execute(f"DESCRIBE {table}")
                columns_info = mysql_cur.fetchall()

                # Import comprehensive type mapping for return conversion
                try:
                    from TypeMappingValidator import GetMySQLToSQLiteType
                    mysql_to_sqlite_mapper = GetMySQLToSQLiteType
                except ImportError:
                    # Fallback mapping
                    def mysql_to_sqlite_mapper(mysql_type):
                        if "INT" in mysql_type.upper():
                            return "INTEGER"
                        elif "FLOAT" in mysql_type.upper() or "DOUBLE" in mysql_type.upper():
                            return "REAL"
                        elif "BLOB" in mysql_type.upper():
                            return "BLOB"
                        else:
                            return "TEXT"

                # Create table in SQLite
                column_defs = []
                for col in columns_info:
                    col_name = col[0]
                    col_type = col[1]
                    sqlite_type = mysql_to_sqlite_mapper(col_type)
                    column_defs.append(f"{col_name} {sqlite_type}")

                create_stmt = f"CREATE TABLE {table} ({', '.join(column_defs)})"
                sqlite_cur.execute(create_stmt)

                # Copy data back
                mysql_cur.execute(f"SELECT * FROM {table}")
                rows = mysql_cur.fetchall()

                if rows:
                    placeholders = ", ".join(["?"] * len(rows[0]))
                    insert_stmt = f"INSERT INTO {table} VALUES ({placeholders})"
                    sqlite_cur.executemany(insert_stmt, rows)

                sqlite_conn.commit()

            mysql_conn.close()
            sqlite_conn.close()
            
            conversion_time = time.time() - start_time
            self.test_results['performance_metrics']['mysql_to_sqlite_seconds'] = conversion_time
            return True
            
        except Exception as e:
            self.test_results['errors'].append(f"MySQL to SQLite conversion failed: {str(e)}")
            return False

    def RunRoundTripTest(self, original_sqlite: str, test_name: str) -> Dict[str, Any]:
        """Run complete round-trip test"""
        print(f"Starting round-trip test: {test_name}")
        print(f"Original database: {original_sqlite}")
        
        test_start = time.time()
        mysql_db_name = f"roundtrip_test_{self.test_results['test_id']}"
        converted_sqlite = f"/tmp/roundtrip_test_{self.test_results['test_id']}.db"
        
        # Step 1: Analyze original database
        print("Step 1: Analyzing original database...")
        original_counts = self.GetTableRowCounts(original_sqlite)
        original_hashes = {}
        for table in original_counts.keys():
            original_hashes[table] = self.CalculateTableHash(original_sqlite, table)
        
        self.test_results['data_integrity']['original_row_counts'] = original_counts
        self.test_results['data_integrity']['original_hashes'] = original_hashes
        
        # Step 2: Convert SQLite → MySQL
        print("Step 2: Converting SQLite → MySQL...")
        if not self.ConvertSQLiteToMySQL(original_sqlite, mysql_db_name):
            return self.test_results
        
        # Step 3: Convert MySQL → SQLite
        print("Step 3: Converting MySQL → SQLite...")
        if not self.ConvertMySQLToSQLite(mysql_db_name, converted_sqlite):
            return self.test_results
        
        # Step 4: Analyze converted database
        print("Step 4: Analyzing converted database...")
        converted_counts = self.GetTableRowCounts(converted_sqlite)
        converted_hashes = {}
        for table in converted_counts.keys():
            converted_hashes[table] = self.CalculateTableHash(converted_sqlite, table)
        
        self.test_results['data_integrity']['converted_row_counts'] = converted_counts
        self.test_results['data_integrity']['converted_hashes'] = converted_hashes
        
        # Step 5: Calculate integrity metrics
        print("Step 5: Calculating integrity metrics...")
        total_original_rows = sum(original_counts.values())
        total_converted_rows = sum(converted_counts.values())
        
        integrity_percentage = (total_converted_rows / total_original_rows * 100) if total_original_rows > 0 else 0
        
        # Check hash matches
        hash_matches = 0
        for table in original_hashes:
            if table in converted_hashes and original_hashes[table] == converted_hashes[table]:
                hash_matches += 1
        
        hash_integrity_percentage = (hash_matches / len(original_hashes) * 100) if original_hashes else 0
        
        self.test_results['data_integrity']['row_count_integrity_percent'] = integrity_percentage
        self.test_results['data_integrity']['hash_integrity_percent'] = hash_integrity_percentage
        self.test_results['performance_metrics']['total_test_seconds'] = time.time() - test_start
        self.test_results['test_name'] = test_name
        
        # Cleanup
        try:
            mysql_conn = self.GetMySQLConnection()
            mysql_cur = mysql_conn.cursor()
            mysql_cur.execute(f"DROP DATABASE IF EXISTS {mysql_db_name}")
            mysql_conn.close()
            
            if os.path.exists(converted_sqlite):
                os.remove(converted_sqlite)
        except:
            pass
        
        print(f"Test completed! Row integrity: {integrity_percentage:.1f}%, Hash integrity: {hash_integrity_percentage:.1f}%")
        return self.test_results

def main():
    parser = argparse.ArgumentParser(description="SQLite ↔ MySQL Round-Trip Tester")
    parser.add_argument("sqlite_db", help="Path to SQLite database to test")
    parser.add_argument("--mysql-user", required=True, help="MySQL username")
    parser.add_argument("--mysql-password", required=True, help="MySQL password")
    parser.add_argument("--mysql-host", default="localhost", help="MySQL host")
    parser.add_argument("--mysql-port", default=3306, type=int, help="MySQL port")
    parser.add_argument("--test-name", default="Round Trip Test", help="Test name")
    parser.add_argument("--output", help="JSON output file for results")
    parser.add_argument("--use-sudo", action="store_true", help="Use sudo for MySQL root connections")
    parser.add_argument("--sudo-password", help="Sudo password for system access")
    
    args = parser.parse_args()
    
    mysql_config = {
        'host': args.mysql_host,
        'port': args.mysql_port,
        'user': args.mysql_user,
        'password': args.mysql_password
    }
    
    tester = RoundTripTester(mysql_config, args.use_sudo, args.sudo_password)
    results = tester.RunRoundTripTest(args.sqlite_db, args.test_name)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"Results saved to: {args.output}")
    else:
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()