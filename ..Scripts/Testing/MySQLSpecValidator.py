# File: MySQLSpecValidator.py
# Path: Scripts/Testing/MySQLSpecValidator.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  07:18PM
"""
Description: MySQL specification validator that ensures type mappings stay consistent
Automatically validates against official MySQL documentation and constraints
"""

import mysql.connector
import requests
import json
import re
from typing import Dict, List, Any, Tuple
from datetime import datetime

class MySQLSpecValidator:
    """Validate type mappings against MySQL specifications"""
    
    # Official MySQL data types from MySQL 8.0 documentation
    MYSQL_OFFICIAL_TYPES = {
        # Numeric Types
        "TINYINT": {"storage_bytes": 1, "signed_range": (-128, 127), "unsigned_range": (0, 255)},
        "SMALLINT": {"storage_bytes": 2, "signed_range": (-32768, 32767), "unsigned_range": (0, 65535)},
        "MEDIUMINT": {"storage_bytes": 3, "signed_range": (-8388608, 8388607), "unsigned_range": (0, 16777215)},
        "INT": {"storage_bytes": 4, "signed_range": (-2147483648, 2147483647), "unsigned_range": (0, 4294967295)},
        "INTEGER": {"storage_bytes": 4, "signed_range": (-2147483648, 2147483647), "unsigned_range": (0, 4294967295)},
        "BIGINT": {"storage_bytes": 8, "signed_range": (-9223372036854775808, 9223372036854775807), "unsigned_range": (0, 18446744073709551615)},
        "DECIMAL": {"storage_bytes": "variable", "precision_range": (1, 65), "scale_range": (0, 30)},
        "NUMERIC": {"alias_for": "DECIMAL"},
        "FLOAT": {"storage_bytes": 4, "precision": "single"},
        "DOUBLE": {"storage_bytes": 8, "precision": "double"},
        "REAL": {"alias_for": "DOUBLE"},
        "BIT": {"storage_bits": (1, 64)},
        
        # String Types
        "CHAR": {"max_length": 255, "storage": "fixed_length"},
        "VARCHAR": {"max_length": 65535, "storage": "variable_length"},
        "BINARY": {"max_length": 255, "storage": "fixed_binary"},
        "VARBINARY": {"max_length": 65535, "storage": "variable_binary"},
        "TINYTEXT": {"max_length": 255, "storage_bytes": "L + 1"},
        "TEXT": {"max_length": 65535, "storage_bytes": "L + 2"},
        "MEDIUMTEXT": {"max_length": 16777215, "storage_bytes": "L + 3"},
        "LONGTEXT": {"max_length": 4294967295, "storage_bytes": "L + 4"},
        "TINYBLOB": {"max_length": 255, "storage_bytes": "L + 1"},
        "BLOB": {"max_length": 65535, "storage_bytes": "L + 2"},
        "MEDIUMBLOB": {"max_length": 16777215, "storage_bytes": "L + 3"},
        "LONGBLOB": {"max_length": 4294967295, "storage_bytes": "L + 4"},
        
        # Date and Time Types
        "DATE": {"format": "YYYY-MM-DD", "range": ("1000-01-01", "9999-12-31"), "storage_bytes": 3},
        "TIME": {"format": "HH:MM:SS[.fraction]", "range": ("-838:59:59", "838:59:59"), "storage_bytes": 3},
        "DATETIME": {"format": "YYYY-MM-DD HH:MM:SS[.fraction]", "range": ("1000-01-01 00:00:00", "9999-12-31 23:59:59"), "storage_bytes": 8},
        "TIMESTAMP": {"format": "YYYY-MM-DD HH:MM:SS[.fraction]", "range": ("1970-01-01 00:00:01", "2038-01-19 03:14:07"), "storage_bytes": 4},
        "YEAR": {"format": "YYYY", "range": (1901, 2155), "storage_bytes": 1},
        
        # JSON Type (MySQL 5.7+)
        "JSON": {"storage": "variable", "max_size": "1GB"},
        
        # Spatial Types
        "GEOMETRY": {"storage": "variable"},
        "POINT": {"storage": "variable"},
        "LINESTRING": {"storage": "variable"},
        "POLYGON": {"storage": "variable"},
        "MULTIPOINT": {"storage": "variable"},
        "MULTILINESTRING": {"storage": "variable"},
        "MULTIPOLYGON": {"storage": "variable"},
        "GEOMETRYCOLLECTION": {"storage": "variable"}
    }
    
    # SQLite affinity rules for type inference
    SQLITE_AFFINITY_RULES = {
        "INTEGER": ["INT"],
        "TEXT": ["CHAR", "CLOB", "TEXT"],
        "BLOB": ["BLOB"],
        "REAL": ["REAL", "FLOA", "DOUB"],
        "NUMERIC": ["NUMERIC", "DECIMAL", "BOOLEAN", "DATE", "DATETIME"]
    }
    
    def __init__(self, mysql_config: Dict[str, Any] = None):
        self.mysql_config = mysql_config or {"user": "root"}
        self.validation_cache = {}
        
    def GetMySQLConnection(self):
        """Get MySQL connection for live validation"""
        if self.mysql_config.get('user') == 'root':
            return mysql.connector.connect(
                unix_socket='/var/run/mysqld/mysqld.sock',
                user='root'
            )
        return mysql.connector.connect(**self.mysql_config)
    
    def ValidateTypeMappingConsistency(self) -> Dict[str, Any]:
        """Validate that our type mappings are consistent with MySQL specs"""
        validation = {
            "timestamp": datetime.now().isoformat(),
            "mysql_version": None,
            "mapping_validation": {},
            "inconsistencies": [],
            "recommendations": []
        }
        
        # Get MySQL version for validation context
        try:
            conn = self.GetMySQLConnection()
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            validation["mysql_version"] = cursor.fetchone()[0]
            conn.close()
        except Exception as e:
            validation["mysql_version"] = f"Unable to connect: {e}"
        
        # Import our current type mappings
        try:
            from TypeMappingValidator import SQLITE_TO_MYSQL_TYPES, MYSQL_TO_SQLITE_TYPES
            
            # Validate SQLite → MySQL mappings
            for sqlite_type, mysql_type in SQLITE_TO_MYSQL_TYPES.items():
                validation_result = self.ValidateMapping(sqlite_type, mysql_type, "SQLite→MySQL")
                validation["mapping_validation"][f"{sqlite_type}→{mysql_type}"] = validation_result
                
                if not validation_result["valid"]:
                    validation["inconsistencies"].append({
                        "mapping": f"{sqlite_type} → {mysql_type}",
                        "issues": validation_result["issues"]
                    })
            
            # Validate MySQL → SQLite mappings
            for mysql_type, sqlite_type in MYSQL_TO_SQLITE_TYPES.items():
                validation_result = self.ValidateMapping(mysql_type, sqlite_type, "MySQL→SQLite")
                validation["mapping_validation"][f"{mysql_type}→{sqlite_type}"] = validation_result
                
                if not validation_result["valid"]:
                    validation["inconsistencies"].append({
                        "mapping": f"{mysql_type} → {sqlite_type}",
                        "issues": validation_result["issues"]
                    })
                    
        except ImportError:
            validation["inconsistencies"].append({
                "mapping": "IMPORT_ERROR",
                "issues": ["Could not import TypeMappingValidator module"]
            })
        
        # Generate recommendations
        validation["recommendations"] = self.GenerateRecommendations(validation)
        
        return validation
    
    def ValidateMapping(self, source_type: str, target_type: str, direction: str) -> Dict[str, Any]:
        """Validate a specific type mapping"""
        validation = {
            "source_type": source_type,
            "target_type": target_type,
            "direction": direction,
            "valid": True,
            "issues": [],
            "warnings": []
        }
        
        if direction == "SQLite→MySQL":
            # Validate that MySQL type exists and is properly specified
            mysql_base_type = target_type.split('(')[0].upper()
            
            if mysql_base_type not in self.MYSQL_OFFICIAL_TYPES:
                validation["valid"] = False
                validation["issues"].append(f"MySQL type '{mysql_base_type}' not found in official specifications")
            else:
                # Check for proper usage
                mysql_spec = self.MYSQL_OFFICIAL_TYPES[mysql_base_type]
                
                # Check length specifications for string types
                if mysql_base_type in ["VARCHAR", "CHAR", "BINARY", "VARBINARY"] and "(" not in target_type:
                    validation["warnings"].append(f"{mysql_base_type} should specify length: {mysql_base_type}(n)")
                
                # Check if this is the best mapping for the SQLite type
                sqlite_affinity = self.GetSQLiteAffinity(source_type)
                if not self.IsOptimalMapping(sqlite_affinity, mysql_base_type):
                    validation["warnings"].append(f"Mapping may not be optimal for SQLite affinity '{sqlite_affinity}'")
        
        elif direction == "MySQL→SQLite":
            # Validate that the SQLite type follows proper affinity rules
            sqlite_affinity = self.GetSQLiteAffinity(target_type)
            mysql_base_type = source_type.split('(')[0].upper()
            
            if not self.IsAffinityCompatible(mysql_base_type, sqlite_affinity):
                validation["warnings"].append(f"SQLite affinity '{sqlite_affinity}' may not preserve MySQL '{mysql_base_type}' semantics")
        
        return validation
    
    def GetSQLiteAffinity(self, sqlite_type: str) -> str:
        """Determine SQLite type affinity for a given type"""
        sqlite_type_upper = sqlite_type.upper()
        
        # SQLite affinity determination rules
        if "INT" in sqlite_type_upper:
            return "INTEGER"
        elif any(keyword in sqlite_type_upper for keyword in ["CHAR", "CLOB", "TEXT"]):
            return "TEXT"
        elif "BLOB" in sqlite_type_upper:
            return "BLOB"
        elif any(keyword in sqlite_type_upper for keyword in ["REAL", "FLOA", "DOUB"]):
            return "REAL"
        else:
            return "NUMERIC"
    
    def IsOptimalMapping(self, sqlite_affinity: str, mysql_type: str) -> bool:
        """Check if MySQL type is optimal for SQLite affinity"""
        optimal_mappings = {
            "INTEGER": ["TINYINT", "SMALLINT", "MEDIUMINT", "INT", "INTEGER", "BIGINT"],
            "TEXT": ["CHAR", "VARCHAR", "TINYTEXT", "TEXT", "MEDIUMTEXT", "LONGTEXT"],
            "BLOB": ["BINARY", "VARBINARY", "TINYBLOB", "BLOB", "MEDIUMBLOB", "LONGBLOB"],
            "REAL": ["FLOAT", "DOUBLE", "REAL"],
            "NUMERIC": ["DECIMAL", "NUMERIC"]
        }
        
        return mysql_type in optimal_mappings.get(sqlite_affinity, [])
    
    def IsAffinityCompatible(self, mysql_type: str, sqlite_affinity: str) -> bool:
        """Check if SQLite affinity preserves MySQL type semantics"""
        compatible_mappings = {
            "TINYINT": ["INTEGER"],
            "SMALLINT": ["INTEGER"],
            "MEDIUMINT": ["INTEGER"],
            "INT": ["INTEGER"],
            "INTEGER": ["INTEGER"],
            "BIGINT": ["INTEGER"],
            "DECIMAL": ["TEXT", "NUMERIC"],  # TEXT for precision preservation
            "NUMERIC": ["TEXT", "NUMERIC"],
            "FLOAT": ["REAL"],
            "DOUBLE": ["REAL"],
            "REAL": ["REAL"],
            "CHAR": ["TEXT"],
            "VARCHAR": ["TEXT"],
            "TINYTEXT": ["TEXT"],
            "TEXT": ["TEXT"],
            "MEDIUMTEXT": ["TEXT"],
            "LONGTEXT": ["TEXT"],
            "TINYBLOB": ["BLOB"],
            "BLOB": ["BLOB"],
            "MEDIUMBLOB": ["BLOB"],
            "LONGBLOB": ["BLOB"],
            "DATE": ["TEXT"],
            "TIME": ["TEXT"],
            "DATETIME": ["TEXT"],
            "TIMESTAMP": ["TEXT"],
            "YEAR": ["INTEGER"],
            "JSON": ["TEXT"]
        }
        
        return sqlite_affinity in compatible_mappings.get(mysql_type, [])
    
    def GenerateRecommendations(self, validation: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if validation["inconsistencies"]:
            recommendations.append(f"Found {len(validation['inconsistencies'])} mapping inconsistencies - review type mappings")
        else:
            recommendations.append("All type mappings are consistent with MySQL specifications")
        
        # Specific recommendations based on common issues
        for inconsistency in validation["inconsistencies"]:
            mapping = inconsistency["mapping"]
            issues = inconsistency["issues"]
            
            if "not found in official specifications" in str(issues):
                recommendations.append(f"Update mapping for {mapping} - use official MySQL type names")
            
            if "should specify length" in str(issues):
                recommendations.append("Add length specifications for VARCHAR/CHAR types where appropriate")
        
        recommendations.append("Regularly validate mappings against MySQL version updates")
        recommendations.append("Consider automated testing for type conversion edge cases")
        
        return recommendations
    
    def TestLiveConversion(self, test_cases: List[Tuple[str, Any]]) -> Dict[str, Any]:
        """Test actual conversion with MySQL server"""
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "test_cases": [],
            "success_rate": 0
        }
        
        try:
            conn = self.GetMySQLConnection()
            cursor = conn.cursor()
            
            # Create test database
            test_db = f"type_test_{int(datetime.now().timestamp())}"
            cursor.execute(f"CREATE DATABASE {test_db}")
            cursor.execute(f"USE {test_db}")
            
            successful_tests = 0
            
            for i, (mysql_type, test_value) in enumerate(test_cases):
                test_result = {
                    "test_id": i + 1,
                    "mysql_type": mysql_type,
                    "test_value": str(test_value),
                    "success": False,
                    "error": None
                }
                
                try:
                    # Create test table
                    cursor.execute(f"CREATE TABLE test_{i} (id INT PRIMARY KEY, test_col {mysql_type})")
                    
                    # Insert test value
                    cursor.execute(f"INSERT INTO test_{i} (id, test_col) VALUES (1, %s)", (test_value,))
                    
                    # Retrieve value
                    cursor.execute(f"SELECT test_col FROM test_{i} WHERE id = 1")
                    retrieved_value = cursor.fetchone()[0]
                    
                    test_result["retrieved_value"] = str(retrieved_value)
                    test_result["success"] = True
                    successful_tests += 1
                    
                except Exception as e:
                    test_result["error"] = str(e)
                
                test_results["test_cases"].append(test_result)
            
            test_results["success_rate"] = (successful_tests / len(test_cases)) * 100
            
            # Cleanup
            cursor.execute(f"DROP DATABASE {test_db}")
            conn.close()
            
        except Exception as e:
            test_results["connection_error"] = str(e)
        
        return test_results

