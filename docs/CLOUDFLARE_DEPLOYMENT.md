# Cloudflare Pages 部署指南

本文档详细说明如何将积分管理系统部署到Cloudflare Pages。

## 🏗️ 架构说明

### 技术栈
- **前端**: 静态HTML/CSS/JavaScript
- **后端**: Cloudflare Workers Functions
- **数据库**: Cloudflare D1 (SQLite)
- **会话存储**: Cloudflare KV
- **部署平台**: Cloudflare Pages

### 架构优势
- ✅ 全球CDN加速
- ✅ 无服务器架构
- ✅ 自动扩缩容
- ✅ 低延迟响应
- ✅ 成本效益高

## 📋 部署前准备

### 1. 环境要求
- Node.js 18+
- npm 或 yarn
- Cloudflare 账户
- Wrangler CLI

### 2. 安装Wrangler CLI
```bash
npm install -g wrangler
```

### 3. 登录Cloudflare
```bash
wrangler login
```

## 🚀 部署步骤

### 第一步：创建D1数据库
```bash
# 创建D1数据库
wrangler d1 create points-management-db

# 记录返回的database_id，更新wrangler.toml中的database_id
```

### 第二步：创建KV命名空间
```bash
# 创建生产环境KV命名空间
wrangler kv:namespace create "SESSIONS"

# 创建预览环境KV命名空间
wrangler kv:namespace create "SESSIONS" --preview

# 记录返回的id，更新wrangler.toml中的KV配置
```

### 第三步：更新配置文件
编辑 `wrangler.toml`，填入正确的ID：

```toml
[[d1_databases]]
binding = "DB"
database_name = "points-management-db"
database_id = "your-actual-database-id"

[[kv_namespaces]]
binding = "SESSIONS"
id = "your-actual-kv-id"
preview_id = "your-actual-preview-kv-id"
```

### 第四步：初始化数据库
```bash
# 执行数据库初始化脚本
wrangler d1 execute points-management-db --file=./schema.sql
```

### 第五步：本地开发测试
```bash
# 安装依赖
npm install

# 启动本地开发服务器
npm run dev
```

访问 http://localhost:8788 测试功能

### 第六步：部署到Cloudflare Pages
```bash
# 部署到生产环境
npm run deploy
```

## 🔧 配置说明

### wrangler.toml 配置
```toml
name = "points-management-system"
compatibility_date = "2024-01-15"
pages_build_output_dir = "dist"

# D1数据库配置
[[d1_databases]]
binding = "DB"
database_name = "points-management-db"
database_id = "your-database-id"

# KV存储配置
[[kv_namespaces]]
binding = "SESSIONS"
id = "your-kv-id"
preview_id = "your-preview-kv-id"

# 环境变量
[env.production.vars]
ENVIRONMENT = "production"

[env.preview.vars]
ENVIRONMENT = "preview"
```

### 数据库结构
- **users**: 用户账户表
- **user_points**: 用户积分统计表
- **points_history**: 积分历史记录表
- **upload_history**: 上传历史记录表

### API端点
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/logout` - 用户登出
- `POST /api/upload/file` - 文件上传
- `GET /api/points/list` - 积分列表
- `GET /api/query/user` - 用户查询

## 🔒 安全配置

### 环境变量
在Cloudflare Pages设置中配置：
- `JWT_SECRET`: JWT签名密钥
- `ADMIN_EMAIL`: 管理员邮箱
- `MAX_FILE_SIZE`: 最大文件大小限制

### CORS配置
已在Functions中配置CORS头：
```javascript
const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};
```

## 📊 监控和日志

### Cloudflare Analytics
- 访问量统计
- 性能监控
- 错误率追踪

### Workers Analytics
- Function调用次数
- 执行时间
- 错误日志

### D1 Analytics
- 数据库查询统计
- 存储使用量
- 连接数监控

## 🛠️ 维护操作

### 数据库维护
```bash
# 查看数据库信息
wrangler d1 info points-management-db

# 执行SQL查询
wrangler d1 execute points-management-db --command="SELECT COUNT(*) FROM users"

# 备份数据库
wrangler d1 export points-management-db --output=backup.sql
```

### KV存储维护
```bash
# 查看KV命名空间
wrangler kv:namespace list

# 查看KV键值
wrangler kv:key list --namespace-id=your-kv-id

# 删除过期会话
wrangler kv:key delete "expired-session-key" --namespace-id=your-kv-id
```

### 日志查看
```bash
# 查看实时日志
wrangler pages deployment tail

# 查看特定部署的日志
wrangler pages deployment tail --deployment-id=your-deployment-id
```

## 🔄 CI/CD配置

### GitHub Actions示例
```yaml
name: Deploy to Cloudflare Pages

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          
      - name: Install dependencies
        run: npm install
        
      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          projectName: points-management-system
          directory: dist
```

## 📈 性能优化

### 缓存策略
- 静态资源：长期缓存
- API响应：短期缓存
- 数据库查询：适当缓存

### 代码优化
- 压缩JavaScript和CSS
- 优化图片资源
- 减少HTTP请求

### 数据库优化
- 合理使用索引
- 优化查询语句
- 定期清理过期数据

## 🆘 故障排除

### 常见问题

1. **部署失败**
   - 检查wrangler.toml配置
   - 确认D1和KV资源已创建
   - 查看部署日志

2. **数据库连接失败**
   - 确认database_id正确
   - 检查数据库是否已初始化
   - 验证SQL语法

3. **认证问题**
   - 检查KV命名空间配置
   - 确认会话存储正常
   - 验证JWT配置

4. **API调用失败**
   - 检查CORS配置
   - 确认API路由正确
   - 查看Function日志

### 调试技巧
- 使用`console.log`输出调试信息
- 利用Cloudflare Dashboard查看日志
- 使用本地开发环境测试
- 检查网络请求和响应

## 📞 技术支持

如遇到部署问题，可以：
1. 查看Cloudflare官方文档
2. 检查项目GitHub Issues
3. 联系开发团队

---

**版本**: v2.0  
**更新时间**: 2024-01-15  
**适用平台**: Cloudflare Pages
