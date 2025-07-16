# File: TypeMappingValidator.py
# Path: Scripts/Testing/TypeMappingValidator.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  07:02PM
"""
Description: Comprehensive type mapping validator for SQLite ↔ MySQL conversions
Ensures robust handling of all SQLite and MySQL data types
"""

# Complete SQLite → MySQL type mapping
SQLITE_TO_MYSQL_TYPES = {
    # SQLite Core Types
    "INTEGER": "INT",
    "REAL": "DOUBLE",
    "TEXT": "LONGTEXT", 
    "BLOB": "LONGBLOB",
    "NUMERIC": "DECIMAL(65,30)",
    
    # SQLite Affinity Types
    "INT": "INT",
    "TINYINT": "TINYINT",
    "SMALLINT": "SMALLINT", 
    "MEDIUMINT": "MEDIUMINT",
    "BIGINT": "BIGINT",
    "UNSIGNED BIG INT": "BIGINT UNSIGNED",
    "INT2": "SMALLINT",
    "INT8": "BIGINT",
    
    # Character/Text Types
    "CHARACTER(20)": "VARCHAR(20)",
    "VARCHAR(255)": "VARCHAR(255)", 
    "VARYING CHARACTER(255)": "VARCHAR(255)",
    "NCHAR(55)": "CHAR(55)",
    "NATIVE CHARACTER(70)": "CHAR(70)",
    "NVARCHAR(100)": "VARCHAR(100)",
    "CLOB": "LONGTEXT",
    
    # Numeric Types
    "DOUBLE": "DOUBLE",
    "DOUBLE PRECISION": "DOUBLE",
    "FLOAT": "FLOAT",
    "DECIMAL(10,5)": "DECIMAL(10,5)",
    
    # Date/Time (SQLite stores as TEXT/INTEGER)
    "DATE": "DATE",
    "DATETIME": "DATETIME", 
    "TIMESTAMP": "TIMESTAMP",
    
    # Boolean
    "BOOLEAN": "BOOLEAN"
}

# Complete MySQL → SQLite type mapping  
MYSQL_TO_SQLITE_TYPES = {
    # Integer Types
    "TINYINT": "INTEGER",
    "SMALLINT": "INTEGER", 
    "MEDIUMINT": "INTEGER",
    "INT": "INTEGER",
    "INTEGER": "INTEGER",
    "BIGINT": "INTEGER",
    "TINYINT UNSIGNED": "INTEGER",
    "SMALLINT UNSIGNED": "INTEGER",
    "MEDIUMINT UNSIGNED": "INTEGER", 
    "INT UNSIGNED": "INTEGER",
    "BIGINT UNSIGNED": "INTEGER",
    
    # Floating Point
    "FLOAT": "REAL",
    "DOUBLE": "REAL",
    "REAL": "REAL",
    "DECIMAL": "NUMERIC",
    "NUMERIC": "NUMERIC",
    
    # String Types
    "CHAR": "TEXT",
    "VARCHAR": "TEXT",
    "TINYTEXT": "TEXT",
    "TEXT": "TEXT", 
    "MEDIUMTEXT": "TEXT",
    "LONGTEXT": "TEXT",
    "BINARY": "BLOB",
    "VARBINARY": "BLOB",
    
    # BLOB Types
    "TINYBLOB": "BLOB",
    "BLOB": "BLOB",
    "MEDIUMBLOB": "BLOB", 
    "LONGBLOB": "BLOB",
    
    # Date/Time
    "DATE": "TEXT",
    "TIME": "TEXT",
    "DATETIME": "TEXT",
    "TIMESTAMP": "TEXT",
    "YEAR": "INTEGER",
    
    # Other
    "BOOLEAN": "INTEGER",
    "BIT": "INTEGER",
    "JSON": "TEXT",
    "GEOMETRY": "BLOB",
    "POINT": "BLOB",
    "LINESTRING": "BLOB",
    "POLYGON": "BLOB"
}