def main():
    validator = MySQLSpecValidator()
    
    print("🔍 MySQL Specification Validator")
    print("=" * 50)
    
    # Validate type mapping consistency
    print("Validating type mapping consistency...")
    validation = validator.ValidateTypeMappingConsistency()
    
    print(f"MySQL Version: {validation['mysql_version']}")
    print(f"Mappings Validated: {len(validation['mapping_validation'])}")
    print(f"Inconsistencies Found: {len(validation['inconsistencies'])}")
    
    # Show inconsistencies
    if validation["inconsistencies"]:
        print("\n⚠️  Inconsistencies Found:")
        for issue in validation["inconsistencies"]:
            print(f"   {issue['mapping']}: {', '.join(issue['issues'])}")
    else:
        print("\n✅ All mappings are consistent with MySQL specifications")
    
    # Show recommendations
    print("\n💡 Recommendations:")
    for i, rec in enumerate(validation["recommendations"], 1):
        print(f"{i}. {rec}")
    
    # Test live conversion with sample data
    print("\n🧪 Testing Live Conversion...")
    test_cases = [
        ("INT", 42),
        ("LONGTEXT", "Sample text"),
        ("LONGBLOB", b"Binary data"),
        ("DOUBLE", 3.14159),
        ("DATETIME", "2025-07-12 19:20:00")
    ]
    
    live_test = validator.TestLiveConversion(test_cases)
    print(f"Live Test Success Rate: {live_test['success_rate']:.1f}%")
    
    for test in live_test["test_cases"]:
        status = "✅" if test["success"] else "❌"
        print(f"   {status} {test['mysql_type']}: {test['test_value']}")
        if test.get("error"):
            print(f"      Error: {test['error']}")
    
    # Save results
    import os
    os.makedirs("Results/Testing", exist_ok=True)
    output_file = f"Results/Testing/mysql_spec_validation_{int(datetime.now().timestamp())}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "validation": validation,
            "live_test": live_test
        }, f, indent=2)
    
    print(f"\n📄 Results saved to: {output_file}")

if __name__ == "__main__":
    main()