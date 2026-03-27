-- Create database
CREATE DATABASE IF NOT EXISTS contract_review_ai;

-- Select database
USE contract_review_ai;

-- Documents table for storing OCR results
CREATE TABLE IF NOT EXISTS documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    file_name VARCHAR(255),
    file_type VARCHAR(50),
    extracted_text LONGTEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Run SQL:
SELECT id, file_name FROM documents;

-- To view stored OCR text:
SELECT extracted_text FROM documents WHERE id=1;

-- reset the documents table:
TRUNCATE TABLE documents;