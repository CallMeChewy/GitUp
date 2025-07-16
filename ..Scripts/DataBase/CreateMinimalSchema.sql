-- AndyGoogle MVP Minimal MySQL Schema
-- Clean version for direct execution

DROP DATABASE IF EXISTS AndyGoogleMVP;
CREATE DATABASE AndyGoogleMVP CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE AndyGoogleMVP;

-- Categories table
CREATE TABLE Categories (
    CategoryID INT PRIMARY KEY AUTO_INCREMENT,
    CategoryName LONGTEXT NOT NULL,
    CategoryPath LONGTEXT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Subjects table
CREATE TABLE Subjects (
    SubjectID INT PRIMARY KEY AUTO_INCREMENT,
    SubjectName LONGTEXT NOT NULL,
    CategoryID INT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL
);

-- Authors table
CREATE TABLE Authors (
    AuthorID INT PRIMARY KEY AUTO_INCREMENT,
    AuthorName LONGTEXT NOT NULL,
    AuthorBio LONGTEXT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Books table
CREATE TABLE Books (
    BookID INT PRIMARY KEY AUTO_INCREMENT,
    FileName LONGTEXT NOT NULL,
    Title LONGTEXT NOT NULL,
    CategoryID INT,
    SubjectID INT,
    PublicationYear INT,
    ISBN LONGTEXT,
    Publisher LONGTEXT,
    Language LONGTEXT DEFAULT 'English',
    FileSize BIGINT,
    PageCount INT,
    ThumbnailImage LONGBLOB,
    Notes LONGTEXT,
    Rating INT DEFAULT 0,
    LastOpened DATETIME,
    DownloadCount INT DEFAULT 0,
    IsFavorite BOOLEAN DEFAULT FALSE,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedBy LONGTEXT DEFAULT 'System',
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModifiedBy LONGTEXT DEFAULT 'System',
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (CategoryID) REFERENCES Categories(CategoryID) ON DELETE SET NULL,
    FOREIGN KEY (SubjectID) REFERENCES Subjects(SubjectID) ON DELETE SET NULL
);

-- BookAuthors junction table
CREATE TABLE BookAuthors (
    BookAuthorID INT PRIMARY KEY AUTO_INCREMENT,
    BookID INT NOT NULL,
    AuthorID INT NOT NULL,
    AuthorRole LONGTEXT DEFAULT 'Author',
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_book_author (BookID, AuthorID),
    FOREIGN KEY (BookID) REFERENCES Books(BookID) ON DELETE CASCADE,
    FOREIGN KEY (AuthorID) REFERENCES Authors(AuthorID) ON DELETE CASCADE
);

-- SQLiteDatabaseVersions table
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
    CreatedBy LONGTEXT DEFAULT 'System',
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Users table
CREATE TABLE Users (
    UserID INT PRIMARY KEY AUTO_INCREMENT,
    Email LONGTEXT,
    UserName LONGTEXT,
    FirstAccess DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastAccess DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    AccessCount INT DEFAULT 1,
    ClientVersion LONGTEXT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- UsageAnalytics table
CREATE TABLE UsageAnalytics (
    AnalyticsID INT PRIMARY KEY AUTO_INCREMENT,
    SessionToken LONGTEXT,
    UserID INT,
    BookID INT,
    ActionType LONGTEXT NOT NULL,
    ActionDetails LONGTEXT,
    ActionTimestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ClientIP LONGTEXT,
    UserAgent LONGTEXT,
    UploadedToSheets BOOLEAN DEFAULT FALSE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE SET NULL,
    FOREIGN KEY (BookID) REFERENCES Books(BookID) ON DELETE CASCADE
);

-- SystemConfig table
CREATE TABLE SystemConfig (
    ConfigID INT PRIMARY KEY AUTO_INCREMENT,
    ConfigKey LONGTEXT NOT NULL,
    ConfigValue LONGTEXT,
    ConfigDescription LONGTEXT,
    IsActive BOOLEAN DEFAULT TRUE,
    CreatedDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    LastModified DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Insert default configuration
INSERT INTO SystemConfig (ConfigKey, ConfigValue, ConfigDescription) VALUES
('google_drive_folder_id', NULL, 'Google Drive folder ID for AndyLibrary storage'),
('google_sheets_log_id', NULL, 'Google Sheets ID for usage logging'),
('current_sqlite_version', '1.0.0', 'Current SQLite database version for clients'),
('auto_update_enabled', 'true', 'Enable automatic SQLite database updates'),
('usage_logging_enabled', 'true', 'Enable usage analytics collection');

-- Create useful view
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
GROUP BY b.BookID;