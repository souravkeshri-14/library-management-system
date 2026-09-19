-- Run this only if your MySQL user does not have permission to create tables.
-- The Streamlit app also tries to create this table automatically.

CREATE TABLE IF NOT EXISTS book_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    username VARCHAR(100) NOT NULL,
    student_name VARCHAR(150) NOT NULL,
    reg_no VARCHAR(100) NOT NULL,
    request_date DATE NOT NULL,
    status ENUM('Pending', 'Accepted', 'Rejected') NOT NULL DEFAULT 'Pending',
    admin_note VARCHAR(255) DEFAULT NULL,
    issue_id INT DEFAULT NULL,
    INDEX idx_request_username (username),
    INDEX idx_request_status (status),
    INDEX idx_request_book (book_id)
);


-- Add this to an existing users table if you prefer to run the migration manually.
-- The Streamlit app performs this migration automatically when it starts.
ALTER TABLE users ADD COLUMN reg_no VARCHAR(30) NULL UNIQUE;

-- Existing issue_books tables: the app performs these migrations automatically.
ALTER TABLE issue_books MODIFY COLUMN reg_no VARCHAR(30) NOT NULL;
ALTER TABLE issue_books ADD COLUMN issue_type VARCHAR(20) NOT NULL DEFAULT 'Online';
