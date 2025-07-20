-- Cloudflare D1 Database Schema for Points Management System
-- Run: wrangler d1 execute points-management-db --file=./schema.sql

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- 用户积分表
CREATE TABLE IF NOT EXISTS user_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    user_name TEXT,
    total_points INTEGER DEFAULT 0,
    valid_days INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- 积分历史记录表
CREATE TABLE IF NOT EXISTS points_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    points_change INTEGER NOT NULL,
    operation_type TEXT NOT NULL, -- 'add', 'subtract', 'reset'
    description TEXT,
    operator_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operator_id) REFERENCES users(id)
);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 会话表（可选，主要使用KV存储）
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    data TEXT NOT NULL,
    expires_at DATETIME NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- 二维码记录表
CREATE TABLE IF NOT EXISTS qr_codes (
    id TEXT PRIMARY KEY,
    url TEXT NOT NULL,
    expiry_time DATETIME,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (created_by) REFERENCES users(id)
);

-- 插入默认管理员用户 (密码: admin123)
INSERT OR IGNORE INTO users (username, password_hash, email, role, is_active) 
VALUES ('admin', 'ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f', 'admin@example.com', 'admin', 1);

-- 插入默认系统配置
INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES
('points_expiry_days', '90', '积分有效期（天）'),
('max_upload_size', '10485760', '最大上传文件大小（字节）'),
('qr_cache_limit', '100', '二维码缓存数量限制'),
('qr_default_expiry', '86400', '二维码默认有效期（秒）'),
('pagination_size', '20', '分页大小'),
('system_title', '积分查询系统', '系统标题'),
('system_description', '便捷的积分查询和管理系统', '系统描述');

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_user_points_user_id ON user_points(user_id);
CREATE INDEX IF NOT EXISTS idx_points_history_user_id ON points_history(user_id);
CREATE INDEX IF NOT EXISTS idx_points_history_created_at ON points_history(created_at);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON sessions(expires_at);
CREATE INDEX IF NOT EXISTS idx_qr_codes_created_at ON qr_codes(created_at);
CREATE INDEX IF NOT EXISTS idx_qr_codes_is_active ON qr_codes(is_active);
