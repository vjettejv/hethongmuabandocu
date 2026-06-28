import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function Register() {
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // BÆ°á»›c 1: Äiá»n form | BÆ°á»›c 2: Nháº­p OTP

    const navigate = useNavigate();

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