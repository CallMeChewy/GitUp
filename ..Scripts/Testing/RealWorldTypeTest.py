# File: RealWorldTypeTest.py
# Path: Scripts/Testing/RealWorldTypeTest.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  07:05PM
"""
Description: Real-world database type testing with edge cases and complex scenarios
Creates test databases with challenging data types and validates round-trip conversion
"""

import sqlite3
import mysql.connector
import os
import tempfile
import json
import hashlib
from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Tuple

class RealWorldTypeTest:
    def __init__(self, mysql_config: Dict[str, Any]):
        self.mysql_config = mysql_config
        self.test_results = []
        
    def CreateTestDatabase(self) -> str:
        """Create SQLite database with challenging real-world data types"""
        test_db = tempfile.mktemp(suffix='.db')
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # Table 1: Complex numeric types
        cursor.execute('''
        CREATE TABLE NumericTests (
            id INTEGER PRIMARY KEY,
            tiny_int TINYINT,
            small_int SMALLINT,
            big_int BIGINT,
            decimal_precise DECIMAL(15,4),
            numeric_val NUMERIC(10,2),
            real_val REAL,
            double_val DOUBLE PRECISION,
            float_val FLOAT,
            boolean_val BOOLEAN,
            negative_int INTEGER,
            zero_val INTEGER,
            max_int INTEGER
        )
        ''')
        
        # Table 2: Text and character types
        cursor.execute('''
        CREATE TABLE TextTests (
            id INTEGER PRIMARY KEY,
            char_fixed CHAR(10),
            varchar_var VARCHAR(255),
            text_small TEXT,
            text_large TEXT,
            clob_data CLOB,
            unicode_text NVARCHAR(100),
            empty_text TEXT,
            null_text TEXT,
            special_chars TEXT,
            json_like TEXT
        )
        ''')
        
        # Table 3: Binary and BLOB types
        cursor.execute('''
        CREATE TABLE BlobTests (
            id INTEGER PRIMARY KEY,
            small_blob BLOB,
            large_blob BLOB,
            binary_data BINARY(16),
            empty_blob BLOB,
            null_blob BLOB,
            image_like BLOB,
            pdf_like BLOB
        )
        ''')
        
        # Table 4: Date/Time types (stored as TEXT in SQLite)
        cursor.execute('''
        CREATE TABLE DateTimeTests (
            id INTEGER PRIMARY KEY,
            date_val DATE,
            datetime_val DATETIME,
            timestamp_val TIMESTAMP,
            time_val TIME,
            year_val YEAR,
            iso_datetime TEXT,
            unix_timestamp INTEGER,
            null_date DATE
        )
        ''')
        
        # Table 5: Edge cases and problematic data
        cursor.execute('''
        CREATE TABLE EdgeCaseTests (
            id INTEGER PRIMARY KEY,
            sql_injection TEXT,
            quote_heavy TEXT,
            newline_text TEXT,
            binary_string TEXT,
            very_long_text TEXT,
            emoji_unicode TEXT,
            control_chars TEXT,
            mixed_encoding TEXT
        )
        ''')
        
        # Insert test data
        self.InsertTestData(cursor)
        
        conn.commit()
        conn.close()
        return test_db
    
    def InsertTestData(self, cursor):
        """Insert challenging test data"""
        
        # Numeric test data (using strings for decimal precision)
        cursor.executemany('''
        INSERT INTO NumericTests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, 127, 32767, 9223372036854775807, '12345.6789', '999.99', 3.14159, 2.718281828, 1.23e-4, 1, -42, 0, 2147483647),
            (2, -128, -32768, -9223372036854775808, '-9999.9999', '-123.45', -2.5, -1.414, -9.87e5, 0, -2147483648, 0, 0),
            (3, 0, 0, 0, '0.0001', '0.01', 0.0, 0.0, 0.0, None, None, None, None)
        ])
        
        # Text test data
        cursor.executemany('''
        INSERT INTO TextTests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, 'FIXED_CHAR', 'Variable length string', 'Short text', 'A' * 10000, 'CLOB data here', 'Unicode: café', '', None, "Special: !@#$%^&*()_+-=[]{}|;':\",./<>?", '{"key": "value", "number": 42}'),
            (2, 'SHORT', 'Another string with "quotes" and \'apostrophes\'', 'More text', 'B' * 50000, 'Large CLOB ' * 1000, 'Español: niño', '', None, 'Newline\nTab\tReturn\r', '[1,2,3,"text",null,true]'),
            (3, '', '', '', '', '', '', '', None, '\\x00\\x01\\x02\\xFF', '{"nested": {"deep": {"value": true}}}')
        ])
        
        # BLOB test data
        import os
        small_blob = os.urandom(1024)  # 1KB
        large_blob = os.urandom(1024 * 1024)  # 1MB
        binary_data = b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0A\x0B\x0C\x0D\x0E\x0F'
        
        cursor.executemany('''
        INSERT INTO BlobTests VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, small_blob, large_blob, binary_data, b'', None, b'\x89PNG\r\n\x1a\n' + os.urandom(100), b'%PDF-1.4' + os.urandom(200)),
            (2, os.urandom(512), os.urandom(2048), binary_data * 2, b'', None, os.urandom(50), os.urandom(300)),
            (3, None, None, None, None, None, None, None)
        ])
        
        # DateTime test data (MySQL timestamp range: 1970-01-01 00:00:01 to 2038-01-19 03:14:07 UTC)
        cursor.executemany('''
        INSERT INTO DateTimeTests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, '2025-07-12', '2025-07-12 19:05:30', '2025-07-12 19:05:30', '19:05:30', 2025, '2025-07-12T19:05:30.123Z', 1752360330, None),
            (2, '1970-01-01', '1970-01-01 00:00:01', '1970-01-01 00:00:01', '00:00:01', 1970, '1970-01-01T00:00:01.000Z', 1, None),
            (3, '2037-12-31', '2037-12-31 23:59:59', '2037-12-31 23:59:59', '23:59:59', 2037, '2037-12-31T23:59:59.999Z', 2145916799, None)
        ])
        
        # Edge case test data
        cursor.executemany('''
        INSERT INTO EdgeCaseTests VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            (1, "'; DROP TABLE users; --", 'Text with "many" \'different\' `quote` types', 'Line 1\nLine 2\nLine 3\r\nWindows line', '0101001001000101', 'X' * 100000, '🌟 Unicode emoji test 🎉 with symbols ⚡', '\x00\x01\x02\x03\x1B[31mRed text\x1B[0m', 'Mixed: ASCII + UTF-8: café'),
            (2, "1' OR '1'='1", 'Text with backslashes: C:\\\\Windows\\\\System32\\\\', 'Tab\tseparated\tvalues\there', '\xFF\xFE\x00\x01Binary in text', 'Y' * 200000, '测试中文字符 🇨🇳', '\x07\x08\x0C\x0E\x15\x16\x17', 'ISO-8859-1: café'),
            (3, None, None, None, None, None, None, None, None)
        ])
    
    def GetMySQLConnection(self):
        """Get MySQL connection with auth_socket for root"""
        if self.mysql_config.get('user') == 'root':
            return mysql.connector.connect(
                unix_socket='/var/run/mysqld/mysqld.sock',
                user='root'
            )
        return mysql.connector.connect(**self.mysql_config)
    
    def RunComprehensiveTest(self) -> Dict[str, Any]:
        """Run comprehensive real-world type testing"""
        print("Creating real-world test database...")
        test_db = self.CreateTestDatabase()
        
        try:
            # Import updated type mapping
            from TypeMappingValidator import GetSQLiteToMySQLType, GetMySQLToSQLiteType
            
            print("Running comprehensive type conversion test...")
            
            # Step 1: Convert to MySQL
            mysql_db = f"realworld_test_{int(datetime.now().timestamp())}"
            self.ConvertToMySQL(test_db, mysql_db, GetSQLiteToMySQLType)
            
            # Step 2: Validate MySQL data
            mysql_validation = self.ValidateMySQLData(mysql_db)
            
            # Step 3: Convert back to SQLite
            converted_db = tempfile.mktemp(suffix='_converted.db')
            self.ConvertToSQLite(mysql_db, converted_db, GetMySQLToSQLiteType)
            
            # Step 4: Compare original vs converted
            comparison = self.CompareDataBases(test_db, converted_db)
            
            # Step 5: Cleanup
            self.CleanupMySQL(mysql_db)
            
            results = {
                'timestamp': datetime.now().isoformat(),
                'mysql_validation': mysql_validation,
                'data_comparison': comparison,
                'test_database': test_db,
                'converted_database': converted_db
            }
            
            return results
            
        except Exception as e:
            return {'error': str(e), 'test_database': test_db}
    
    def ConvertToMySQL(self, sqlite_db: str, mysql_db: str, type_mapper):
        """Convert SQLite to MySQL using comprehensive type mapping"""
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cur = sqlite_conn.cursor()
        
        mysql_conn = self.GetMySQLConnection()
        mysql_cur = mysql_conn.cursor()
        
        # Create MySQL database
        mysql_cur.execute(f"DROP DATABASE IF EXISTS {mysql_db}")
        mysql_cur.execute(f"CREATE DATABASE {mysql_db}")
        mysql_cur.execute(f"USE {mysql_db}")
        
        # Get all tables
        sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in sqlite_cur.fetchall()]
        
        for table in tables:
            print(f"Converting table: {table}")
            
            # Get table structure
            sqlite_cur.execute(f"PRAGMA table_info({table})")
            columns = sqlite_cur.fetchall()
            
            # Create MySQL table with proper type mapping
            column_defs = []
            primary_keys = []
            
            for col in columns:
                col_name = col[1]
                sqlite_type = col[2]
                mysql_type = type_mapper(sqlite_type)
                
                column_defs.append(f"`{col_name}` {mysql_type}")
                if col[5]:  # Primary key
                    primary_keys.append(f"`{col_name}`")
            
            create_stmt = f"CREATE TABLE `{table}` ({', '.join(column_defs)}"
            if primary_keys:
                create_stmt += f", PRIMARY KEY ({', '.join(primary_keys)})"
            create_stmt += ")"
            
            mysql_cur.execute(create_stmt)
            
            # Copy data
            columns_list = [col[1] for col in columns]
            col_names = ", ".join(f"`{c}`" for c in columns_list)
            placeholders = ", ".join(["%s"] * len(columns_list))
            
            sqlite_cur.execute(f"SELECT {col_names} FROM `{table}`")
            rows = sqlite_cur.fetchall()
            
            if rows:
                insert_stmt = f"INSERT INTO `{table}` ({col_names}) VALUES ({placeholders})"
                mysql_cur.executemany(insert_stmt, rows)
                mysql_conn.commit()
        
        sqlite_conn.close()
        mysql_conn.close()
    
    def ValidateMySQLData(self, mysql_db: str) -> Dict[str, Any]:
        """Validate data in MySQL database"""
        mysql_conn = self.GetMySQLConnection()
        mysql_cur = mysql_conn.cursor()
        mysql_cur.execute(f"USE {mysql_db}")
        
        validation = {}
        
        # Check table counts
        mysql_cur.execute("SHOW TABLES")
        tables = [row[0] for row in mysql_cur.fetchall()]
        validation['table_count'] = len(tables)
        validation['tables'] = {}
        
        for table in tables:
            mysql_cur.execute(f"SELECT COUNT(*) FROM `{table}`")
            row_count = mysql_cur.fetchone()[0]
            
            mysql_cur.execute(f"DESCRIBE `{table}`")
            schema = mysql_cur.fetchall()
            
            validation['tables'][table] = {
                'row_count': row_count,
                'columns': len(schema),
                'schema': [{'name': col[0], 'type': col[1]} for col in schema]
            }
        
        mysql_conn.close()
        return validation
    
    def ConvertToSQLite(self, mysql_db: str, sqlite_db: str, type_mapper):
        """Convert MySQL back to SQLite using comprehensive type mapping"""
        mysql_conn = self.GetMySQLConnection()
        mysql_cur = mysql_conn.cursor()
        mysql_cur.execute(f"USE {mysql_db}")
        
        sqlite_conn = sqlite3.connect(sqlite_db)
        sqlite_cur = sqlite_conn.cursor()
        
        # Get tables
        mysql_cur.execute("SHOW TABLES")
        tables = [row[0] for row in mysql_cur.fetchall()]
        
        for table in tables:
            print(f"Converting back table: {table}")
            
            # Get MySQL schema
            mysql_cur.execute(f"DESCRIBE `{table}`")
            columns = mysql_cur.fetchall()
            
            # Create SQLite table
            column_defs = []
            for col in columns:
                col_name = col[0]
                mysql_type = col[1]
                sqlite_type = type_mapper(mysql_type)
                column_defs.append(f"`{col_name}` {sqlite_type}")
            
            create_stmt = f"CREATE TABLE `{table}` ({', '.join(column_defs)})"
            sqlite_cur.execute(create_stmt)
            
            # Copy data with type conversion
            mysql_cur.execute(f"SELECT * FROM `{table}`")
            rows = mysql_cur.fetchall()
            
            if rows:
                # Convert problematic types
                converted_rows = []
                for row in rows:
                    converted_row = []
                    for value in row:
                        # Handle Decimal objects
                        if hasattr(value, '__class__') and 'Decimal' in str(type(value)):
                            converted_row.append(str(value))
                        else:
                            converted_row.append(value)
                    converted_rows.append(tuple(converted_row))
                
                placeholders = ", ".join(["?"] * len(converted_rows[0]))
                insert_stmt = f"INSERT INTO `{table}` VALUES ({placeholders})"
                sqlite_cur.executemany(insert_stmt, converted_rows)
                sqlite_conn.commit()
        
        mysql_conn.close()
        sqlite_conn.close()
    
    def CompareDataBases(self, original_db: str, converted_db: str) -> Dict[str, Any]:
        """Compare original and converted databases"""
        def get_db_hash(db_path: str) -> Dict[str, str]:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            hashes = {}
            for table in tables:
                cursor.execute(f"SELECT * FROM `{table}` ORDER BY ROWID")
                rows = cursor.fetchall()
                data_str = str(rows)
                hashes[table] = hashlib.md5(data_str.encode()).hexdigest()
            
            conn.close()
            return hashes
        
        original_hashes = get_db_hash(original_db)
        converted_hashes = get_db_hash(converted_db)
        
        comparison = {
            'total_tables': len(original_hashes),
            'matching_tables': 0,
            'table_comparison': {}
        }
        
        for table in original_hashes:
            matches = table in converted_hashes and original_hashes[table] == converted_hashes[table]
            if matches:
                comparison['matching_tables'] += 1
            
            comparison['table_comparison'][table] = {
                'data_match': matches,
                'original_hash': original_hashes[table],
                'converted_hash': converted_hashes.get(table, 'MISSING')
            }
        
        comparison['integrity_percentage'] = (comparison['matching_tables'] / comparison['total_tables']) * 100
        
        return comparison
    
    def CleanupMySQL(self, mysql_db: str):
        """Clean up MySQL test database"""
        try:
            mysql_conn = self.GetMySQLConnection()
            mysql_cur = mysql_conn.cursor()
            mysql_cur.execute(f"DROP DATABASE IF EXISTS {mysql_db}")
            mysql_conn.close()
        except:
            pass

def main():
    mysql_config = {'user': 'root'}
    tester = RealWorldTypeTest(mysql_config)
    
    print("🧪 Running Real-World Type Conversion Test")
    print("=" * 60)
    
    results = tester.RunComprehensiveTest()
    
    if 'error' in results:
        print(f"❌ Test failed: {results['error']}")
        return
    
    print("\n📊 Test Results:")
    print("-" * 40)
    
    mysql_val = results['mysql_validation']
    print(f"MySQL Tables Created: {mysql_val['table_count']}")
    
    for table, info in mysql_val['tables'].items():
        print(f"  {table}: {info['row_count']} rows, {info['columns']} columns")
    
    comparison = results['data_comparison']
    print(f"\nData Integrity: {comparison['integrity_percentage']:.1f}%")
    print(f"Matching Tables: {comparison['matching_tables']}/{comparison['total_tables']}")
    
    for table, comp in comparison['table_comparison'].items():
        status = "✅" if comp['data_match'] else "❌"
        print(f"  {table}: {status}")
    
    # Save detailed results
    output_file = f"Results/Testing/realworld_test_{int(datetime.now().timestamp())}.json"
    os.makedirs("Results/Testing", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()