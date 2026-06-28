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

    // XỬ LÝ XÁC THỰC OTP (Có lỗi thiếu email)
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
            </div>
        </div>
    );
}
export default Register;