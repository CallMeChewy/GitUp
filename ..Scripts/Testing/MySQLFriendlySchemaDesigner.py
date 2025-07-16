# File: MySQLFriendlySchemaDesigner.py
# Path: Scripts/Testing/MySQLFriendlySchemaDesigner.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  07:15PM
"""
Description: MySQL-friendly SQLite schema designer and mapping validator
Ensures SQLite schemas are designed for optimal MySQL compatibility
"""

import sqlite3
import mysql.connector
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime

class MySQLFriendlySchemaDesigner:
    """Design SQLite schemas that convert cleanly to MySQL"""
    
    # MySQL-friendly SQLite type recommendations
    MYSQL_FRIENDLY_TYPES = {
        # Use these SQLite types for best MySQL compatibility
        "INTEGER": "INT",           # Clean 1:1 mapping
        "BIGINT": "BIGINT",         # Large integers
        "REAL": "DOUBLE",           # Floating point
        "TEXT": "LONGTEXT",         # Variable text
        "BLOB": "LONGBLOB",         # Binary data
        
        # Avoid these problematic SQLite types:
        # "NUMERIC" -> causes precision issues
        # "DECIMAL(x,y)" -> not natively supported in SQLite
        # "VARCHAR(n)" -> SQLite ignores length, MySQL enforces it
        # "CHAR(n)" -> same length enforcement issue
    }
    
    # MySQL specification constraints
    MYSQL_CONSTRAINTS = {
        "VARCHAR_MAX_LENGTH": 65535,
        "CHAR_MAX_LENGTH": 255,
        "TEXT_MAX_LENGTH": 65535,
        "MEDIUMTEXT_MAX_LENGTH": 16777215,
        "LONGTEXT_MAX_LENGTH": 4294967295,
        "TINYINT_RANGE": (-128, 127),
        "SMALLINT_RANGE": (-32768, 32767),
        "MEDIUMINT_RANGE": (-8388608, 8388607),
        "INT_RANGE": (-2147483648, 2147483647),
        "BIGINT_RANGE": (-9223372036854775808, 9223372036854775807),
        "TIMESTAMP_RANGE": ("1970-01-01 00:00:01", "2038-01-19 03:14:07"),
        "DATETIME_RANGE": ("1000-01-01 00:00:00", "9999-12-31 23:59:59"),
        "DATE_RANGE": ("1000-01-01", "9999-12-31")
    }
    
    def __init__(self):
        self.validation_results = []
        
    def AnalyzeCurrentSchema(self, db_path: str) -> Dict[str, Any]:
        """Analyze current SQLite schema for MySQL compatibility"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        analysis = {
            "database": db_path,
            "timestamp": datetime.now().isoformat(),
            "tables": {},
            "compatibility_score": 0,
            "recommendations": []
        }
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        tables = [row[0] for row in cursor.fetchall()]
        
        total_columns = 0
        compatible_columns = 0
        
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            table_analysis = {
                "columns": [],
                "issues": [],
                "mysql_friendly_score": 0
            }
            
            for col in columns:
                col_name = col[1]
                col_type = col[2].upper()
                is_pk = col[5] == 1
                
                # Analyze column compatibility
                compatibility = self.AnalyzeColumnCompatibility(col_name, col_type, is_pk)
                table_analysis["columns"].append(compatibility)
                
                total_columns += 1
                if compatibility["mysql_friendly"]:
                    compatible_columns += 1
                    table_analysis["mysql_friendly_score"] += 1
                else:
                    table_analysis["issues"].extend(compatibility["issues"])
            
            table_analysis["mysql_friendly_score"] = (table_analysis["mysql_friendly_score"] / len(columns)) * 100
            analysis["tables"][table] = table_analysis
        
        analysis["compatibility_score"] = (compatible_columns / total_columns) * 100 if total_columns > 0 else 0
        analysis["total_columns"] = total_columns
        analysis["compatible_columns"] = compatible_columns
        
        # Generate overall recommendations
        analysis["recommendations"] = self.GenerateRecommendations(analysis)
        
        conn.close()
        return analysis
    
    def AnalyzeColumnCompatibility(self, col_name: str, col_type: str, is_pk: bool) -> Dict[str, Any]:
        """Analyze individual column for MySQL compatibility"""
        compatibility = {
            "name": col_name,
            "sqlite_type": col_type,
            "mysql_type": None,
            "mysql_friendly": False,
            "issues": [],
            "recommendations": []
        }
        
        # Check type compatibility
        base_type = col_type.split('(')[0].strip()
        
        if base_type in self.MYSQL_FRIENDLY_TYPES:
            compatibility["mysql_type"] = self.MYSQL_FRIENDLY_TYPES[base_type]
            compatibility["mysql_friendly"] = True
        else:
            # Analyze problematic types
            if "NUMERIC" in col_type or "DECIMAL" in col_type:
                compatibility["issues"].append("NUMERIC/DECIMAL types may lose precision in round-trip conversion")
                compatibility["recommendations"].append("Use TEXT for decimal values requiring exact precision")
                compatibility["mysql_type"] = "DECIMAL(65,30)"
            
            elif "VARCHAR" in col_type or "CHAR" in col_type:
                compatibility["issues"].append("VARCHAR/CHAR length constraints not enforced in SQLite")
                compatibility["recommendations"].append("Use TEXT type for variable-length strings")
                compatibility["mysql_type"] = "LONGTEXT"
            
            elif any(keyword in col_type for keyword in ["DATETIME", "TIMESTAMP", "DATE"]):
                compatibility["issues"].append("Date/time types stored as TEXT in SQLite, format validation needed")
                compatibility["recommendations"].append("Validate date formats match MySQL requirements")
                compatibility["mysql_type"] = "DATETIME"
            
            else:
                # Unknown type - apply SQLite affinity rules
                if "INT" in col_type:
                    compatibility["mysql_type"] = "INT"
                    compatibility["mysql_friendly"] = True
                elif any(keyword in col_type for keyword in ["CHAR", "CLOB", "TEXT"]):
                    compatibility["mysql_type"] = "LONGTEXT"
                    compatibility["mysql_friendly"] = True
                elif "BLOB" in col_type:
                    compatibility["mysql_type"] = "LONGBLOB"
                    compatibility["mysql_friendly"] = True
                elif any(keyword in col_type for keyword in ["REAL", "FLOA", "DOUB"]):
                    compatibility["mysql_type"] = "DOUBLE"
                    compatibility["mysql_friendly"] = True
                else:
                    compatibility["mysql_type"] = "LONGTEXT"
                    compatibility["issues"].append(f"Unknown type '{col_type}', defaulting to LONGTEXT")
        
        # Check for naming issues
        if col_name.lower() in ["order", "group", "select", "from", "where", "insert", "update", "delete"]:
            compatibility["issues"].append(f"Column name '{col_name}' is a MySQL reserved word")
            compatibility["recommendations"].append(f"Rename to '{col_name}Value' or use backticks in queries")
        
        return compatibility
    
    def GenerateRecommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate overall recommendations for schema improvement"""
        recommendations = []
        
        if analysis["compatibility_score"] < 80:
            recommendations.append("Schema has significant MySQL compatibility issues - consider redesign")
        elif analysis["compatibility_score"] < 95:
            recommendations.append("Schema has minor compatibility issues - review individual column recommendations")
        else:
            recommendations.append("Schema is highly MySQL-compatible")
        
        # Collect unique issues across all tables
        all_issues = set()
        for table_data in analysis["tables"].values():
            for issue in table_data["issues"]:
                all_issues.add(issue)
        
        if "NUMERIC/DECIMAL types may lose precision" in str(all_issues):
            recommendations.append("Consider storing precise decimals as TEXT with application-level validation")
        
        if "VARCHAR/CHAR length constraints" in str(all_issues):
            recommendations.append("Replace VARCHAR/CHAR with TEXT for better SQLite/MySQL compatibility")
        
        if "Date/time types stored as TEXT" in str(all_issues):
            recommendations.append("Implement date format validation: 'YYYY-MM-DD HH:MM:SS' for DATETIME")
        
        return recommendations
    
    def GenerateMySQLFriendlySchema(self, original_schema: Dict[str, Any]) -> str:
        """Generate improved MySQL-friendly SQLite schema"""
        sql_statements = []
        sql_statements.append("-- MySQL-Friendly SQLite Schema")
        sql_statements.append("-- Generated: " + datetime.now().isoformat())
        sql_statements.append("-- Optimized for clean MySQL conversion")
        sql_statements.append("")
        
        for table_name, table_data in original_schema["tables"].items():
            sql_statements.append(f"-- Table: {table_name}")
            sql_statements.append(f"CREATE TABLE {table_name} (")
            
            column_definitions = []
            primary_keys = []
            
            for col in table_data["columns"]:
                col_name = col["name"]
                
                # Use MySQL-friendly type
                if col["mysql_friendly"]:
                    sqlite_type = col["sqlite_type"]
                else:
                    # Apply recommendations
                    if "NUMERIC" in col["sqlite_type"] or "DECIMAL" in col["sqlite_type"]:
                        sqlite_type = "TEXT"  # Store as text for precision
                    elif "VARCHAR" in col["sqlite_type"] or "CHAR" in col["sqlite_type"]:
                        sqlite_type = "TEXT"
                    else:
                        sqlite_type = "TEXT"  # Safe default
                
                # Handle reserved words
                if col_name.lower() in ["order", "group", "select", "from", "where"]:
                    col_name = f"{col_name}Value"
                
                column_def = f"    {col_name} {sqlite_type}"
                
                # Add constraints
                if col["sqlite_type"] == "INTEGER" and any("PRIMARY KEY" in str(col) for col in table_data["columns"]):
                    column_def += " PRIMARY KEY"
                
                column_definitions.append(column_def)
            
            sql_statements.append(",\n".join(column_definitions))
            sql_statements.append(");")
            sql_statements.append("")
        
        return "\n".join(sql_statements)
    
    def ValidateAgainstMySQLSpecs(self, mysql_type: str, sample_data: Any = None) -> Dict[str, Any]:
        """Validate data against MySQL specifications"""
        validation = {
            "mysql_type": mysql_type,
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        mysql_type_upper = mysql_type.upper()
        
        # Validate against MySQL constraints
        if "VARCHAR" in mysql_type_upper:
            # Extract length if specified
            if "(" in mysql_type:
                try:
                    length = int(mysql_type.split("(")[1].split(")")[0])
                    if length > self.MYSQL_CONSTRAINTS["VARCHAR_MAX_LENGTH"]:
                        validation["errors"].append(f"VARCHAR length {length} exceeds MySQL limit {self.MYSQL_CONSTRAINTS['VARCHAR_MAX_LENGTH']}")
                        validation["valid"] = False
                except:
                    validation["warnings"].append("Could not parse VARCHAR length specification")
            
        elif "CHAR" in mysql_type_upper and "(" in mysql_type:
            try:
                length = int(mysql_type.split("(")[1].split(")")[0])
                if length > self.MYSQL_CONSTRAINTS["CHAR_MAX_LENGTH"]:
                    validation["errors"].append(f"CHAR length {length} exceeds MySQL limit {self.MYSQL_CONSTRAINTS['CHAR_MAX_LENGTH']}")
                    validation["valid"] = False
            except:
                validation["warnings"].append("Could not parse CHAR length specification")
        
        elif "TIMESTAMP" in mysql_type_upper:
            validation["warnings"].append("TIMESTAMP has limited range in MySQL: 1970-2038")
            validation["warnings"].append("Consider using DATETIME for dates outside this range")
        
        return validation

def main():
    designer = MySQLFriendlySchemaDesigner()
    
    # Analyze current MyLibrary database
    print("🔍 Analyzing Current SQLite Schema for MySQL Compatibility")
    print("=" * 65)
    
    db_path = "/home/herb/Desktop/AndyGoogle/Data/Databases/MyLibrary.db"
    analysis = designer.AnalyzeCurrentSchema(db_path)
    
    print(f"Database: {analysis['database']}")
    print(f"Overall Compatibility Score: {analysis['compatibility_score']:.1f}%")
    print(f"Compatible Columns: {analysis['compatible_columns']}/{analysis['total_columns']}")
    print()
    
    # Show table-by-table analysis
    for table_name, table_data in analysis["tables"].items():
        print(f"📋 Table: {table_name}")
        print(f"   MySQL-Friendly Score: {table_data['mysql_friendly_score']:.1f}%")
        
        for col in table_data["columns"]:
            status = "✅" if col["mysql_friendly"] else "⚠️"
            print(f"   {status} {col['name']}: {col['sqlite_type']} → {col['mysql_type']}")
            
            for issue in col["issues"]:
                print(f"      ⚠️  {issue}")
            for rec in col["recommendations"]:
                print(f"      💡 {rec}")
        
        if table_data["issues"]:
            print(f"   Issues: {len(table_data['issues'])}")
        print()
    
    # Show overall recommendations
    print("💡 Overall Recommendations:")
    for i, rec in enumerate(analysis["recommendations"], 1):
        print(f"{i}. {rec}")
    
    # Save analysis
    output_file = f"Results/Testing/schema_analysis_{int(datetime.now().timestamp())}.json"
    import os
    os.makedirs("Results/Testing", exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n📄 Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()