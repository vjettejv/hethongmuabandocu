import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { errorMessage } from '../services/contracts';
import { ErrorNotice } from '../components/Page';

export default function Register() {
    const [form, setForm] = useState({ username: '', email: '', password: '' });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [message, setMessage] = useState('');
    const navigate = useNavigate();
    const register = async () => {
        if (busy) return;
        setBusy(true); setError(''); setMessage('');
        try {
            await api.post('/auth/register', { ...form, username: form.username.trim(), email: form.email.trim() });
            setStep(2); setOtp(''); setMessage('Yêu cầu gửi mã OTP đã được tiếp nhận. Hãy kiểm tra email của bạn.');
        } catch (failure) { setError(errorMessage(failure, 'Không thể đăng ký.')); }
        finally { setBusy(false); }
    };
    const verify = async event => {
        event.preventDefault();
        if (busy) return;
        setBusy(true); setError('');
        try {
            await api.post('/auth/verify-otp', { email: form.email.trim(), otp });
            navigate('/login', { replace: true });
        } catch (failure) { setError(errorMessage(failure, 'Mã OTP không đúng.')); }
        finally { setBusy(false); }
    };
    return <div className="container"><section className="card card-pad auth-card">
        <h1 className="page-title">{step === 1 ? 'Đăng ký' : 'Xác thực OTP'}</h1>
        <ErrorNotice error={error} />
        {message && <p className="hint" role="status">{message}</p>}
        {step === 1 ? <form className="form-stack" onSubmit={event => { event.preventDefault(); register(); }}>
            <label className="field"><span className="label">Tên đăng nhập</span><input className="input" required autoComplete="username" value={form.username}
                onChange={event => setForm({ ...form, username: event.target.value })} /></label>
            <label className="field"><span className="label">Email</span><input className="input" required type="email" autoComplete="email" value={form.email}
                onChange={event => setForm({ ...form, email: event.target.value })} /></label>
            <label className="field"><span className="label">Mật khẩu</span><input className="input" required type="password" autoComplete="new-password" value={form.password}
                onChange={event => setForm({ ...form, password: event.target.value })} /></label>
            <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Đang đăng ký…' : 'Đăng ký'}</button>
        </form> : <form className="form-stack" onSubmit={verify}>
            <p className="hint">Email nhận OTP: {form.email}</p>
            <label className="field"><span className="label">Mã OTP</span><input className="input" required inputMode="numeric" pattern="[0-9]{6}"
                maxLength={6} autoComplete="one-time-code" value={otp} onChange={event => setOtp(event.target.value.replace(/[^0-9]/g, ''))} /></label>
            <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Đang xác thực…' : 'Xác thực và kích hoạt'}</button>
            <button className="btn btn-ghost" type="button" disabled={busy} onClick={register}>Gửi lại OTP</button>
            <button className="btn btn-ghost" type="button" disabled={busy} onClick={() => { setStep(1); setError(''); setMessage(''); }}>Sửa thông tin đăng ký</button>
        </form>}
        <p className="hint">Đã có tài khoản? <Link to="/login">Đăng nhập</Link></p>
    </section></div>;
}
