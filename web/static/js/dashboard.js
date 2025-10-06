let socket = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

function initializeSocket() {
    if (typeof io === 'undefined') {
        console.warn('Socket.IO not loaded');
        return;
    }

    socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionDelayMax: 5000,
        reconnectionAttempts: maxReconnectAttempts
    });

    socket.on('connect', () => {
        console.log('Socket.IO connected');
        reconnectAttempts = 0;
        updateConnectionStatus(true);
    });

    socket.on('disconnect', () => {
        console.log('Socket.IO disconnected');
        updateConnectionStatus(false);
    });

    socket.on('connect_error', (error) => {
        console.error('Socket.IO connection error:', error);
        reconnectAttempts++;

        if (reconnectAttempts >= maxReconnectAttempts) {
            console.error('Max reconnection attempts reached');
            updateConnectionStatus(false);
        }
    });

    socket.on('pong', (data) => {
        console.log('Received pong:', data);
    });

    socket.on('guild_update', (data) => {
        console.log('Guild updated:', data);
        handleGuildUpdate(data);
    });

    socket.on('stats_update', (data) => {
        console.log('Stats updated:', data);
        updateStats(data);
    });
}

function updateConnectionStatus(connected) {
    const statusIndicator = document.getElementById('connection-status');
    if (statusIndicator) {
        statusIndicator.className = connected ? 'status-online' : 'status-offline';
        statusIndicator.textContent = connected ? 'Connected' : 'Disconnected';
    }
}

function handleGuildUpdate(data) {
    if (window.location.pathname.includes('/dashboard/') && data.guild_id) {
        const currentGuildId = window.location.pathname.split('/').pop();
        if (currentGuildId === data.guild_id) {
            showToast('Guild settings updated', 'info');
        }
    }
}

function updateStats(data) {
    const statsElements = {
        guilds: document.getElementById('stat-guilds'),
        users: document.getElementById('stat-users'),
        latency: document.getElementById('stat-latency'),
        status: document.getElementById('stat-status')
    };

    if (statsElements.guilds && data.guilds !== undefined) {
        statsElements.guilds.textContent = data.guilds;
    }

    if (statsElements.users && data.users !== undefined) {
        statsElements.users.textContent = data.users.toLocaleString();
    }

    if (statsElements.latency && data.latency !== undefined) {
        statsElements.latency.textContent = data.latency;
    }

    if (statsElements.status && data.status !== undefined) {
        statsElements.status.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
        statsElements.status.className = 'stat-value status-' + data.status;
    }
}

function sendPing() {
    if (socket && socket.connected) {
        socket.emit('ping', { timestamp: Date.now() });
    }
}

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    if (!toast) return;

    toast.textContent = message;
    toast.className = `toast toast-${type} show`;

    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

async function makeRequest(url, method = 'GET', data = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };

    if (data && (method === 'POST' || method === 'PATCH' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        const result = await response.json();

        if (!response.ok) {
            throw new Error(result.detail || 'Request failed');
        }

        return result;
    } catch (error) {
        console.error('Request error:', error);
        throw error;
    }
}

async function loadGuildData(guildId) {
    try {
        const data = await makeRequest(`/api/guilds/${guildId}`);
        return data;
    } catch (error) {
        showToast('Failed to load guild data', 'error');
        return null;
    }
}

async function loadGuildStats(guildId) {
    try {
        const stats = await makeRequest(`/api/guilds/${guildId}/stats`);
        return stats;
    } catch (error) {
        showToast('Failed to load guild stats', 'error');
        return null;
    }
}

async function loadGuildMembers(guildId, limit = 50, offset = 0) {
    try {
        const members = await makeRequest(`/api/guilds/${guildId}/members?limit=${limit}&offset=${offset}`);
        return members;
    } catch (error) {
        showToast('Failed to load guild members', 'error');
        return null;
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

function formatDate(date) {
    const d = new Date(date);
    return d.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('Copied to clipboard!', 'success');
        }).catch(err => {
            console.error('Failed to copy:', err);
            showToast('Failed to copy', 'error');
        });
    } else {
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            showToast('Copied to clipboard!', 'success');
        } catch (err) {
            console.error('Failed to copy:', err);
            showToast('Failed to copy', 'error');
        }

        document.body.removeChild(textArea);
    }
}

function validateChannelId(id) {
    return /^\d{17,19}$/.test(id);
}

function validateRoleId(id) {
    return /^\d{17,19}$/.test(id);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function parseDiscordMentions(text) {
    return text
        .replace(/<@!?(\d+)>/g, '@User')
        .replace(/<@&(\d+)>/g, '@Role')
        .replace(/<#(\d+)>/g, '#channel');
}

document.addEventListener('DOMContentLoaded', () => {
    initializeSocket();

    const pingInterval = setInterval(sendPing, 30000);

    window.addEventListener('beforeunload', () => {
        clearInterval(pingInterval);
        if (socket) {
            socket.disconnect();
        }
    });

    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', () => {
            const text = button.getAttribute('data-copy');
            copyToClipboard(text);
        });
    });

    const channelInputs = document.querySelectorAll('input[id*="channel"]');
    channelInputs.forEach(input => {
        input.addEventListener('blur', () => {
            const value = input.value.trim();
            if (value && !validateChannelId(value)) {
                showToast('Invalid channel ID format', 'warning');
            }
        });
    });

    const roleInputs = document.querySelectorAll('input[id*="role"]');
    roleInputs.forEach(input => {
        input.addEventListener('blur', () => {
            const value = input.value.trim();
            if (value && !validateRoleId(value)) {
                showToast('Invalid role ID format', 'warning');
            }
        });
    });
});