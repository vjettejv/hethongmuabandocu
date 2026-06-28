import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function Register() {
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // Bước 1: Điền form | Bước 2: Nhập OTP

    const navigate = useNavigate();

    // XỬ LÝ GỬI FORM ĐĂNG KÝ
    const handleRegister = async (e) => {
        e.preventDefault();
        Swal.fire({ title: 'Đang xử lý...', text: 'Đang gửi email xác nhận', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        try {
            await api.post('/auth/register', formData);
            Swal.close();
            Swal.fire('Thành công!', 'Vui lòng kiểm tra Email để lấy mã OTP', 'success');
            setStep(2); // Chuyển sang màn hình nhập OTP
        } catch (error) {
            Swal.close();
            Swal.fire('Lỗi', error.response?.data?.message || error.response?.data?.error || 'Không thể đăng ký', 'error');
        }
    };

    // XỬ LÝ XÁC THỰC OTP
    const handleVerify = async (e) => {
        e.preventDefault();
        try {
            await api.post('/auth/verify-otp', { otp });
            Swal.fire({
                icon: 'success', title: 'Xác thực thành công!', text: 'Bạn có thể đăng nhập!', timer: 2000
            }).then(() => navigate('/login'));
        } catch (error) {
            Swal.fire('Lỗi', error.response?.data?.message || 'Mã OTP sai rồi!', 'error');
        }
    };

    return (
        <div className="container">
            <div className="card card-pad" style={{ maxWidth: 520, margin: '0 auto' }}>
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>
                            {step === 1 ? 'Đăng ký' : 'Xác thực OTP'}
                        </h2>
                        <div className="hint">
                            {step === 1
                                ? 'Tạo tài khoản để đăng tin và chat thuận tiện.'
                                : 'Nhập mã OTP 6 chữ số đã gửi tới email của bạn.'}
                        </div>
                    </div>
                    <button className="btn btn-ghost" type="button" onClick={() => navigate('/')}>
                        Về trang chủ
                    </button>
                </div>

                {step === 1 ? (
                    <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                        <div className="field">
                            <div className="label">Tên đăng nhập</div>
                            <input
                                className="input"
                                type="text"
                                placeholder="VD: phamvandat"
                                required
                                value={formData.username}
                                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                            />
                        </div>
                        <div className="field">
                            <div className="label">Email</div>
                            <input
                                className="input"
                                type="email"
                                placeholder="VD: dat@gmail.com"
                                required
                                value={formData.email}
                                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                            />
                        </div>
                        <div className="field">
                            <div className="label">Mật khẩu</div>
                            <input
                                className="input"
                                type="password"
                                placeholder="Tối thiểu 6 ký tự (khuyến nghị)"
                                required
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            />
                        </div>

                        <button className="btn btn-primary" type="submit" style={{ marginTop: 6 }}>
                            Đăng ký
                        </button>

                        <div className="hint" style={{ textAlign: 'center', marginTop: 6 }}>
                            Đã có tài khoản?{' '}
                            <span style={{ color: 'var(--primary)', fontWeight: 900, cursor: 'pointer' }} onClick={() => navigate('/login')}>
                                Đăng nhập
                            </span>
                        </div>
                    </form>
                ) : (
                    <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                        <div className="card card-pad" style={{ background: 'rgba(15,23,42,0.03)' }}>
                            <div className="label">Email nhận OTP</div>
                            <div className="hint" style={{ marginTop: 6, fontWeight: 900 }}>
                                {formData.email}
                            </div>
                        </div>

                        <div className="field">
                            <div className="label">Mã OTP</div>
                            <input
                                className="input"
                                type="text"
                                placeholder="Nhập 6 chữ số"
                                required
                                maxLength="6"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                inputMode="numeric"
                                style={{ textAlign: 'center', fontSize: 18, letterSpacing: 6, fontWeight: 900 }}
                            />
                        </div>

                        <button className="btn btn-primary" type="submit">
                            Xác thực & kích hoạt
                        </button>

                        <button className="btn btn-ghost" type="button" onClick={() => { setStep(1); setOtp(''); }}>
                            Gửi lại OTP
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
export default Register;