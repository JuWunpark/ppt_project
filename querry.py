"""CREATE DATABASE ppt_platform;
USE ppt_platform;

-- 사용자 테이블
CREATE TABLE User (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    nickname VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 디자인 테이블
CREATE TABLE Design (
    design_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- PPT 테이블 (design_id를 NULL 허용)
CREATE TABLE PPT (
    ppt_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    design_id INT NULL,  -- NULL 허용 (SET NULL이 가능하도록 변경)
    title VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (design_id) REFERENCES Design(design_id) ON DELETE SET NULL
);

-- 파일 저장 테이블 (웹에서 열람 가능한 파일만 저장)
CREATE TABLE File (
    file_id INT AUTO_INCREMENT PRIMARY KEY,
    ppt_id INT NOT NULL,
    file_path VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ppt_id) REFERENCES PPT(ppt_id) ON DELETE CASCADE
);

-- 커뮤니티 테이블 (PPT 공유 가능)
CREATE TABLE Community (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    ppt_id INT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES User(user_id) ON DELETE CASCADE,
    FOREIGN KEY (ppt_id) REFERENCES PPT(ppt_id) ON DELETE SET NULL
);
"""