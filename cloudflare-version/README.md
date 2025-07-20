# 积分查询系统 - Cloudflare Pages版本

这是积分查询系统的Cloudflare Pages适配版本，使用Cloudflare Pages、Functions、D1数据库和KV存储构建。

## 🏗️ 架构说明

### 技术栈
- **前端**: 静态HTML + JavaScript
- **后端**: Cloudflare Functions (Edge Functions)
- **数据库**: Cloudflare D1 (SQLite)
- **会话存储**: Cloudflare KV
- **部署平台**: Cloudflare Pages

### 项目结构
```
cloudflare-version/
├── public/                 # 静态文件目录
│   ├── index.html         # 首页
│   ├── query.html         # 查询页面
│   ├── login.html         # 登录页面
│   ├── register.html      # 注册页面
│   ├── admin/             # 管理员页面
│   │   ├── points.html    # 积分管理
│   │   ├── upload.html    # 数据上传
│   │   └── config.html    # 系统配置
│   ├── css/               # 样式文件
│   │   └── cloudflare-styles.css
│   └── js/                # JavaScript文件
│       └── cloudflare-adapter.js
├── functions/             # Cloudflare Functions
│   └── api/               # API路由
│       ├── query.js       # 查询API
│       ├── auth/          # 认证相关API
│       │   ├── login.js
│       │   ├── register.js
│       │   ├── check.js
│       │   └── logout.js
│       ├── admin/         # 管理员API
│       │   ├── points.js
│       │   └── upload.js
│       ├── config/        # 配置API
│       │   └── system.js
│       └── qr/            # 二维码API
│           └── generate.js
├── schema.sql             # 数据库结构
├── wrangler.toml          # Cloudflare配置
└── README.md              # 本文件
```

## 🚀 部署步骤

### 1. 准备工作

#### 安装Wrangler CLI
```bash
npm install -g wrangler
```

#### 登录Cloudflare
```bash
wrangler login
```

### 2. 创建资源

#### 创建D1数据库
```bash
wrangler d1 create points-management-db
```

记录返回的数据库ID，更新`wrangler.toml`中的`database_id`。

#### 创建KV命名空间
```bash
# 创建会话存储
wrangler kv:namespace create "SESSIONS"
wrangler kv:namespace create "SESSIONS" --preview

# 创建缓存存储
wrangler kv:namespace create "CACHE"
wrangler kv:namespace create "CACHE" --preview
```

记录返回的命名空间ID，更新`wrangler.toml`中的相应配置。

### 3. 配置数据库

#### 初始化数据库结构
```bash
wrangler d1 execute points-management-db --file=./schema.sql
```

#### 验证数据库
```bash
wrangler d1 execute points-management-db --command="SELECT * FROM users;"
```

### 4. 更新配置

编辑`wrangler.toml`文件，更新以下配置：
- `database_id`: D1数据库ID
- KV命名空间ID
- 环境变量（密钥等）

### 5. 部署应用

#### 本地开发
```bash
wrangler pages dev public --compatibility-date=2024-01-15
```

#### 部署到Cloudflare Pages
```bash
wrangler pages deploy public
```

或者通过Cloudflare Dashboard连接Git仓库自动部署。

## ⚙️ 配置说明

### 环境变量
在Cloudflare Dashboard的Pages设置中配置以下环境变量：

- `SECRET_KEY`: 用于加密的密钥
- `ADMIN_PASSWORD_HASH`: 管理员密码哈希
- `ENVIRONMENT`: 环境标识（production/preview）

### 数据库配置
默认管理员账户：
- 用户名: `admin`
- 密码: `admin123`
- 密码哈希: `ef92b778bafe771e89245b89ecbc08a44a4e166c06659911881f383d4473e94f`

### KV存储用途
- `SESSIONS`: 用户会话存储
- `CACHE`: 系统缓存和临时数据

## 🔧 API接口

### 认证相关
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `GET /api/auth/check` - 检查登录状态
- `POST /api/auth/logout` - 用户注销

### 查询相关
- `POST /api/query` - 积分查询

### 管理员相关
- `GET /api/admin/points` - 获取积分数据
- `POST /api/admin/upload` - 上传数据文件

### 配置相关
- `GET /api/config/system` - 获取系统配置
- `POST /api/config/system` - 更新系统配置

### 二维码相关
- `POST /api/qr/generate` - 生成二维码

## 🎯 功能特性

### 用户功能
- ✅ 积分查询
- ✅ 用户注册和登录
- ✅ 响应式设计
- ✅ 实时消息提示

### 管理员功能
- ✅ 积分数据管理
- ✅ 数据上传处理
- ✅ 系统配置管理
- ✅ 二维码生成

### 技术特性
- ✅ 边缘计算（全球CDN）
- ✅ 无服务器架构
- ✅ 自动扩缩容
- ✅ 高可用性
- ✅ 低延迟

## 🔒 安全特性

- 会话管理（KV存储）
- 密码哈希存储
- HTTPS强制
- CSRF保护
- 输入验证
- 权限控制

## 📊 性能优化

- 静态资源CDN缓存
- 边缘函数执行
- 数据库连接池
- KV缓存策略
- 压缩传输

## 🐛 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查D1数据库ID配置
   - 确认数据库已正确初始化

2. **KV存储错误**
   - 验证KV命名空间ID
   - 检查权限配置

3. **函数执行超时**
   - 优化数据库查询
   - 检查网络连接

4. **认证失败**
   - 检查会话配置
   - 验证密码哈希

### 调试方法

#### 查看日志
```bash
wrangler pages deployment tail
```

#### 本地调试
```bash
wrangler pages dev public --local
```

#### 数据库查询
```bash
wrangler d1 execute points-management-db --command="SELECT * FROM users LIMIT 5;"
```

## 📈 监控和分析

Cloudflare提供以下监控功能：
- 请求分析
- 错误率监控
- 性能指标
- 用户地理分布
- 缓存命中率

## 🔄 数据迁移

从Flask版本迁移数据：

1. 导出Flask版本的CSV数据
2. 使用D1的批量插入API导入数据
3. 验证数据完整性

## 📝 维护说明

### 定期任务
- 清理过期会话
- 备份数据库
- 更新依赖
- 监控性能

### 更新部署
```bash
# 更新函数
wrangler pages deploy public

# 更新数据库结构
wrangler d1 execute points-management-db --file=./schema.sql
```

## 🆘 支持

如遇问题，请检查：
1. Cloudflare Dashboard的错误日志
2. 浏览器开发者工具
3. 网络连接状态
4. 配置文件正确性

---

**注意**: 这是从Flask应用自动转换的Cloudflare Pages版本，某些功能可能需要根据实际需求进行调整。
