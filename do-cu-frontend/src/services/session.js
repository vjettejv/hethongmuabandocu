const KEYS = ['token', 'userId', 'userRoleId', 'username'];
export const SESSION_EVENT = 'docu-session-change';

export function tokenClaims(token) {
    try {
        const part = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/');
        return JSON.parse(atob(part));
    } catch { return null; }
}

export function getSession() {
    const token = localStorage.getItem('token');
    const claims = token ? tokenClaims(token) : null;
    const authenticated = Number.isInteger(claims?.id) && claims.id > 0 &&
        Number.isFinite(claims?.exp) && claims.exp * 1000 > Date.now();
    return {
        token: authenticated ? token : null,
        userId: authenticated ? claims.id : null,
        userRoleId: authenticated ? String(claims.roleId) : null,
        username: authenticated ? localStorage.getItem('username') || '' : '',
        expiresAt: authenticated ? claims.exp * 1000 : null,
        isAuthenticated: authenticated,
        isAdmin: authenticated && String(claims.roleId) === '2',
    };
}

export function saveSession({ token, user }) {
    const claims = tokenClaims(token);
    if (!Number.isInteger(claims?.id) || claims.id !== user?.id ||
        String(claims.roleId) !== String(user?.roleId) || !Number.isFinite(claims.exp) || claims.exp * 1000 <= Date.now()) {
        throw new Error('Invalid login response');
    }
    localStorage.setItem('token', token);
    localStorage.setItem('userId', String(user.id));
    localStorage.setItem('userRoleId', String(user.roleId));
    localStorage.setItem('username', user.username || '');
    window.dispatchEvent(new Event(SESSION_EVENT));
}

export function clearSession() {
    KEYS.forEach(key => localStorage.removeItem(key));
    window.dispatchEvent(new Event(SESSION_EVENT));
}
