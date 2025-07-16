# File: MigrateToMinimalMySQL.py
# Path: Scripts/DataBase/MigrateToMinimalMySQL.py
# Standard: AIDEV-PascalCase-2.1
# Created: 2025-07-12
# Last Modified: 2025-07-12  07:25PM
"""
Description: Migration script to populate minimal MySQL schema with existing MyLibrary data
Uses validated type mapping and handles author normalization
"""

import sqlite3
import mysql.connector
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any

class MyLibraryToMinimalMySQLMigrator:
    """Migrate MyLibrary.db to AndyGoogle minimal MySQL schema"""
    
    def __init__(self, mysql_config: Dict[str, Any]):
        self.mysql_config = mysql_config
        self.migration_log = {
            'timestamp': datetime.now().isoformat(),
            'source_db': None,
            'target_db': 'AndyGoogleMVP',
            'stats': {},
            'errors': [],
            'warnings': []
        }
        self.author_cache = {}  # Cache for author normalization
        
    def GetMySQLConnection(self):
        """Get MySQL connection with auth_socket for root"""
        if self.mysql_config.get('user') == 'root':
            return mysql.connector.connect(
                unix_socket='/var/run/mysqld/mysqld.sock',
                user='root'
            )
        return mysql.connector.connect(**self.mysql_config)
    
    def AnalyzeSourceData(self, sqlite_db_path: str) -> Dict[str, Any]:
        """Analyze source SQLite database"""
        conn = sqlite3.connect(sqlite_db_path)
        cursor = conn.cursor()
        
        analysis = {
            'database': sqlite_db_path,
            'table_counts': {},
            'data_issues': [],
            'author_analysis': {}
        }
        
        # Count records in each table
        tables = ['books', 'categories', 'subjects']
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                analysis['table_counts'][table] = cursor.fetchone()[0]
            except Exception as e:
                analysis['data_issues'].append(f"Error counting {table}: {e}")
        
        # Analyze author data for normalization
        try:
            cursor.execute("SELECT DISTINCT author FROM books WHERE author IS NOT NULL AND author != ''")
            authors = [row[0] for row in cursor.fetchall()]
            
            # Detect multiple authors in single field
            multi_author_books = []
            for author_field in authors:
                if any(sep in author_field for sep in [',', '&', ' and ', ';']):
                    multi_author_books.append(author_field)
            
            analysis['author_analysis'] = {
                'total_unique_authors': len(authors),
                'books_with_multiple_authors': len(multi_author_books),
                'multi_author_examples': multi_author_books[:5]
            }
            
        except Exception as e:
            analysis['data_issues'].append(f"Error analyzing authors: {e}")
        
        conn.close()
        return analysis
    
    def CreateMinimalSchema(self) -> bool:
        """Create the minimal MySQL schema"""
        try:
            mysql_conn = self.GetMySQLConnection()
            cursor = mysql_conn.cursor()
            
            # Create database
            cursor.execute("DROP DATABASE IF EXISTS AndyGoogleMVP")
            cursor.execute("CREATE DATABASE AndyGoogleMVP CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            cursor.execute("USE AndyGoogleMVP")
            
            # Create tables in dependency order
            print("Creating Categories table...")
            cursor.execute("""
                CREATE TABLE Categories (
                    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
                    CategoryName LONGTEXT NOT NULL,
                    CategoryPath LONGTEXT,
                    IsActive BOOLEAN DEFAULT TRUE,
                    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            print("Creating Subjects table...")
            cursor.execute("""
                CREATE TABLE Subjects (
                    SubjectID INT PRIMARY KEY AUTO_INCREMENT,
                    SubjectName LONGTEXT NOT NULL,
                    CategoryID INT,
                    IsActive BOOLEAN DEFAULT TRUE,
                    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL
                )
            """)
            
            print("Creating Authors table...")
            cursor.execute("""
                CREATE TABLE Authors (
                    AuthorID INT PRIMARY KEY AUTO_INCREMENT,
                    AuthorName LONGTEXT NOT NULL,
                    AuthorBio LONGTEXT,
                    IsActive BOOLEAN DEFAULT TRUE,
                    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            print("Creating Books table...")
            cursor.execute("""
                CREATE TABLE Books (
                    BookID INT PRIMARY KEY AUTO_INCREMENT,
                    FileName LONGTEXT NOT NULL,
                    Title LONGTEXT NOT NULL,
                    CategoryID INT,
                    SubjectID INT,
                    PublicationYear INT,
                    ISBN LONGTEXT,
                    Publisher LONGTEXT,
                    Language LONGTEXT,
                    FileSize BIGINT,
                    PageCount INT,
                    ThumbnailImage LONGBLOB,
                    Notes LONGTEXT,
                    Rating INT DEFAULT 0,
                    LastOpened DATETIME,
                    DownloadCount INT DEFAULT 0,
                    IsFavorite BOOLEAN DEFAULT FALSE,
                    IsActive BOOLEAN DEFAULT TRUE,
                    CreatedBy LONGTEXT,
                    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                    LastModifiedBy LONGTEXT,
                    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL,
                    FOREIGN KEY (SubjectID) REFERENCES Subjects(SubjectID) ON DELETE SET NULL
                )
            """)
            
            print("Creating BookAuthors table...")
            cursor.execute("""
                CREATE TABLE BookAuthors (
                    BookAuthorID INT PRIMARY KEY AUTO_INCREMENT,
                    BookID INT NOT NULL,
                    AuthorID INT NOT NULL,
                    AuthorRole LONGTEXT,
                    IsActive BOOLEAN DEFAULT TRUE,
                    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_book_author (BookID, AuthorID),
                    FOREIGN KEY (BookID) REFERENCES Books(BookID) ON DELETE CASCADE,
                    FOREIGN KEY (AuthorID) REFERENCES Authors(AuthorID) ON DELETE CASCADE
                )
            """)
            
            print("Creating SQLiteDatabaseVersions table...")
            cursor.execute("""
                CREATE TABLE SQLiteDatabaseVersions (
                    DatabaseVersionID INT PRIMARY KEY AUTO_INCREMENT,
                    VersionNumber LONGTEXT NOT NULL,
                    IsProduction BOOLEAN DEFAULT FALSE,
                    IsActive BOOLEAN DEFAULT TRUE,
                    GoogleDriveFileID LONGTEXT,
                    GoogleDriveFileName LONGTEXT,
                    FileSizeBytes BIGINT,
                    RecordCount INT,
                    ChangeDescription LONGTEXT,
                    GeneratedFromMySQLVersion LONGTEXT,
                    CreatedBy LONGTEXT,
                    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
                    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
            """)
            
            mysql_conn.commit()
            mysql_conn.close()
            return True
            
        except Exception as e:
            self.migration_log['errors'].append(f"Schema creation failed: {e}")
            print(f"Schema error: {e}")
            return False
    
    def NormalizeAuthor(self, author_string: str) -> List[str]:
        """Normalize author string into individual author names"""
        if not author_string or author_string.strip() == '':
            return []
        
        # Common separators for multiple authors
        separators = [', ', ' & ', ' and ', '; ', '|']
        
        authors = [author_string]
        for sep in separators:
            new_authors = []
            for author in authors:
                new_authors.extend(author.split(sep))
            authors = new_authors
        
        # Clean up author names
        normalized_authors = []
        for author in authors:
            author = author.strip()
            # Remove common prefixes/suffixes
            author = author.replace('Dr. ', '').replace('Prof. ', '').replace('Mr. ', '').replace('Ms. ', '')
            author = author.replace(' (Editor)', '').replace(' (Ed.)', '')
            
            if author and len(author) > 1:
                normalized_authors.append(author)
        
        return normalized_authors
    
    def GetOrCreateAuthor(self, mysql_cursor, author_name: str) -> int:
        """Get existing author ID or create new author"""
        if author_name in self.author_cache:
            return self.author_cache[author_name]
        
        # Check if author exists
        mysql_cursor.execute("SELECT AuthorID FROM Authors WHERE AuthorName = %s", (author_name,))
        result = mysql_cursor.fetchone()
        
        if result:
            author_id = result[0]
        else:
            # Create new author
            mysql_cursor.execute(
                "INSERT INTO Authors (AuthorName) VALUES (%s)",
                (author_name,)
            )
            author_id = mysql_cursor.lastrowid
        
        self.author_cache[author_name] = author_id
        return author_id
    
    def MigrateCategories(self, sqlite_cursor, mysql_cursor) -> Dict[int, int]:
        """Migrate categories and return mapping of old ID to new ID"""
        sqlite_cursor.execute("SELECT id, category FROM categories ORDER BY id")
        categories = sqlite_cursor.fetchall()
        
        category_mapping = {}
        
        for old_id, category_name in categories:
            # Check if category already exists
            mysql_cursor.execute("SELECT CategoryID FROM Categories WHERE CategoryName = %s", (category_name,))
            result = mysql_cursor.fetchone()
            
            if result:
                new_id = result[0]
            else:
                # Insert new category
                mysql_cursor.execute(
                    "INSERT INTO Categories (CategoryName, CategoryPath) VALUES (%s, %s)",
                    (category_name, category_name)
                )
                new_id = mysql_cursor.lastrowid
            
            category_mapping[old_id] = new_id
        
        self.migration_log['stats']['categories_migrated'] = len(categories)
        return category_mapping
    
    def MigrateSubjects(self, sqlite_cursor, mysql_cursor, category_mapping: Dict[int, int]) -> Dict[int, int]:
        """Migrate subjects and return mapping of old ID to new ID"""
        sqlite_cursor.execute("SELECT id, category_id, subject FROM subjects ORDER BY id")
        subjects = sqlite_cursor.fetchall()
        
        subject_mapping = {}
        
        for old_id, old_category_id, subject_name in subjects:
            new_category_id = category_mapping.get(old_category_id)
            
            # Check if subject already exists
            mysql_cursor.execute(
                "SELECT SubjectID FROM Subjects WHERE SubjectName = %s AND CategoryID = %s",
                (subject_name, new_category_id)
            )
            result = mysql_cursor.fetchone()
            
            if result:
                new_id = result[0]
            else:
                # Insert new subject
                mysql_cursor.execute(
                    "INSERT INTO Subjects (SubjectName, CategoryID) VALUES (%s, %s)",
                    (subject_name, new_category_id)
                )
                new_id = mysql_cursor.lastrowid
            
            subject_mapping[old_id] = new_id
        
        self.migration_log['stats']['subjects_migrated'] = len(subjects)
        return subject_mapping
    
    def MigrateBooks(self, sqlite_cursor, mysql_cursor, category_mapping: Dict[int, int], subject_mapping: Dict[int, int]):
        """Migrate books with author normalization"""
        sqlite_cursor.execute("""
            SELECT id, title, category_id, subject_id, author, FilePath, ThumbnailImage,
                   last_opened, LastOpened, Rating, Notes, FileSize, PageCount, 
                   CreatedBy, LastModifiedBy
            FROM books 
            ORDER BY id
        """)
        
        books = sqlite_cursor.fetchall()
        books_migrated = 0
        authors_created = 0
        book_author_links = 0
        
        for book_data in books:
            (old_id, title, old_category_id, old_subject_id, author_string, 
             file_path, thumbnail, last_opened, last_opened2, rating, notes, 
             file_size, page_count, created_by, last_modified_by) = book_data
            
            # Map foreign keys
            new_category_id = category_mapping.get(old_category_id)
            new_subject_id = subject_mapping.get(old_subject_id)
            
            # Handle last_opened (use the more recent one if both exist)
            last_opened_final = last_opened2 or last_opened
            
            # Extract filename from path
            filename = file_path.split('/')[-1] if file_path else f"book_{old_id}.pdf"
            
            # Insert book
            mysql_cursor.execute("""
                INSERT INTO Books (
                    FileName, Title, CategoryID, SubjectID, FileSize, PageCount,
                    ThumbnailImage, Notes, Rating, LastOpened, CreatedBy, LastModifiedBy
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                filename, title, new_category_id, new_subject_id, file_size, page_count,
                thumbnail, notes, rating, last_opened_final, created_by, last_modified_by
            ))
            
            new_book_id = mysql_cursor.lastrowid
            books_migrated += 1
            
            # Handle authors
            if author_string:
                author_names = self.NormalizeAuthor(author_string)
                for author_name in author_names:
                    author_id = self.GetOrCreateAuthor(mysql_cursor, author_name)
                    
                    # Link book to author (ignore duplicates)
                    try:
                        mysql_cursor.execute(
                            "INSERT INTO BookAuthors (BookID, AuthorID, AuthorRole) VALUES (%s, %s, %s)",
                            (new_book_id, author_id, 'Author')
                        )
                        book_author_links += 1
                    except mysql.connector.IntegrityError:
                        # Duplicate entry - skip it
                        pass
        
        self.migration_log['stats']['books_migrated'] = books_migrated
        self.migration_log['stats']['authors_created'] = len(self.author_cache)
        self.migration_log['stats']['book_author_links'] = book_author_links
    
    def CreateInitialDatabaseVersion(self, mysql_cursor):
        """Create initial SQLite database version record"""
        mysql_cursor.execute("""
            INSERT INTO SQLiteDatabaseVersions (
                VersionNumber, IsProduction, IsActive, 
                ChangeDescription, GeneratedFromMySQLVersion
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            "1.0.0", True, True,
            "Initial migration from MyLibrary.db to AndyGoogle minimal schema",
            "MinimalMySQLSchema_v1"
        ))
        
        version_id = mysql_cursor.lastrowid
        self.migration_log['stats']['initial_version_id'] = version_id
    
    def RunMigration(self, sqlite_db_path: str) -> Dict[str, Any]:
        """Run complete migration process"""
        self.migration_log['source_db'] = sqlite_db_path
        
        print(f"🔄 Starting migration from {sqlite_db_path}")
        
        # Step 1: Analyze source data
        print("Step 1: Analyzing source data...")
        analysis = self.AnalyzeSourceData(sqlite_db_path)
        self.migration_log['source_analysis'] = analysis
        
        print(f"   Books: {analysis['table_counts'].get('books', 0)}")
        print(f"   Categories: {analysis['table_counts'].get('categories', 0)}")
        print(f"   Subjects: {analysis['table_counts'].get('subjects', 0)}")
        print(f"   Unique authors: {analysis['author_analysis'].get('total_unique_authors', 0)}")
        
        # Step 2: Create schema
        print("Step 2: Creating minimal MySQL schema...")
        if not self.CreateMinimalSchema():
            return self.migration_log
        
        # Step 3: Connect to databases
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        mysql_conn = self.GetMySQLConnection()
        mysql_cursor = mysql_conn.cursor()
        mysql_cursor.execute("USE AndyGoogleMVP")
        
        try:
            # Step 4: Migrate data
            print("Step 3: Migrating categories...")
            category_mapping = self.MigrateCategories(sqlite_cursor, mysql_cursor)
            
            print("Step 4: Migrating subjects...")
            subject_mapping = self.MigrateSubjects(sqlite_cursor, mysql_cursor, category_mapping)
            
            print("Step 5: Migrating books and authors...")
            self.MigrateBooks(sqlite_cursor, mysql_cursor, category_mapping, subject_mapping)
            
            print("Step 6: Creating initial database version...")
            self.CreateInitialDatabaseVersion(mysql_cursor)
            
            # Commit all changes
            mysql_conn.commit()
            
            # Final statistics
            mysql_cursor.execute("SELECT COUNT(*) FROM Books")
            final_book_count = mysql_cursor.fetchone()[0]
            
            mysql_cursor.execute("SELECT COUNT(*) FROM Authors")
            final_author_count = mysql_cursor.fetchone()[0]
            
            self.migration_log['stats']['final_book_count'] = final_book_count
            self.migration_log['stats']['final_author_count'] = final_author_count
            self.migration_log['success'] = True
            
            print(f"✅ Migration completed successfully!")
            print(f"   Final book count: {final_book_count}")
            print(f"   Final author count: {final_author_count}")
            
        except Exception as e:
            self.migration_log['errors'].append(f"Migration failed: {e}")
            mysql_conn.rollback()
            
        finally:
            sqlite_conn.close()
            mysql_conn.close()
        
        return self.migration_log

def main():
    mysql_config = {'user': 'root'}
    migrator = MyLibraryToMinimalMySQLMigrator(mysql_config)
    
    sqlite_db_path = "/home/herb/Desktop/AndyGoogle/Data/Databases/MyLibrary.db"
    
    print("🚀 MyLibrary → AndyGoogle Minimal MySQL Migration")
    print("=" * 60)
    
    results = migrator.RunMigration(sqlite_db_path)
    
    # Save migration log
    import os
    os.makedirs("Results/Migration", exist_ok=True)
    log_file = f"Results/Migration/migration_log_{int(datetime.now().timestamp())}.json"
    with open(log_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Migration log saved to: {log_file}")
    
    if results.get('success'):
        print("\n🎉 AndyGoogle minimal MySQL schema is ready!")
        print("Next: Begin AndyGoogle project structure with Google Drive integration")
    else:
        print(f"\n❌ Migration failed. Check {log_file} for details.")

if __name__ == "__main__":
    main()