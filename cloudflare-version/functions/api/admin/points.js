
export async function onRequestGet(context) {
    const { request, env } = context;
    
    try {
        // 验证管理员权限
        const session = await getSession(request, env);
        if (!session || session.role !== 'admin') {
            return new Response(JSON.stringify({ error: '权限不足' }), {
                status: 403,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 获取积分数据
        const stmt = env.DB.prepare(`
            SELECT user_id, user_name, total_points, valid_days, last_updated
            FROM user_points 
            ORDER BY total_points DESC
            LIMIT 100
        `);
        
        const results = await stmt.all();
        
        return new Response(JSON.stringify({
            success: true,
            data: results.results || []
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({ error: '获取数据失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function getSession(request, env) {
    const cookie = request.headers.get('Cookie');
    if (!cookie) return null;
    
    const sessionMatch = cookie.match(/session=([^;]+)/);
    if (!sessionMatch) return null;
    
    const sessionData = await env.SESSIONS.get(sessionMatch[1]);
    return sessionData ? JSON.parse(sessionData) : null;
}
