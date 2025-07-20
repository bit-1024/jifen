#!/bin/bash

# Cloudflare Pages 部署脚本
# 自动化部署积分查询系统到Cloudflare Pages

set -e

echo "🚀 开始部署积分查询系统到Cloudflare Pages..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查依赖
check_dependencies() {
    echo -e "${BLUE}🔍 检查依赖...${NC}"
    
    if ! command -v wrangler &> /dev/null; then
        echo -e "${RED}❌ Wrangler CLI 未安装${NC}"
        echo "请运行: npm install -g wrangler"
        exit 1
    fi
    
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js 未安装${NC}"
        echo "请安装 Node.js: https://nodejs.org/"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖检查完成${NC}"
}

# 检查登录状态
check_login() {
    echo -e "${BLUE}🔐 检查Cloudflare登录状态...${NC}"
    
    if ! wrangler whoami &> /dev/null; then
        echo -e "${YELLOW}⚠️  未登录Cloudflare${NC}"
        echo "正在启动登录流程..."
        wrangler login
    else
        echo -e "${GREEN}✅ 已登录Cloudflare${NC}"
    fi
}

# 创建D1数据库
create_database() {
    echo -e "${BLUE}🗄️  创建D1数据库...${NC}"
    
    # 检查数据库是否已存在
    if wrangler d1 list | grep -q "points-management-db"; then
        echo -e "${YELLOW}⚠️  数据库已存在，跳过创建${NC}"
    else
        echo "创建新的D1数据库..."
        wrangler d1 create points-management-db
        echo -e "${GREEN}✅ 数据库创建完成${NC}"
        echo -e "${YELLOW}📝 请更新wrangler.toml中的database_id${NC}"
    fi
}

# 创建KV命名空间
create_kv_namespaces() {
    echo -e "${BLUE}🗂️  创建KV命名空间...${NC}"
    
    # 创建SESSIONS命名空间
    if wrangler kv:namespace list | grep -q "SESSIONS"; then
        echo -e "${YELLOW}⚠️  SESSIONS命名空间已存在${NC}"
    else
        echo "创建SESSIONS命名空间..."
        wrangler kv:namespace create "SESSIONS"
        wrangler kv:namespace create "SESSIONS" --preview
    fi
    
    # 创建CACHE命名空间
    if wrangler kv:namespace list | grep -q "CACHE"; then
        echo -e "${YELLOW}⚠️  CACHE命名空间已存在${NC}"
    else
        echo "创建CACHE命名空间..."
        wrangler kv:namespace create "CACHE"
        wrangler kv:namespace create "CACHE" --preview
    fi
    
    echo -e "${GREEN}✅ KV命名空间创建完成${NC}"
    echo -e "${YELLOW}📝 请更新wrangler.toml中的KV命名空间ID${NC}"
}

# 初始化数据库
init_database() {
    echo -e "${BLUE}🏗️  初始化数据库结构...${NC}"
    
    if [ -f "schema.sql" ]; then
        wrangler d1 execute points-management-db --file=./schema.sql
        echo -e "${GREEN}✅ 数据库结构初始化完成${NC}"
    else
        echo -e "${RED}❌ schema.sql文件不存在${NC}"
        exit 1
    fi
}

# 验证配置
validate_config() {
    echo -e "${BLUE}🔧 验证配置文件...${NC}"
    
    if [ ! -f "wrangler.toml" ]; then
        echo -e "${RED}❌ wrangler.toml文件不存在${NC}"
        exit 1
    fi
    
    # 检查必要的配置项
    if grep -q "your-database-id-here" wrangler.toml; then
        echo -e "${YELLOW}⚠️  请更新wrangler.toml中的database_id${NC}"
        echo "1. 运行: wrangler d1 list"
        echo "2. 复制数据库ID到wrangler.toml"
        read -p "配置完成后按Enter继续..."
    fi
    
    if grep -q "your-kv-namespace-id-here" wrangler.toml; then
        echo -e "${YELLOW}⚠️  请更新wrangler.toml中的KV命名空间ID${NC}"
        echo "1. 运行: wrangler kv:namespace list"
        echo "2. 复制命名空间ID到wrangler.toml"
        read -p "配置完成后按Enter继续..."
    fi
    
    echo -e "${GREEN}✅ 配置验证完成${NC}"
}

# 本地测试
local_test() {
    echo -e "${BLUE}🧪 启动本地测试...${NC}"
    
    read -p "是否启动本地开发服务器进行测试? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "启动本地服务器..."
        echo "访问 http://localhost:8788 进行测试"
        echo "按 Ctrl+C 停止服务器并继续部署"
        wrangler pages dev public --compatibility-date=2024-01-15
    fi
}

# 部署到Cloudflare Pages
deploy_pages() {
    echo -e "${BLUE}🚀 部署到Cloudflare Pages...${NC}"
    
    # 检查public目录
    if [ ! -d "public" ]; then
        echo -e "${RED}❌ public目录不存在${NC}"
        exit 1
    fi
    
    # 部署
    wrangler pages deploy public --project-name=points-management-system
    
    echo -e "${GREEN}✅ 部署完成${NC}"
}

# 验证部署
verify_deployment() {
    echo -e "${BLUE}🔍 验证部署...${NC}"
    
    # 测试数据库连接
    echo "测试数据库连接..."
    if wrangler d1 execute points-management-db --command="SELECT COUNT(*) FROM users;"; then
        echo -e "${GREEN}✅ 数据库连接正常${NC}"
    else
        echo -e "${RED}❌ 数据库连接失败${NC}"
    fi
    
    echo -e "${GREEN}🎉 部署验证完成${NC}"
}

# 显示部署信息
show_deployment_info() {
    echo -e "${GREEN}🎊 部署成功！${NC}"
    echo
    echo -e "${BLUE}📋 部署信息:${NC}"
    echo "• 项目名称: points-management-system"
    echo "• 访问地址: https://points-management-system.pages.dev"
    echo "• 管理面板: https://dash.cloudflare.com/pages"
    echo
    echo -e "${BLUE}🔑 默认管理员账户:${NC}"
    echo "• 用户名: admin"
    echo "• 密码: admin123"
    echo
    echo -e "${BLUE}📚 后续步骤:${NC}"
    echo "1. 访问网站验证功能"
    echo "2. 上传积分数据"
    echo "3. 配置自定义域名（可选）"
    echo "4. 设置环境变量"
    echo "5. 配置监控和告警"
    echo
    echo -e "${YELLOW}⚠️  重要提醒:${NC}"
    echo "• 请及时修改默认管理员密码"
    echo "• 定期备份数据库数据"
    echo "• 监控应用性能和错误"
}

# 主函数
main() {
    echo -e "${GREEN}🎯 Cloudflare Pages 部署脚本${NC}"
    echo "========================================"
    
    # 执行部署步骤
    check_dependencies
    check_login
    create_database
    create_kv_namespaces
    validate_config
    init_database
    local_test
    deploy_pages
    verify_deployment
    show_deployment_info
    
    echo
    echo -e "${GREEN}✨ 部署流程完成！${NC}"
}

# 错误处理
trap 'echo -e "${RED}❌ 部署过程中出现错误${NC}"; exit 1' ERR

# 运行主函数
main "$@"
