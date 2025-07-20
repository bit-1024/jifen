
export async function onRequestPost(context) {
    const { request, env } = context;
    
    try {
        const formData = await request.formData();
        const username = formData.get('username');
        const password = formData.get('password');
        
        if (!username || !password) {
            return new Response(JSON.stringify({ error: '用户名和密码不能为空' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 验证用户
        const stmt = env.DB.prepare('SELECT * FROM users WHERE username = ?');
        const user = await stmt.bind(username).first();
        
        if (!user || !verifyPassword(password, user.password_hash)) {
            return new Response(JSON.stringify({ error: '用户名或密码错误' }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 创建会话
        const sessionId = generateSessionId();
        await env.SESSIONS.put(sessionId, JSON.stringify({
            userId: user.id,
            username: user.username,
            role: user.role,
            loginTime: Date.now()
        }), { expirationTtl: 86400 }); // 24小时过期
        
        return new Response(JSON.stringify({
            success: true,
            redirect: user.role === 'admin' ? '/admin/points.html' : '/query.html'
        }), {
            headers: { 
                'Content-Type': 'application/json',
                'Set-Cookie': `session=${sessionId}; HttpOnly; Secure; SameSite=Strict; Max-Age=86400`
            }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({ error: '登录失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

function verifyPassword(password, hash) {
    // 简单的密码验证，实际应用中应使用更安全的方法
    const crypto = require('crypto');
    return crypto.createHash('sha256').update(password).digest('hex') === hash;
}

function generateSessionId() {
    return crypto.randomBytes(32).toString('hex');
}
