
export async function onRequestPost(context) {
    const { request, env } = context;
    
    try {
        const formData = await request.formData();
        const username = formData.get('username');
        const password = formData.get('password');
        const email = formData.get('email');
        
        if (!username || !password || !email) {
            return new Response(JSON.stringify({ error: '所有字段都是必填的' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 检查用户是否已存在
        const existingUser = await env.DB.prepare('SELECT id FROM users WHERE username = ? OR email = ?')
            .bind(username, email).first();
        
        if (existingUser) {
            return new Response(JSON.stringify({ error: '用户名或邮箱已存在' }), {
                status: 409,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 创建新用户
        const passwordHash = hashPassword(password);
        const stmt = env.DB.prepare(`
            INSERT INTO users (username, password_hash, email, role, created_at, is_active)
            VALUES (?, ?, ?, 'user', datetime('now'), 1)
        `);
        
        await stmt.bind(username, passwordHash, email).run();
        
        return new Response(JSON.stringify({
            success: true,
            message: '注册成功',
            redirect: '/login.html'
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({ error: '注册失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

function hashPassword(password) {
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(password).digest('hex');
}
