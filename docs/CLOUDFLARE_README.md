# 积分管理系统 - Cloudflare Pages版本

🚀 **现代化无服务器部署版本**

基于Cloudflare Pages + D1 + Workers的全新架构，提供更好的性能、可扩展性和用户体验。

## ✨ Cloudflare版本特性

### 🌍 全球化部署
- **全球CDN**: 静态资源在全球200+数据中心缓存
- **边缘计算**: API在离用户最近的边缘节点执行
- **低延迟**: 平均响应时间 < 50ms

### ⚡ 性能优势
- **无冷启动**: Workers保持热启动状态
- **自动扩缩容**: 根据流量自动调整资源
- **高并发**: 支持数万并发请求

### 💰 成本效益
- **按需付费**: 只为实际使用的资源付费
- **免费额度**: 
  - 100,000 请求/天 (Workers)
  - 5GB 存储 (D1)
  - 1GB 带宽/月 (Pages)

## 🏗️ 技术架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   用户浏览器     │    │  Cloudflare CDN  │    │  Cloudflare     │
│                │────▶│                  │────▶│  Workers        │
│  静态HTML/JS    │    │  全球边缘节点     │    │  API Functions  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Cloudflare KV  │    │  Cloudflare D1  │
                       │  会话存储        │    │  SQLite数据库    │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 快速部署

### 前置要求
- Cloudflare账户
- Node.js 18+
- Git

### 一键部署
```bash
# 1. 克隆项目
git clone <your-repo-url>
cd points-management-system

# 2. 安装依赖
npm install

# 3. 登录Cloudflare
npx wrangler login

# 4. 创建资源
npm run setup

# 5. 部署应用
npm run deploy
```

### 详细部署步骤

#### 第一步：创建Cloudflare资源
```bash
# 创建D1数据库
npx wrangler d1 create points-management-db

# 创建KV命名空间
npx wrangler kv:namespace create "SESSIONS"
npx wrangler kv:namespace create "SESSIONS" --preview
```

#### 第二步：配置wrangler.toml
将创建资源时返回的ID填入配置文件：
```toml
[[d1_databases]]
binding = "DB"
database_name = "points-management-db"
database_id = "your-database-id-here"  # 填入实际ID

[[kv_namespaces]]
binding = "SESSIONS"
id = "your-kv-id-here"                 # 填入实际ID
preview_id = "your-preview-kv-id-here" # 填入实际预览ID
```

#### 第三步：初始化数据库
```bash
npx wrangler d1 execute points-management-db --file=./schema.sql
```

#### 第四步：部署应用
```bash
npm run deploy
```

## 📁 项目结构

```
cloudflare-version/
├── functions/                      # Cloudflare Workers Functions
│   └── api/
│       └── [[path]].js            # 统一API路由处理器
├── dist/                          # 静态前端文件
│   ├── index.html                 # 主页
│   ├── login.html                 # 登录页
│   ├── register.html              # 注册页
│   ├── upload.html                # 上传页
│   ├── points.html                # 积分管理页
│   ├── query.html                 # 查询页
│   └── js/
│       ├── auth.js                # 认证逻辑
│       ├── upload.js              # 上传逻辑
│       ├── points.js              # 积分管理
│       └── query.js               # 查询逻辑
├── schema.sql                     # D1数据库结构
├── wrangler.toml                  # Cloudflare配置
├── package.json                   # 项目配置
└── .github/workflows/             # CI/CD配置
    └── deploy.yml                 # 自动部署工作流
```

## 🔧 开发指南

### 本地开发
```bash
# 启动本地开发服务器
npm run dev

# 访问本地应用
open http://localhost:8788
```

### 环境配置
```bash
# 生产环境
npm run deploy

# 预览环境
npm run deploy:preview
```

### 数据库操作
```bash
# 查看数据库信息
npx wrangler d1 info points-management-db

# 执行SQL查询
npx wrangler d1 execute points-management-db --command="SELECT * FROM users"

# 导入数据
npx wrangler d1 execute points-management-db --file=./data.sql
```

## 🔒 安全配置

### 环境变量
在Cloudflare Pages设置中配置：
- `JWT_SECRET`: JWT签名密钥
- `ADMIN_EMAIL`: 管理员邮箱
- `MAX_FILE_SIZE`: 最大文件大小

### CORS配置
已在Functions中预配置CORS头，支持跨域请求。

### 认证机制
- JWT Token认证
- KV存储会话
- 自动过期清理

## 📊 API文档

### 认证接口
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/logout` - 用户登出

### 数据接口
- `POST /api/upload/file` - 文件上传
- `GET /api/points/list` - 积分列表
- `POST /api/points/calculate` - 积分计算
- `GET /api/query/user` - 用户查询

### 响应格式
```json
{
  "success": true,
  "message": "操作成功",
  "data": {...}
}
```

## 📈 监控和分析

### Cloudflare Analytics
- 访问量统计
- 性能指标
- 错误率监控
- 地理分布

### Workers Analytics
- Function调用统计
- 执行时间分析
- 内存使用情况
- 错误日志

### D1 Analytics
- 数据库查询统计
- 存储使用量
- 连接数监控

## 🔄 CI/CD流程

### GitHub Actions
自动化部署流程：
1. 代码推送到main分支
2. 自动运行测试
3. 构建静态资源
4. 部署到Cloudflare Pages
5. 更新数据库结构（如需要）

### 部署环境
- **Production**: 生产环境，main分支自动部署
- **Preview**: 预览环境，PR自动创建预览

## 🆘 故障排除

### 常见问题

1. **部署失败**
   ```bash
   # 检查配置
   npx wrangler pages project list
   
   # 查看部署日志
   npx wrangler pages deployment tail
   ```

2. **数据库连接失败**
   ```bash
   # 验证数据库
   npx wrangler d1 info points-management-db
   
   # 测试连接
   npx wrangler d1 execute points-management-db --command="SELECT 1"
   ```

3. **API调用失败**
   - 检查CORS配置
   - 验证路由设置
   - 查看Function日志

### 调试技巧
- 使用`console.log`输出调试信息
- 利用Cloudflare Dashboard查看实时日志
- 使用本地开发环境测试
- 检查网络请求和响应

## 📞 技术支持

- 📖 [Cloudflare Pages文档](https://developers.cloudflare.com/pages/)
- 📖 [Cloudflare D1文档](https://developers.cloudflare.com/d1/)
- 📖 [Cloudflare Workers文档](https://developers.cloudflare.com/workers/)
- 🐛 [项目Issues](https://github.com/your-repo/issues)

## 📄 许可证

MIT License - 详见 [LICENSE](./LICENSE) 文件

---

**🎉 享受现代化的无服务器积分管理体验！**
