import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import api from '../services/api';
import { saveSession } from '../services/session';
import { errorMessage, safeReturnPath } from '../services/contracts';
import useSession from '../hooks/useSession';
import { ErrorNotice } from '../components/Page';

export default function Login() {
    const [form, setForm] = useState({ email: '', password: '' });
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const navigate = useNavigate();
    const location = useLocation();
    const session = useSession();
    const destination = safeReturnPath(location.state?.from);
    if (session.isAuthenticated) return <Navigate to={destination} replace />;

    const submit = async event => {
        event.preventDefault();
        if (busy) return;
        setBusy(true);
        setError('');
        try {
            const response = await api.post('/auth/login', { email: form.email.trim(), password: form.password });
            saveSession(response.data);
            navigate(destination, { replace: true });
        } catch (failure) { setError(errorMessage(failure, 'Không thể đăng nhập.')); }
        finally { setBusy(false); }
    };
    return <div className="container"><section className="card card-pad auth-card">
        <h1 className="page-title">Đăng nhập</h1>
        <p className="hint">Đăng nhập để đăng tin, lưu sản phẩm và nhắn tin.</p>
        <ErrorNotice error={error} />
        <form className="form-stack" onSubmit={submit}>
            <label className="field"><span className="label">Email</span>
                <input className="input" type="email" name="email" autoComplete="username" required value={form.email}
                    onChange={event => setForm({ ...form, email: event.target.value })} />
            </label>
            <label className="field"><span className="label">Mật khẩu</span>
                <input className="input" type="password" name="password" autoComplete="current-password" required value={form.password}
                    onChange={event => setForm({ ...form, password: event.target.value })} />
            </label>
            <button className="btn btn-primary" type="submit" disabled={busy}>{busy ? 'Đang đăng nhập…' : 'Đăng nhập'}</button>
        </form>
        <p className="hint">Chưa có tài khoản? <Link to="/register">Đăng ký</Link></p>
    </section></div>;
}
