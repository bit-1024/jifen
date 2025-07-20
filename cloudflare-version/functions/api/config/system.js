
export async function onRequestGet(context) {
    const { env } = context;
    
    try {
        const config = await env.SESSIONS.get('system_config');
        return new Response(config || '{}', {
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (error) {
        return new Response(JSON.stringify({ error: '获取配置失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

export async function onRequestPost(context) {
    const { request, env } = context;
    
    try {
        const session = await getSession(request, env);
        if (!session || session.role !== 'admin') {
            return new Response(JSON.stringify({ error: '权限不足' }), {
                status: 403,
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        const config = await request.json();
        await env.SESSIONS.put('system_config', JSON.stringify(config));
        
        return new Response(JSON.stringify({ success: true }), {
            headers: { 'Content-Type': 'application/json' }
        });
    } catch (error) {
        return new Response(JSON.stringify({ error: '保存配置失败' }), {
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
