#!/usr/bin/env node

/**
 * Cloudflare Pages 项目设置脚本
 * 自动配置数据库ID和KV命名空间ID
 */

const fs = require('fs');
const { execSync } = require('child_process');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

async function main() {
    console.log('🚀 Cloudflare Pages 项目设置');
    console.log('================================');
    
    try {
        // 检查wrangler是否已安装
        try {
            execSync('wrangler --version', { stdio: 'ignore' });
        } catch (error) {
            console.log('❌ Wrangler CLI 未安装');
            console.log('请运行: npm install -g wrangler');
            process.exit(1);
        }
        
        // 检查是否已登录
        try {
            execSync('wrangler whoami', { stdio: 'ignore' });
            console.log('✅ 已登录Cloudflare');
        } catch (error) {
            console.log('⚠️  未登录Cloudflare，请先运行: wrangler login');
            process.exit(1);
        }
        
        // 读取当前配置
        let wranglerConfig = fs.readFileSync('wrangler.toml', 'utf8');
        
        // 获取D1数据库列表
        console.log('\n🗄️  获取D1数据库信息...');
        let databases;
        try {
            const dbOutput = execSync('wrangler d1 list --json', { encoding: 'utf8' });
            databases = JSON.parse(dbOutput);
        } catch (error) {
            console.log('❌ 获取数据库列表失败');
            databases = [];
        }
        
        // 查找或创建数据库
        let targetDb = databases.find(db => db.name === 'points-management-db');
        
        if (!targetDb) {
            console.log('📝 创建新的D1数据库...');
            const createOutput = execSync('wrangler d1 create points-management-db --json', { encoding: 'utf8' });
            targetDb = JSON.parse(createOutput);
            console.log('✅ 数据库创建完成');
        } else {
            console.log('✅ 找到现有数据库');
        }
        
        // 更新数据库ID
        wranglerConfig = wranglerConfig.replace(
            /database_id = "your-database-id-here"/,
            `database_id = "${targetDb.uuid}"`
        );
        
        console.log(`📋 数据库ID: ${targetDb.uuid}`);
        
        // 获取KV命名空间列表
        console.log('\n🗂️  获取KV命名空间信息...');
        let namespaces;
        try {
            const kvOutput = execSync('wrangler kv:namespace list --json', { encoding: 'utf8' });
            namespaces = JSON.parse(kvOutput);
        } catch (error) {
            console.log('❌ 获取KV命名空间列表失败');
            namespaces = [];
        }
        
        // 查找或创建SESSIONS命名空间
        let sessionsNs = namespaces.find(ns => ns.title === 'SESSIONS');
        if (!sessionsNs) {
            console.log('📝 创建SESSIONS命名空间...');
            const createOutput = execSync('wrangler kv:namespace create "SESSIONS" --json', { encoding: 'utf8' });
            sessionsNs = JSON.parse(createOutput);
            
            // 创建预览命名空间
            const previewOutput = execSync('wrangler kv:namespace create "SESSIONS" --preview --json', { encoding: 'utf8' });
            sessionsNs.preview_id = JSON.parse(previewOutput).id;
            
            console.log('✅ SESSIONS命名空间创建完成');
        } else {
            console.log('✅ 找到现有SESSIONS命名空间');
        }
        
        // 查找或创建CACHE命名空间
        let cacheNs = namespaces.find(ns => ns.title === 'CACHE');
        if (!cacheNs) {
            console.log('📝 创建CACHE命名空间...');
            const createOutput = execSync('wrangler kv:namespace create "CACHE" --json', { encoding: 'utf8' });
            cacheNs = JSON.parse(createOutput);
            
            // 创建预览命名空间
            const previewOutput = execSync('wrangler kv:namespace create "CACHE" --preview --json', { encoding: 'utf8' });
            cacheNs.preview_id = JSON.parse(previewOutput).id;
            
            console.log('✅ CACHE命名空间创建完成');
        } else {
            console.log('✅ 找到现有CACHE命名空间');
        }
        
        // 更新KV命名空间ID
        wranglerConfig = wranglerConfig.replace(
            /id = "your-kv-namespace-id-here"/g,
            `id = "${sessionsNs.id}"`
        );
        
        wranglerConfig = wranglerConfig.replace(
            /preview_id = "your-preview-kv-namespace-id-here"/g,
            `preview_id = "${sessionsNs.preview_id || sessionsNs.id}"`
        );
        
        wranglerConfig = wranglerConfig.replace(
            /id = "your-cache-kv-namespace-id-here"/g,
            `id = "${cacheNs.id}"`
        );
        
        wranglerConfig = wranglerConfig.replace(
            /preview_id = "your-cache-preview-kv-namespace-id-here"/g,
            `preview_id = "${cacheNs.preview_id || cacheNs.id}"`
        );
        
        console.log(`📋 SESSIONS命名空间ID: ${sessionsNs.id}`);
        console.log(`📋 CACHE命名空间ID: ${cacheNs.id}`);
        
        // 写入更新的配置
        fs.writeFileSync('wrangler.toml', wranglerConfig);
        console.log('✅ wrangler.toml 配置已更新');
        
        // 初始化数据库
        console.log('\n🏗️  初始化数据库结构...');
        try {
            execSync(`wrangler d1 execute ${targetDb.name} --file=./schema.sql`, { stdio: 'inherit' });
            console.log('✅ 数据库结构初始化完成');
        } catch (error) {
            console.log('❌ 数据库初始化失败');
            console.log('请手动运行: wrangler d1 execute points-management-db --file=./schema.sql');
        }
        
        // 询问是否立即部署
        const shouldDeploy = await question('\n🚀 是否立即部署到Cloudflare Pages? (y/N): ');
        
        if (shouldDeploy.toLowerCase() === 'y') {
            console.log('📦 开始部署...');
            try {
                execSync('wrangler pages deploy public --project-name=points-management-system', { stdio: 'inherit' });
                console.log('✅ 部署完成');
                console.log('🌐 访问地址: https://points-management-system.pages.dev');
            } catch (error) {
                console.log('❌ 部署失败');
                console.log('请手动运行: npm run deploy');
            }
        }
        
        // 显示完成信息
        console.log('\n🎉 设置完成！');
        console.log('\n📋 项目信息:');
        console.log(`• 数据库: ${targetDb.name} (${targetDb.uuid})`);
        console.log(`• SESSIONS KV: ${sessionsNs.id}`);
        console.log(`• CACHE KV: ${cacheNs.id}`);
        console.log('\n📚 可用命令:');
        console.log('• npm run dev     - 本地开发');
        console.log('• npm run deploy  - 部署到生产环境');
        console.log('• npm run db:init - 初始化数据库');
        console.log('• npm run logs    - 查看部署日志');
        
        console.log('\n🔑 默认管理员账户:');
        console.log('• 用户名: admin');
        console.log('• 密码: admin123');
        
        console.log('\n⚠️  重要提醒:');
        console.log('• 请及时修改默认管理员密码');
        console.log('• 在Cloudflare Dashboard中配置环境变量');
        console.log('• 定期备份数据库数据');
        
    } catch (error) {
        console.error('❌ 设置过程中出现错误:', error.message);
        process.exit(1);
    } finally {
        rl.close();
    }
}

// 运行主函数
main().catch(error => {
    console.error('❌ 未处理的错误:', error);
    process.exit(1);
});
