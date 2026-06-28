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

                {step === 1 ? (
                    <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                        <div className="field">
                            <div className="label">TÃªn Ä‘Äƒng nháº­p</div>
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
                            <div className="label">Máº­t kháº©u</div>
                            <input
                                className="input"
                                type="password"
                                placeholder="Tá»‘i thiá»ƒu 6 kÃ½ tá»± (khuyáº¿n nghá»‹)"
                                required
                                value={formData.password}
                                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                            />
                        </div>

                        <button className="btn btn-primary" type="submit" style={{ marginTop: 6 }}>
                            ÄÄƒng kÃ½
                        </button>

                        <div className="hint" style={{ textAlign: 'center', marginTop: 6 }}>
                            ÄÃ£ cÃ³ tÃ i khoáº£n?{' '}
                            <span style={{ color: 'var(--primary)', fontWeight: 900, cursor: 'pointer' }} onClick={() => navigate('/login')}>
                                ÄÄƒng nháº­p
                            </span>
                        </div>
                    </form>
                ) : (
                    <form onSubmit={handleVerify} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 8 }}>
                        <div className="card card-pad" style={{ background: 'rgba(15,23,42,0.03)' }}>
                            <div className="label">Email nháº­n OTP</div>
                            <div className="hint" style={{ marginTop: 6, fontWeight: 900 }}>
                                {formData.email}
                            </div>
                        </div>

                        <div className="field">
                            <div className="label">MÃ£ OTP</div>
                            <input
                                className="input"
                                type="text"
                                placeholder="Nháº­p 6 chá»¯ sá»‘"
                                required
                                maxLength="6"
                                value={otp}
                                onChange={(e) => setOtp(e.target.value)}
                                inputMode="numeric"
                                style={{ textAlign: 'center', fontSize: 18, letterSpacing: 6, fontWeight: 900 }}
                            />
                        </div>

                        <button className="btn btn-primary" type="submit">
                            XÃ¡c thá»±c & kÃ­ch hoáº¡t
                        </button>

                        <button className="btn btn-ghost" type="button" onClick={() => { setStep(1); setOtp(''); }}>
                            Gá»­i láº¡i OTP
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}
export default Register;