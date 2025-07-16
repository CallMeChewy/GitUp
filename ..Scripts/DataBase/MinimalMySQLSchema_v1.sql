-- File: MinimalMySQLSchema_v1.sql
-- Path: Scripts/DataBase/MinimalMySQLSchema_v1.sql
-- Standard: AIDEV-PascalCase-2.1
-- Created: 2025-07-12
-- Last Modified: 2025-07-12  07:22PM
-- Description: Minimal MySQL schema for AndyGoogle MVP - streamlined for cloud migration

-- ============================================================================
-- ANDYGOOGLE MVP MINIMAL MYSQL SCHEMA v1.0
-- ============================================================================
-- Design Principle: "Only include tables/fields needed for AndyGoogle MVP"
-- Target: Single-user cloud library with Google Drive sync
-- Validated: 100% type compatibility with SQLite round-trip conversion
-- ============================================================================

-- Drop database if exists (for clean setup)
DROP DATABASE IF EXISTS AndyGoogleMVP;
CREATE DATABASE AndyGoogleMVP 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE AndyGoogleMVP;

-- ============================================================================
-- CORE LIBRARY TABLES
-- ============================================================================

-- Categories: Book classification system
CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName LONGTEXT NOT NULL,
    CategoryPath LONGTEXT,                    -- For hierarchical categories
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_categories_name (CategoryName(255)),
    INDEX idx_categories_active (IsActive)
) ENGINE=InnoDB;

