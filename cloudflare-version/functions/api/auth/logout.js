/**
 * 用户注销API
 */

export async function onRequestPost(context) {
    const { request, env } = context;
    
    try {
        const cookie = request.headers.get('Cookie');
        
        if (cookie) {
            const sessionMatch = cookie.match(/session=([^;]+)/);
            if (sessionMatch) {
                // 删除服务器端会话
                await env.SESSIONS.delete(sessionMatch[1]);
            }
        }
        
        return new Response(JSON.stringify({
            success: true,
            message: '注销成功'
        }), {
            headers: { 
                'Content-Type': 'application/json',
                'Set-Cookie': 'session=; HttpOnly; Secure; SameSite=Strict; Max-Age=0; Path=/'
            }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({
            success: false,
            error: '注销失败'
        }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}