def GetSQLiteToMySQLType(sqlite_type: str) -> str:
    """Convert SQLite type to appropriate MySQL type"""
    sqlite_type = sqlite_type.upper().strip()
    
    # Handle parameterized types like VARCHAR(255)
    base_type = sqlite_type.split('(')[0].strip()
    
    # Check exact match first
    if sqlite_type in SQLITE_TO_MYSQL_TYPES:
        return SQLITE_TO_MYSQL_TYPES[sqlite_type]
    
    # Check base type
    if base_type in SQLITE_TO_MYSQL_TYPES:
        return SQLITE_TO_MYSQL_TYPES[base_type]
    
    # SQLite affinity rules - check for keywords
    if any(keyword in sqlite_type for keyword in ["INT"]):
        return "INT"
    elif any(keyword in sqlite_type for keyword in ["CHAR", "CLOB", "TEXT"]):
        return "LONGTEXT" 
    elif any(keyword in sqlite_type for keyword in ["BLOB"]):
        return "LONGBLOB"
    elif any(keyword in sqlite_type for keyword in ["REAL", "FLOA", "DOUB"]):
        return "DOUBLE"
    else:
        # Default to TEXT for unknown types
        return "LONGTEXT"

def GetMySQLToSQLiteType(mysql_type: str) -> str:
    """Convert MySQL type to appropriate SQLite type"""
    mysql_type = mysql_type.upper().strip()
    
    # Handle parameterized types
    base_type = mysql_type.split('(')[0].strip()
    
    # Check exact match first
    if mysql_type in MYSQL_TO_SQLITE_TYPES:
        return MYSQL_TO_SQLITE_TYPES[mysql_type]
    
    # Check base type
    if base_type in MYSQL_TO_SQLITE_TYPES:
        return MYSQL_TO_SQLITE_TYPES[base_type]
    
    # Fallback based on common patterns
    if any(keyword in mysql_type for keyword in ["INT", "SERIAL"]):
        return "INTEGER"
    elif any(keyword in mysql_type for keyword in ["FLOAT", "DOUBLE", "REAL"]):
        return "REAL"
    elif any(keyword in mysql_type for keyword in ["CHAR", "TEXT", "JSON"]):
        return "TEXT"
    elif any(keyword in mysql_type for keyword in ["BLOB", "BINARY"]):
        return "BLOB"
    elif any(keyword in mysql_type for keyword in ["DECIMAL", "NUMERIC"]):
        return "NUMERIC"
    else:
        # Default to TEXT for unknown types
        return "TEXT"

def ValidateTypeMapping():
    """Test type mapping with common scenarios"""
    test_cases = [
        # Your actual database types
        ("INTEGER", "INT", "INTEGER"),
        ("TEXT", "LONGTEXT", "TEXT"), 
        ("BLOB", "LONGBLOB", "BLOB"),
        
        # Edge cases
        ("VARCHAR(255)", "VARCHAR(255)", "TEXT"),
        ("DECIMAL(10,2)", "DECIMAL(10,2)", "NUMERIC"),
        ("DATETIME", "DATETIME", "TEXT"),
        ("BOOLEAN", "BOOLEAN", "INTEGER"),
        ("MEDIUMBLOB", None, "BLOB"),  # MySQL → SQLite only
        ("UNKNOWN_TYPE", "LONGTEXT", "TEXT")
    ]
    
    print("Type Mapping Validation:")
    print("=" * 60)
    
    for i, (original, expected_mysql, expected_sqlite) in enumerate(test_cases):
        if expected_mysql:  # SQLite → MySQL test
            result_mysql = GetSQLiteToMySQLType(original)
            mysql_match = "✅" if result_mysql == expected_mysql else "❌"
            print(f"{i+1:2d}. SQLite '{original}' → MySQL '{result_mysql}' {mysql_match}")
            
            # Test round trip
            result_sqlite = GetMySQLToSQLiteType(result_mysql)
            sqlite_match = "✅" if result_sqlite == expected_sqlite else "❌"
            print(f"    Round trip → SQLite '{result_sqlite}' {sqlite_match}")
        else:  # MySQL → SQLite only
            result_sqlite = GetMySQLToSQLiteType(original)
            sqlite_match = "✅" if result_sqlite == expected_sqlite else "❌"
            print(f"{i+1:2d}. MySQL '{original}' → SQLite '{result_sqlite}' {sqlite_match}")
        
        print()

if __name__ == "__main__":
    ValidateTypeMapping()