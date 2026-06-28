import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function Register() {
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // Bước 1: Điền form | Bước 2: Nhập OTP

    const navigate = useNavigate();

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