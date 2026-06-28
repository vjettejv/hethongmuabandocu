import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function Register() {
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // BÆ°á»›c 1: Äiá»n form | BÆ°á»›c 2: Nháº­p OTP

    const navigate = useNavigate();

    // Xá»¬ LÃ Gá»¬I FORM ÄÄ‚NG KÃ
    const handleRegister = async (e) => {
        e.preventDefault();
        Swal.fire({ title: 'Äang xá»­ lÃ½...', text: 'Äang gá»­i email xÃ¡c nháº­n', allowOutsideClick: false, didOpen: () => Swal.showLoading() });

        try {
            await api.post('/auth/register', formData);
            Swal.close();
            Swal.fire('ThÃ nh cÃ´ng!', 'Vui lÃ²ng kiá»ƒm tra Email Ä‘á»ƒ láº¥y mÃ£ OTP', 'success');
            setStep(2); // Chuyá»ƒn sang mÃ n hÃ¬nh nháº­p OTP
        } catch (error) {
            Swal.close();
            Swal.fire('Lá»—i', error.response?.data?.message || error.response?.data?.error || 'KhÃ´ng thá»ƒ Ä‘Äƒng kÃ½', 'error');
        }
    };

    // Xá»¬ LÃ XÃC THá»°C OTP
    const handleVerify = async (e) => {
        e.preventDefault();
        try {
            await api.post('/auth/verify-otp', { otp });
            Swal.fire({
                icon: 'success', title: 'XÃ¡c thá»±c thÃ nh cÃ´ng!', text: 'Báº¡n cÃ³ thá»ƒ Ä‘Äƒng nháº­p!', timer: 2000
            }).then(() => navigate('/login'));
        } catch (error) {
            Swal.fire('Lá»—i', error.response?.data?.message || 'MÃ£ OTP sai rá»“i!', 'error');
        }
    };

    return (
        <div className="container">
            <div className="card card-pad" style={{ maxWidth: 520, margin: '0 auto' }}>
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>
                            {step === 1 ? 'ÄÄƒng kÃ½' : 'XÃ¡c thá»±c OTP'}
                        </h2>
                        <div className="hint">
                            {step === 1
                                ? 'Táº¡o tÃ i khoáº£n Ä‘á»ƒ Ä‘Äƒng tin vÃ  chat thuáº­n tiá»‡n.'
                                : 'Nháº­p mÃ£ OTP 6 chá»¯ sá»‘ Ä‘Ã£ gá»­i tá»›i email cá»§a báº¡n.'}
                        </div>
                    </div>
                    <button className="btn btn-ghost" type="button" onClick={() => navigate('/')}>
                        Vá» trang chá»§
                    </button>
                </div>
            </div>
        </div>
    );
}
export default Register;