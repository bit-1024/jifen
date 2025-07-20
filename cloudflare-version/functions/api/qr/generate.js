
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
        
        const { url, expiry } = await request.json();
        
        // 生成二维码（这里需要使用适合Cloudflare Workers的二维码库）
        const qrCodeData = await generateQRCode(url);
        
        // 存储二维码信息
        const qrId = generateId();
        await env.SESSIONS.put(`qr_${qrId}`, JSON.stringify({
            url,
            expiry,
            created: Date.now()
        }), { expirationTtl: expiry || 86400 });
        
        return new Response(JSON.stringify({
            success: true,
            qrId,
            qrData: qrCodeData
        }), {
            headers: { 'Content-Type': 'application/json' }
        });
        
    } catch (error) {
        return new Response(JSON.stringify({ error: '生成二维码失败' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

async function generateQRCode(text) {
    // 简化的二维码生成，实际应用中需要使用专门的库
    return `data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" width="200" height="200"><text x="100" y="100" text-anchor="middle">QR: ${text}</text></svg>`;
}

function generateId() {
    return Math.random().toString(36).substr(2, 9);
}

async function getSession(request, env) {
    const cookie = request.headers.get('Cookie');
    if (!cookie) return null;
    
    const sessionMatch = cookie.match(/session=([^;]+)/);
    if (!sessionMatch) return null;
    
    const sessionData = await env.SESSIONS.get(sessionMatch[1]);
    return sessionData ? JSON.parse(sessionData) : null;
}
