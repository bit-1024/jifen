/**
 * Cloudflare Pages 客户端适配器
 * 处理前端与Cloudflare Functions的交互
 */

class CloudflareAdapter {
    constructor() {
        this.apiBase = '/api';
        this.init();
    }

    init() {
        // 初始化事件监听器
        this.setupFormHandlers();
        this.setupAuthCheck();
        this.setupNavigation();
    }

    // 设置表单处理器
    setupFormHandlers() {
        // 查询表单
        const queryForm = document.querySelector('form[action*="query"]');
        if (queryForm) {
            queryForm.addEventListener('submit', (e) => this.handleQuerySubmit(e));
        }

        // 登录表单
        const loginForm = document.querySelector('form[action*="login"]');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLoginSubmit(e));
        }

        // 注册表单
        const registerForm = document.querySelector('form[action*="register"]');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegisterSubmit(e));
        }

        // 管理员表单
        const adminForms = document.querySelectorAll('form[action*="admin"]');
        adminForms.forEach(form => {
            form.addEventListener('submit', (e) => this.handleAdminSubmit(e));
        });
    }

    // 设置认证检查
    setupAuthCheck() {
        // 检查需要认证的页面
        const authRequired = document.querySelector('<!-- AUTH_REQUIRED -->');
        const adminRequired = document.querySelector('<!-- ADMIN_REQUIRED -->');

        if (authRequired || adminRequired) {
            this.checkAuth(adminRequired !== null);
        }
    }

    // 设置导航
    setupNavigation() {
        // 处理导航按钮
        const navButtons = document.querySelectorAll('.nav-btn');
        navButtons.forEach(btn => {
            if (btn.href && btn.href.includes('javascript:history.back()')) {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    history.back();
                });
            }
        });
    }

    // 处理查询提交
    async handleQuerySubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        try {
            this.showLoading(true);
            const response = await fetch('/api/query', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.displayQueryResult(result.data);
            } else {
                this.showError(result.error || '查询失败');
            }
        } catch (error) {
            this.showError('网络错误，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    // 处理登录提交
    async handleLoginSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        try {
            this.showLoading(true);
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                if (result.redirect) {
                    window.location.href = result.redirect;
                } else {
                    window.location.href = '/';
                }
            } else {
                this.showError(result.error || '登录失败');
            }
        } catch (error) {
            this.showError('网络错误，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    // 处理注册提交
    async handleRegisterSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const formData = new FormData(form);

        // 验证密码
        const password = formData.get('password');
        const confirmPassword = formData.get('confirm_password');

        if (password !== confirmPassword) {
            this.showError('两次输入的密码不一致');
            return;
        }

        try {
            this.showLoading(true);
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message || '注册成功');
                setTimeout(() => {
                    window.location.href = result.redirect || '/login.html';
                }, 2000);
            } else {
                this.showError(result.error || '注册失败');
            }
        } catch (error) {
            this.showError('网络错误，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    // 处理管理员表单提交
    async handleAdminSubmit(e) {
        e.preventDefault();
        const form = e.target;
        const action = form.action;
        const formData = new FormData(form);

        try {
            this.showLoading(true);
            const response = await fetch(action, {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                this.showSuccess(result.message || '操作成功');
                // 刷新页面或更新数据
                if (result.reload) {
                    setTimeout(() => location.reload(), 1000);
                }
            } else {
                this.showError(result.error || '操作失败');
            }
        } catch (error) {
            this.showError('网络错误，请重试');
        } finally {
            this.showLoading(false);
        }
    }

    // 检查认证状态
    async checkAuth(requireAdmin = false) {
        try {
            const response = await fetch('/api/auth/check');
            const result = await response.json();

            if (!result.authenticated) {
                window.location.href = '/login.html';
                return;
            }

            if (requireAdmin && result.user.role !== 'admin') {
                this.showError('权限不足');
                setTimeout(() => {
                    window.location.href = '/';
                }, 2000);
                return;
            }

            // 更新UI显示用户信息
            this.updateUserInfo(result.user);

        } catch (error) {
            console.error('认证检查失败:', error);
            window.location.href = '/login.html';
        }
    }

    // 显示查询结果
    displayQueryResult(data) {
        // 创建结果页面内容
        const resultHtml = `
            <div class="query-result">
                <div class="result-header">
                    <h2>查询结果</h2>
                </div>
                <div class="result-content">
                    <div class="user-info">
                        <h3>用户信息</h3>
                        <p><strong>用户ID:</strong> ${data.user_id}</p>
                        <p><strong>用户姓名:</strong> ${data.user_name || '未设置'}</p>
                    </div>
                    <div class="points-info">
                        <h3>积分信息</h3>
                        <p><strong>总积分:</strong> ${data.total_points}</p>
                        <p><strong>有效天数:</strong> ${data.valid_days}</p>
                        <p><strong>最后更新:</strong> ${new Date(data.last_updated).toLocaleString()}</p>
                    </div>
                </div>
            </div>
        `;

        // 替换页面内容或跳转到结果页面
        const container = document.querySelector('.container');
        if (container) {
            container.innerHTML = resultHtml;
        }
    }

    // 更新用户信息显示
    updateUserInfo(user) {
        const userInfoElements = document.querySelectorAll('.user-info');
        userInfoElements.forEach(element => {
            element.textContent = `欢迎，${user.username}`;
        });

        // 显示/隐藏管理员功能
        const adminElements = document.querySelectorAll('.admin-only');
        adminElements.forEach(element => {
            element.style.display = user.role === 'admin' ? 'block' : 'none';
        });
    }

    // 显示加载状态
    showLoading(show) {
        let loader = document.querySelector('.loading-overlay');
        
        if (show) {
            if (!loader) {
                loader = document.createElement('div');
                loader.className = 'loading-overlay';
                loader.innerHTML = `
                    <div class="loading-spinner">
                        <div class="spinner"></div>
                        <p>处理中...</p>
                    </div>
                `;
                document.body.appendChild(loader);
            }
            loader.style.display = 'flex';
        } else {
            if (loader) {
                loader.style.display = 'none';
            }
        }
    }

    // 显示错误消息
    showError(message) {
        this.showMessage(message, 'error');
    }

    // 显示成功消息
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    // 显示消息
    showMessage(message, type = 'info') {
        // 移除现有消息
        const existingMessage = document.querySelector('.message-toast');
        if (existingMessage) {
            existingMessage.remove();
        }

        // 创建新消息
        const messageElement = document.createElement('div');
        messageElement.className = `message-toast message-${type}`;
        messageElement.innerHTML = `
            <div class="message-content">
                <span class="message-icon">${type === 'error' ? '❌' : type === 'success' ? '✅' : 'ℹ️'}</span>
                <span class="message-text">${message}</span>
                <button class="message-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;

        document.body.appendChild(messageElement);

        // 自动移除消息
        setTimeout(() => {
            if (messageElement.parentNode) {
                messageElement.remove();
            }
        }, 5000);
    }

    // 工具方法：获取Cookie
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // 工具方法：设置Cookie
    setCookie(name, value, days = 1) {
        const expires = new Date();
        expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
        document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;secure;samesite=strict`;
    }

    // 工具方法：删除Cookie
    deleteCookie(name) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
    }
}

// 初始化页面类型处理
function initCloudflarePages(pageType) {
    const adapter = new CloudflareAdapter();
    
    // 根据页面类型执行特定初始化
    switch (pageType) {
        case 'home':
            initHomePage(adapter);
            break;
        case 'query':
            initQueryPage(adapter);
            break;
        case 'auth':
            initAuthPage(adapter);
            break;
        case 'admin':
            initAdminPage(adapter);
            break;
    }
}

// 首页初始化
function initHomePage(adapter) {
    // 检查用户状态并更新UI
    adapter.checkAuth().catch(() => {
        // 未登录状态，显示登录按钮
        console.log('用户未登录');
    });
}

// 查询页面初始化
function initQueryPage(adapter) {
    // 查询页面特定初始化
    console.log('查询页面已初始化');
}

// 认证页面初始化
function initAuthPage(adapter) {
    // 检查是否已登录
    adapter.checkAuth().then(() => {
        // 已登录，重定向到首页
        window.location.href = '/';
    }).catch(() => {
        // 未登录，正常显示登录页面
        console.log('显示登录页面');
    });
}

// 管理员页面初始化
function initAdminPage(adapter) {
    // 管理员页面需要认证和权限检查
    adapter.checkAuth(true);
}

// 全局错误处理
window.addEventListener('error', function(e) {
    console.error('页面错误:', e.error);
});

// 全局未处理的Promise拒绝
window.addEventListener('unhandledrejection', function(e) {
    console.error('未处理的Promise拒绝:', e.reason);
});

// 导出适配器类供其他脚本使用
window.CloudflareAdapter = CloudflareAdapter;
