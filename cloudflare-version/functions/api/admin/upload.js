
export async function onRequestPost(context) {
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
        
        const formData = await request.formData();
        const file = formData.get('file');
        
        if (!file) {
            return new Response(JSON.stringify({ error: '请选择文件' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 处理Excel文件
        const arrayBuffer = await file.arrayBuffer();
        const processedData = await processExcelFile(arrayBuffer);
        
        // 批量插入数据
        const stmt = env.DB.prepare(`
            INSERT OR REPLACE INTO user_points 
            (user_id, user_name, total_points, valid_days, last_updated)
            VALUES (?, ?, ?, ?, datetime('now'))
        `);
        
        for (const row of processedData) {
            await stmt.bind(row.userId, row.userName, row.points, row.validDays).run();
        }
        
        return new Response(JSON.stringify({
            success: true,
            message: `成功处理 ${processedData.length} 条记录`
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({ error: '文件处理失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function processExcelFile(arrayBuffer) {
    // 这里需要实现Excel文件解析逻辑
    // 由于Cloudflare Workers环境限制，可能需要使用轻量级的CSV解析
    return [];
}

async function getSession(request, env) {
    const cookie = request.headers.get('Cookie');
    if (!cookie) return null;
    
    const sessionMatch = cookie.match(/session=([^;]+)/);
    if (!sessionMatch) return null;
    
    const sessionData = await env.SESSIONS.get(sessionMatch[1]);
    return sessionData ? JSON.parse(sessionData) : null;
}
