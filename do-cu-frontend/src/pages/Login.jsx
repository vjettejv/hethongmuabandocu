import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        try {
            // 1. Gọi API Đăng nhập
            const res = await api.post('/auth/login', { username, password });
            const token = res.data.token;

            if (!token) {
                alert("Đăng nhập thất bại: Máy chủ không trả về Token!");
                return;
            }

            // 2. Lưu Token và ID người dùng
            localStorage.setItem('token', token);
            localStorage.setItem('userId', res.data.user?.id || res.data.id || '');

            // 3. Lấy thông tin quyền (Role)
            let roleIdToSave = '1'; // Mặc định là người dùng bình thường (1)

            try {
                // Thử lấy từ dữ liệu trả về trực tiếp
                if (res.data.user && res.data.user.roleId) {
                    roleIdToSave = res.data.user.roleId.toString();
                } 
                // Nếu không có, giải mã token để lấy thông tin
                else {
                    const base64Url = token.split('.')[1];
                    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
                    const jsonPayload = decodeURIComponent(window.atob(base64).split('').map(function (c) {
                        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
                    }).join(''));

                    const decodedToken = JSON.parse(jsonPayload);
                    if (decodedToken.roleId) {
                        roleIdToSave = decodedToken.roleId.toString();
                    }
                }
            } catch (parseError) {
                console.error("Lỗi giải mã token, sử dụng quyền mặc định:", parseError);
            }

            // 4. Lưu quyền và điều hướng
            localStorage.setItem('userRoleId', roleIdToSave);
            Swal.fire({
                icon: 'success',
                title: 'Đăng nhập thành công',
                text: 'Hệ thống đang chuyển hướng...',
                timer: 1500, // Tự động đóng sau 1.5s
                showConfirmButton: false
            }).then(() => {
                window.location.href = '/';
            });

        } catch (error) {
            Swal.fire({
                icon: 'error',
                title: 'Đăng nhập thất bại',
                text: 'Tên đăng nhập hoặc mật khẩu không chính xác.'
            });
        }
    };

    return (
        <div className="container">
            <div className="card card-pad" style={{ maxWidth: 460, margin: '0 auto' }}>
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>Đăng nhập</h2>
                        <div className="hint">Đăng nhập để đăng tin, quản lý tin và chat với người bán.</div>
                    </div>
                    <button className="btn btn-ghost" type="button" onClick={() => navigate('/')}>
                        Về trang chủ
                    </button>
                </div>

                <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 6 }}>
                    <div className="field">
                        <div className="label">Tên đăng nhập</div>
                        <input
                            className="input"
                            type="text"
                            placeholder="Nhập tên đăng nhập"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                        />
                    </div>
                    <div className="field">
                        <div className="label">Mật khẩu</div>
                        <input
                            className="input"
                            type="password"
                            placeholder="Nhập mật khẩu"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button className="btn btn-primary" type="submit" style={{ marginTop: 6 }}>
                        Đăng nhập
                    </button>

                    <div className="hint" style={{ textAlign: 'center', marginTop: 6 }}>
                        Chưa có tài khoản?{' '}
                        <span
                            style={{ color: 'var(--primary)', fontWeight: 900, cursor: 'pointer' }}
                            onClick={() => navigate('/register')}
                        >
                            Đăng ký ngay
                        </span>
                    </div>
                </form>
            </div>
        </div>
    );
}

export default Login;