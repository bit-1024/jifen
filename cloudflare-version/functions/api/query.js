
export async function onRequestPost(context) {
    const { request, env } = context;
    
    try {
        const formData = await request.formData();
        const userId = formData.get('user_id');
        
        if (!userId) {
            return new Response(JSON.stringify({ error: '用户ID不能为空' }), {
                status: 400,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 查询D1数据库
        const stmt = env.DB.prepare('SELECT * FROM user_points WHERE user_id = ?');
        const result = await stmt.bind(userId).first();
        
        if (!result) {
            return new Response(JSON.stringify({ error: '未找到用户数据' }), {
                status: 404,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        return new Response(JSON.stringify({
            success: true,
            data: result
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({ error: '查询失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}
