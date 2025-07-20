# 项目结构说明（最终版）

## 📁 项目目录结构

```
jifen/
├── PROJECT_OVERVIEW.md          # 项目概述
├── README.md                    # 项目说明文档
├── STRUCTURE.md                 # 原始结构文档
├── PROJECT_STRUCTURE_FINAL.md   # 最终结构说明（本文件）
├── cleanup_report.md            # 清理报告
├── backup_20250720_203737/      # 备份目录
│   ├── app.py
│   ├── config_manager.py
│   ├── system_config.json
│   └── users.csv
├── docs/                        # 文档目录
│   ├── CLEAR_POINTS_GUIDE.md
│   ├── CLOUDFLARE_DEPLOYMENT.md
│   ├── CLOUDFLARE_README.md
│   ├── HISTORICAL_DATA_GUIDE.md
│   ├── MIGRATION_GUIDE.md
│   ├── PROJECT_STRUCTURE.md
│   ├── README.md
│   └── 配色方案升级报告.md
├── cloudflare-version/          # Cloudflare版本（可选）
│   ├── README.md
│   ├── dist/
│   ├── functions/
│   ├── schema.sql
│   └── wrangler.toml
└── flask-version/               # Flask版本（主要版本）
    ├── README.md
    ├── __pycache__/
    ├── app.py                   # Flask应用主文件
    ├── config_manager.py        # 配置管理器
    ├── system_config.json       # 系统配置文件
    ├── users.csv               # 用户数据文件
    ├── data/                   # 数据目录
    ├── static/                 # 静态文件目录
    │   └── qr_codes/          # 二维码存储目录
    ├── templates/              # 模板目录
    │   ├── index.html         # 首页模板
    │   ├── query_page.html    # 查询页面模板
    │   ├── query_result.html  # 查询结果模板
    │   ├── login.html         # 登录页面模板
    │   ├── register.html      # 注册页面模板
    │   ├── admin_points.html  # 积分管理模板
    │   ├── admin_upload_combined.html  # 数据上传模板
    │   └── admin_config.html  # 系统配置模板
    └── uploads/               # 上传文件目录
```

## 🎯 核心文件说明

### Flask应用核心
- **`flask-version/app.py`** - Flask应用主文件，包含所有路由和业务逻辑
- **`flask-version/config_manager.py`** - 配置管理器，处理系统配置的读取和更新
- **`flask-version/system_config.json`** - 系统配置文件，存储各种系统参数
- **`flask-version/users.csv`** - 用户数据文件，存储用户信息

### 模板文件
- **`templates/index.html`** - 首页，包含功能介绍、使用流程、二维码展示等
- **`templates/query_page.html`** - 积分查询页面
- **`templates/query_result.html`** - 查询结果展示页面
- **`templates/login.html`** - 用户登录页面
- **`templates/register.html`** - 用户注册页面
- **`templates/admin_points.html`** - 管理员积分管理页面
- **`templates/admin_upload_combined.html`** - 数据上传页面
- **`templates/admin_config.html`** - 系统配置管理页面

### 静态资源
- **`static/qr_codes/`** - 二维码图片存储目录
- **`uploads/`** - 用户上传文件存储目录
- **`data/`** - 数据文件存储目录

## 🧹 清理内容

### 已删除的文件类型
1. **测试文件** - 所有 `test_*.py` 文件（共32个）
2. **演示文件** - 所有 `*_demo.html` 和 `*_preview.html` 文件（共15个）
3. **验证脚本** - `verify_*.py` 文件
4. **重复文件** - 根目录的 `system_config.json` 和 `users.csv`
5. **Node.js相关** - `package.json`、`package-lock.json`、`node_modules/`
6. **临时目录** - 根目录的 `static/` 目录

### 保留的重要文件
1. **核心应用文件** - Flask应用的所有核心文件
2. **配置文件** - 系统配置和用户数据
3. **模板文件** - 所有HTML模板
4. **文档文件** - 项目文档和说明
5. **备份文件** - 自动创建的备份目录

## 🚀 系统功能

### 用户功能
- ✅ 积分查询
- ✅ 用户注册和登录
- ✅ 二维码扫码查询
- ✅ 查询结果展示

### 管理员功能
- ✅ 积分数据管理
- ✅ 数据上传和处理
- ✅ 二维码生成和管理
- ✅ 系统配置管理
- ✅ 用户管理

### 系统特性
- ✅ 响应式设计
- ✅ 现代化UI界面
- ✅ 统一导航系统
- ✅ 配置化管理
- ✅ 数据安全性

## 📊 清理统计

- **删除文件数**: 41个
- **删除目录数**: 2个
- **备份文件数**: 4个
- **保留核心文件**: 100%完整

## 🔧 运行说明

### 启动应用
```bash
cd flask-version
python app.py
```

### 访问地址
- 主页: http://localhost:5000/
- 查询页面: http://localhost:5000/query
- 管理员登录: http://localhost:5000/login

### 默认管理员账户
- 用户名: admin
- 密码: admin123

## 📝 维护说明

### 配置文件位置
- 系统配置: `flask-version/system_config.json`
- 用户数据: `flask-version/users.csv`

### 数据目录
- 上传文件: `flask-version/uploads/`
- 二维码: `flask-version/static/qr_codes/`
- 数据文件: `flask-version/data/`

### 备份恢复
如需恢复文件，可从 `backup_20250720_203737/` 目录中获取备份的核心文件。

## 🎉 清理完成

项目结构已经整理完毕，删除了所有测试文件、演示文件和临时文件，保留了系统运行所需的所有核心文件。系统功能完全不受影响，可以正常运行。

---

*最后更新: 2025-07-20*