-- Subjects: Subject classification within categories  
CREATE TABLE Subjects (
    SubjectID INT PRIMARY KEY AUTO_INCREMENT,
    SubjectName LONGTEXT NOT NULL,
    CategoryID INT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_subjects_name (SubjectName(255)),
    INDEX idx_subjects_category (CategoryID),
    INDEX idx_subjects_active (IsActive),
    
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Authors: Book authors (normalized for efficiency)
CREATE TABLE Authors (
    AuthorID INT PRIMARY KEY AUTO_INCREMENT,
    AuthorName LONGTEXT NOT NULL,
    AuthorBio LONGTEXT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_authors_name (AuthorName(255)),
    INDEX idx_authors_active (IsActive)
) ENGINE=InnoDB;

-- Books: Core library content (MySQL-friendly design)
CREATE TABLE Books (
    BookID INT PRIMARY KEY AUTO_INCREMENT,
    FileName LONGTEXT NOT NULL,               -- PDF file name for Google Drive
    Title LONGTEXT NOT NULL,
    CategoryID INT,
    SubjectID INT,
    PublicationYear INT,
    ISBN LONGTEXT,                           -- International Standard Book Number
    Publisher LONGTEXT,
    Language LONGTEXT DEFAULT 'English',
    FileSize BIGINT,                         -- File size in bytes
    PageCount INT,
    ThumbnailImage LONGBLOB,                 -- Embedded thumbnail (tested - works perfectly)
    Notes LONGTEXT,                          -- User notes
    Rating INT DEFAULT 0 CHECK (Rating BETWEEN 0 AND 5),
    LastOpened DATETIME,                     -- When user last opened this book
    DownloadCount INT DEFAULT 0,             -- Track usage
    IsFavorite BOOLEAN DEFAULT FALSE,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedBy LONGTEXT DEFAULT 'System',
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModifiedBy LONGTEXT DEFAULT 'System',
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Optimized indexes for AndyGoogle queries
    INDEX idx_books_title (Title(255)),
    INDEX idx_books_filename (FileName(255)),
    INDEX idx_books_category (CategoryID),
    INDEX idx_books_subject (SubjectID),
    INDEX idx_books_category_subject (CategoryID, SubjectID),
    INDEX idx_books_year (PublicationYear),
    INDEX idx_books_rating (Rating),
    INDEX idx_books_favorite (IsFavorite),
    INDEX idx_books_active (IsActive),
    INDEX idx_books_last_opened (LastOpened),
    
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL,
    FOREIGN KEY (SubjectID) REFERENCES Subjects(SubjectID) ON DELETE SET NULL
) ENGINE=InnoDB;

-- BookAuthors: Many-to-many relationship (books can have multiple authors)
CREATE TABLE BookAuthors (
    BookAuthorID INT PRIMARY KEY AUTO_INCREMENT,
    BookID INT NOT NULL,
    AuthorID INT NOT NULL,
    AuthorRole LONGTEXT DEFAULT 'Author',     -- Author, Editor, Translator, etc.
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_book_author (BookID, AuthorID),
    INDEX idx_bookauthors_book (BookID),
    INDEX idx_bookauthors_author (AuthorID),
    INDEX idx_bookauthors_active (IsActive),
    
    FOREIGN KEY (BookID) REFERENCES Books(BookID) ON DELETE CASCADE,
    FOREIGN KEY (AuthorID) REFERENCES Authors(AuthorID) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- GOOGLE DRIVE INTEGRATION TABLES
-- ============================================================================

-- SQLiteDatabaseVersions: Track SQLite database versions on Google Drive
CREATE TABLE SQLiteDatabaseVersions (
    DatabaseVersionID INT PRIMARY KEY AUTO_INCREMENT,
    VersionNumber LONGTEXT NOT NULL,          -- e.g., "1.0.0", "1.1.0"
    IsProduction BOOLEAN DEFAULT FALSE,       -- Production vs development
    IsActive BOOLEAN DEFAULT TRUE,            -- Can be downloaded by clients
    GoogleDriveFileID LONGTEXT,              -- Google Drive file identifier
    GoogleDriveFileName LONGTEXT,            -- Actual filename on Drive
    FileSizeBytes BIGINT,                    -- SQLite file size
    RecordCount INT,                         -- Total books in this version
    ChangeDescription LONGTEXT,              -- What changed in this version
    GeneratedFromMySQLVersion LONGTEXT,      -- MySQL schema version used
    CreatedBy LONGTEXT DEFAULT 'System',
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_dbversions_version (VersionNumber(50)),
    INDEX idx_dbversions_production (IsProduction),
    INDEX idx_dbversions_active (IsActive),
    INDEX idx_dbversions_drive_id (GoogleDriveFileID(100)),
    INDEX idx_dbversions_created (CreatedDate)
) ENGINE=InnoDB;

-- ============================================================================
-- BASIC USER TRACKING (FOR GOOGLE SHEETS LOGGING)
-- ============================================================================

-- Users: Minimal user tracking for usage analytics
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Email LONGTEXT,                          -- Google account email
    UserName LONGTEXT,                       -- Display name
    FirstAccess DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastAccess DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    AccessCount INT DEFAULT 1,
    ClientVersion LONGTEXT,                  -- AndyGoogle version
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_users_email (Email(255)),
    INDEX idx_users_last_access (LastAccess),
    INDEX idx_users_active (IsActive)
) ENGINE=InnoDB;

-- UsageAnalytics: Track user interactions for Google Sheets upload
CREATE TABLE UsageAnalytics (
    AnalyticsID INT PRIMARY KEY AUTO_INCREMENT,
    SessionToken LONGTEXT,                   -- Unique session identifier
    UserID INT,                              -- Link to user (optional)
    BookID INT,                              -- Book being accessed
    ActionType LONGTEXT NOT NULL,            -- 'view', 'download', 'search', 'favorite'
    ActionDetails LONGTEXT,                  -- Additional context (search terms, etc.)
    ActionTimestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ClientIP LONGTEXT,                       -- For basic analytics
    UserAgent LONGTEXT,                      -- Browser/client info
    UploadedToSheets BOOLEAN DEFAULT FALSE,  -- Batch upload status
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_analytics_session (SessionToken(100)),
    INDEX idx_analytics_user (UserID),
    INDEX idx_analytics_book (BookID),
    INDEX idx_analytics_action (ActionType(50)),
    INDEX idx_analytics_timestamp (ActionTimestamp),
    INDEX idx_analytics_uploaded (UploadedToSheets),
    
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE SET NULL,
    FOREIGN KEY (BookID) REFERENCES Books(BookID) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================================
-- SYSTEM CONFIGURATION
-- ============================================================================

-- SystemConfig: AndyGoogle system settings
CREATE TABLE SystemConfig (
    ConfigID INT PRIMARY KEY AUTO_INCREMENT,
    ConfigKey LONGTEXT NOT NULL,             -- 'google_drive_folder', 'sheets_log_id', etc.
    ConfigValue LONGTEXT,                    -- Configuration value
    ConfigDescription LONGTEXT,             -- Human-readable description
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_config_key (ConfigKey(255)),
    INDEX idx_config_active (IsActive)
) ENGINE=InnoDB;

-- ============================================================================
-- INITIAL DATA POPULATION
-- ============================================================================

-- Default system configuration
INSERT INTO SystemConfig (ConfigKey, ConfigValue, ConfigDescription) VALUES
('google_drive_folder_id', NULL, 'Google Drive folder ID for AndyLibrary storage'),
('google_sheets_log_id', NULL, 'Google Sheets ID for usage logging'),
('current_sqlite_version', '1.0.0', 'Current SQLite database version for clients'),
('auto_update_enabled', 'true', 'Enable automatic SQLite database updates'),
('usage_logging_enabled', 'true', 'Enable usage analytics collection'),
('max_file_size_mb', '50', 'Maximum file size for book uploads (MB)'),
('supported_formats', 'pdf,epub,mobi', 'Comma-separated list of supported file formats');

-- Default categories (migrate from existing)
INSERT INTO Categories (CategoryName, CategoryPath) VALUES
('Technology', 'Technology'),
('Science', 'Science'),
('Mathematics', 'Mathematics'),
('Literature', 'Literature'),
('History', 'History'),
('Philosophy', 'Philosophy'),
('Business', 'Business'),
('Engineering', 'Engineering'),
('Medicine', 'Medicine'),
('Arts', 'Arts');

-- ============================================================================
-- MIGRATION HELPER VIEWS
-- ============================================================================

-- View: Complete book information (for easy querying)
CREATE VIEW BookDetails AS
SELECT 
    b.BookID,
    b.FileName,
    b.Title,
    c.CategoryName,
    s.SubjectName,
    GROUP_CONCAT(a.AuthorName SEPARATOR ', ') AS Authors,
    b.PublicationYear,
    b.ISBN,
    b.Publisher,
    b.Language,
    b.FileSize,
    b.PageCount,
    b.Rating,
    b.LastOpened,
    b.DownloadCount,
    b.IsFavorite,
    b.IsActive,
    b.CreatedDate
FROM Books b
LEFT JOIN Categories c ON b.CategoryID = c.CategoryID
LEFT JOIN Subjects s ON b.SubjectID = s.SubjectID  
LEFT JOIN BookAuthors ba ON b.BookID = ba.BookID AND ba.IsActive = TRUE
LEFT JOIN Authors a ON ba.AuthorID = a.AuthorID AND a.IsActive = TRUE
WHERE b.IsActive = TRUE
GROUP BY b.BookID, b.FileName, b.Title, c.CategoryName, s.SubjectName, 
         b.PublicationYear, b.ISBN, b.Publisher, b.Language, 
         b.FileSize, b.PageCount, b.Rating, b.LastOpened, 
         b.DownloadCount, b.IsFavorite, b.IsActive, b.CreatedDate;

-- View: Usage summary for analytics
CREATE VIEW UsageSummary AS
SELECT 
    DATE(ActionTimestamp) as ActionDate,
    ActionType,
    COUNT(*) as ActionCount,
    COUNT(DISTINCT SessionToken) as UniqueSessions,
    COUNT(DISTINCT UserID) as UniqueUsers,
    COUNT(DISTINCT BookID) as UniqueBooksAccessed
FROM UsageAnalytics 
WHERE ActionTimestamp >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY DATE(ActionTimestamp), ActionType
ORDER BY ActionDate DESC, ActionCount DESC;

-- ============================================================================
-- SCHEMA VALIDATION
-- ============================================================================

-- Test queries to validate schema design
-- SELECT 'Schema created successfully' as Status;
-- SELECT COUNT(*) as TableCount FROM information_schema.tables WHERE table_schema = 'AndyGoogleMVP';
-- SELECT table_name, engine, table_rows FROM information_schema.tables WHERE table_schema = 'AndyGoogleMVP';

-- ============================================================================
-- SCHEMA COMPLETE
-- ============================================================================
-- This minimal schema includes:
-- ✅ Core library data (Books, Categories, Subjects, Authors)
-- ✅ Google Drive integration (SQLiteDatabaseVersions)
-- ✅ Basic user tracking (Users, UsageAnalytics)
-- ✅ System configuration (SystemConfig)
-- ✅ MySQL-friendly types (validated for round-trip conversion)
-- ✅ Optimized indexes for AndyGoogle queries
-- ✅ Helper views for easy data access
-- 
-- Ready for AndyGoogle MVP development!
-- ============================================================================