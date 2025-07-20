/**
 * 认证检查API
 * 检查用户登录状态和权限
 */

export async function onRequestGet(context) {
    const { request, env } = context;
    
    try {
        const session = await getSession(request, env);
        
        if (!session) {
            return new Response(JSON.stringify({
                authenticated: false,
                error: '未登录'
            }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        // 检查会话是否过期
        if (session.loginTime && Date.now() - session.loginTime > 86400000) { // 24小时
            return new Response(JSON.stringify({
                authenticated: false,
                error: '会话已过期'
            }), {
                status: 401,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        return new Response(JSON.stringify({
            authenticated: true,
            user: {
                id: session.userId,
                username: session.username,
                role: session.role
            }
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({
            authenticated: false,
            error: '认证检查失败'
        }), {
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
