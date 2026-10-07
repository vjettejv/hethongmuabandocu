export function listData(response) {
    const value = response?.data?.data ?? response?.data;
    if (!Array.isArray(value)) throw new Error('Invalid list response');
    return value;
}

export function errorMessage(error, fallback = 'Không thể thực hiện. Vui lòng thử lại.') {
    if (error?.response?.status === 401) return 'Thông tin đăng nhập không đúng hoặc phiên đăng nhập đã hết hạn.';
    if (error?.response?.status >= 500) return 'Máy chủ đang gặp lỗi. Vui lòng thử lại sau.';
    const message = error?.response?.data?.message || error?.response?.data?.error;
    const translated = {
        'Invalid credentials': 'Email hoặc mật khẩu không đúng.',
        'Invalid OTP': 'Mã OTP không đúng.',
        'User not found': 'Không tìm thấy tài khoản.',
        'Post not found': 'Không tìm thấy sản phẩm.',
        'Profile not found': 'Chưa có thông tin tài khoản.',
    };
    return typeof message === 'string' ? translated[message] || message : fallback;
}

export const formatPrice = value => value == null ? 'Liên hệ' : new Intl.NumberFormat('vi-VN', {
    style: 'currency', currency: 'VND', minimumFractionDigits: 0, maximumFractionDigits: 2,
}).format(Number(value));
export const statusLabel = status => ({ approved: 'Đã duyệt', pending: 'Chờ duyệt', available: 'Chờ duyệt', rejected: 'Từ chối', deleted: 'Đã xóa' }[status] || status);
export const mergeMessage = (rows, message) => rows.some(row => String(row.id) === String(message.id)) ? rows : [...rows, message];
export function imageSource(path, origin = '') {
    if (typeof path !== 'string') return '';
    if (/^https?:\/\//i.test(path)) return path;
    return path.startsWith('/uploads/') ? `${origin}${path}` : '';
}
export function safeReturnPath(path) {
    return typeof path === 'string' && path.startsWith('/') && !path.startsWith('//') &&
        !path.includes('\\') && !/^\/(login|register)(?:[/?#]|$)/.test(path) ? path : '/';
}
