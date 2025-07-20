# 积分管理系统

基于直播观看时长的智能积分计算与管理平台，支持多种数据格式，自动识别用户信息，实时统计积分变化。

## ✨ 主要功能

- 🔐 **用户认证**: 安全的登录注册系统
- 📤 **数据上传**: 支持多种格式文件上传（CSV、Excel、TSV、JSON）
- 📊 **积分管理**: 智能积分计算和统计分析
- 🔍 **用户查询**: 快速查询个人积分情况
- 👥 **多用户隔离**: 不同管理员数据完全隔离
- 📱 **响应式设计**: 完美适配桌面和移动设备

## 🏗️ 项目结构

```
积分管理系统/
├── 📁 flask-version/              # Flask传统版本
│   ├── app.py                     # Flask主应用
│   ├── users.csv                  # 用户数据
│   ├── templates/                 # 页面模板
│   ├── data/                      # 用户数据存储
│   └── README.md                  # Flask版本说明
├── 📁 cloudflare-version/         # Cloudflare现代版本
│   ├── functions/                 # Workers Functions
│   ├── dist/                      # 静态前端文件
│   ├── schema.sql                 # D1数据库结构
│   ├── wrangler.toml              # Cloudflare配置
│   └── README.md                  # Cloudflare版本说明
├── 📁 docs/                       # 项目文档
│   ├── CLOUDFLARE_DEPLOYMENT.md   # Cloudflare部署指南
│   ├── MIGRATION_GUIDE.md         # 迁移指南
│   ├── HISTORICAL_DATA_GUIDE.md   # 历史数据处理
│   └── PROJECT_STRUCTURE.md       # 项目结构说明
├── 📁 .github/workflows/          # CI/CD配置
│   └── deploy.yml                 # 自动部署工作流
├── package.json                   # Node.js配置
└── README.md                      # 项目主说明（本文件）
```

## 🚀 快速开始

### 方式一：Cloudflare Pages（推荐）
现代化的无服务器部署，支持全球CDN加速：

```bash
cd cloudflare-version/

# 1. 安装依赖
npm install

# 2. 登录Cloudflare
npx wrangler login

# 3. 创建资源并部署
npm run setup && npm run deploy
```

详细说明：[cloudflare-version/README.md](./cloudflare-version/README.md)

### 方式二：Flask本地部署
传统的Python Flask部署方式：

```bash
cd flask-version/

# 1. 安装依赖
pip install flask pandas openpyxl

# 2. 启动应用
python app.py

# 3. 访问系统
# 浏览器打开: http://127.0.0.1:5000/
```

详细说明：[flask-version/README.md](./flask-version/README.md)

## 🔑 默认账户
- 用户名: `admin`
- 密码: `admin123`

## 📊 积分规则

- **时长要求**: 直播观看时长 ≥ 40分钟
- **积分奖励**: 每天最多1分
- **有效期**: 90天后过期
- **防重复**: 同一用户同一天最多获得1分

## 📁 项目结构

```
jifen/
├── app.py                          # 主应用文件
├── users.csv                       # 用户数据
├── templates/                      # 页面模板
├── data/                          # 用户数据存储
├── uploads/                        # 上传临时目录
└── docs/                          # 文档说明
```

## 📖 使用指南

1. **注册账户**: 创建管理员账户
2. **登录系统**: 使用账户登录
3. **上传数据**: 上传直播观看数据文件
4. **查看统计**: 查看积分统计和用户排名
5. **用户查询**: 用户可查询个人积分

## 🔒 数据安全

- 密码加密存储
- 用户数据隔离
- 会话安全管理
- 文件上传验证

## 📝 支持格式

### 文件格式
- CSV (.csv)
- Excel (.xlsx, .xls)
- TSV (.tsv)
- JSON (.json)

### 数据列要求
- 用户ID/编号
- 用户名称/昵称
- 直播观看时长
- 观看时间（可选）

## 🛠️ 技术栈

- **后端**: Python Flask
- **数据处理**: pandas
- **前端**: HTML5 + CSS3 + JavaScript
- **存储**: CSV文件存储
- **认证**: Flask Session

## 📞 技术支持

如有问题或建议，请查看项目文档或联系开发团队。

---

**版本**: v2.0  
**更新时间**: 2025-07-20
