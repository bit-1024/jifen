@echo off
setlocal enabledelayedexpansion

REM Cloudflare Pages 部署脚本 (Windows版本)
REM 自动化部署积分查询系统到Cloudflare Pages

echo 🚀 开始部署积分查询系统到Cloudflare Pages...
echo.

REM 检查依赖
echo 🔍 检查依赖...
where wrangler >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Wrangler CLI 未安装
    echo 请运行: npm install -g wrangler
    pause
    exit /b 1
)

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js 未安装
    echo 请安装 Node.js: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ 依赖检查完成
echo.

REM 检查登录状态
echo 🔐 检查Cloudflare登录状态...
wrangler whoami >nul 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  未登录Cloudflare
    echo 正在启动登录流程...
    wrangler login
) else (
    echo ✅ 已登录Cloudflare
)
echo.

REM 创建D1数据库
echo 🗄️  创建D1数据库...
wrangler d1 list | findstr "points-management-db" >nul 2>nul
if %errorlevel% neq 0 (
    echo 创建新的D1数据库...
    wrangler d1 create points-management-db
    echo ✅ 数据库创建完成
    echo 📝 请更新wrangler.toml中的database_id
) else (
    echo ⚠️  数据库已存在，跳过创建
)
echo.

REM 创建KV命名空间
echo 🗂️  创建KV命名空间...
wrangler kv:namespace list | findstr "SESSIONS" >nul 2>nul
if %errorlevel% neq 0 (
    echo 创建SESSIONS命名空间...
    wrangler kv:namespace create "SESSIONS"
    wrangler kv:namespace create "SESSIONS" --preview
)

wrangler kv:namespace list | findstr "CACHE" >nul 2>nul
if %errorlevel% neq 0 (
    echo 创建CACHE命名空间...
    wrangler kv:namespace create "CACHE"
    wrangler kv:namespace create "CACHE" --preview
)

echo ✅ KV命名空间创建完成
echo 📝 请更新wrangler.toml中的KV命名空间ID
echo.

REM 验证配置
echo 🔧 验证配置文件...
if not exist "wrangler.toml" (
    echo ❌ wrangler.toml文件不存在
    pause
    exit /b 1
)

findstr "your-database-id-here" wrangler.toml >nul 2>nul
if %errorlevel% equ 0 (
    echo ⚠️  请更新wrangler.toml中的database_id
    echo 1. 运行: wrangler d1 list
    echo 2. 复制数据库ID到wrangler.toml
    pause
)

findstr "your-kv-namespace-id-here" wrangler.toml >nul 2>nul
if %errorlevel% equ 0 (
    echo ⚠️  请更新wrangler.toml中的KV命名空间ID
    echo 1. 运行: wrangler kv:namespace list
    echo 2. 复制命名空间ID到wrangler.toml
    pause
)

echo ✅ 配置验证完成
echo.

REM 初始化数据库
echo 🏗️  初始化数据库结构...
if exist "schema.sql" (
    wrangler d1 execute points-management-db --file=./schema.sql
    echo ✅ 数据库结构初始化完成
) else (
    echo ❌ schema.sql文件不存在
    pause
    exit /b 1
)
echo.

REM 本地测试
echo 🧪 本地测试选项...
set /p test_choice="是否启动本地开发服务器进行测试? (y/N): "
if /i "!test_choice!"=="y" (
    echo 启动本地服务器...
    echo 访问 http://localhost:8788 进行测试
    echo 按 Ctrl+C 停止服务器并继续部署
    wrangler pages dev public --compatibility-date=2024-01-15
)
echo.

REM 部署到Cloudflare Pages
echo 🚀 部署到Cloudflare Pages...
if not exist "public" (
    echo ❌ public目录不存在
    pause
    exit /b 1
)

wrangler pages deploy public --project-name=points-management-system
echo ✅ 部署完成
echo.

REM 验证部署
echo 🔍 验证部署...
echo 测试数据库连接...
wrangler d1 execute points-management-db --command="SELECT COUNT(*) FROM users;"
if %errorlevel% equ 0 (
    echo ✅ 数据库连接正常
) else (
    echo ❌ 数据库连接失败
)
echo ✅ 部署验证完成
echo.

REM 显示部署信息
echo 🎊 部署成功！
echo.
echo 📋 部署信息:
echo • 项目名称: points-management-system
echo • 访问地址: https://points-management-system.pages.dev
echo • 管理面板: https://dash.cloudflare.com/pages
echo.
echo 🔑 默认管理员账户:
echo • 用户名: admin
echo • 密码: admin123
echo.
echo 📚 后续步骤:
echo 1. 访问网站验证功能
echo 2. 上传积分数据
echo 3. 配置自定义域名（可选）
echo 4. 设置环境变量
echo 5. 配置监控和告警
echo.
echo ⚠️  重要提醒:
echo • 请及时修改默认管理员密码
echo • 定期备份数据库数据
echo • 监控应用性能和错误
echo.
echo ✨ 部署流程完成！

pause
