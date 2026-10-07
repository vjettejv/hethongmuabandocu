import { useState, useEffect } from 'react';
import api from '../services/api';
import { errorMessage } from '../services/contracts';
import Page, { ErrorNotice } from '../components/Page';

export default function Account() {
    const [profile, setProfile] = useState({ fullName: '', phone: '', address: '', avatar: '' });
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [loaded, setLoaded] = useState(false);
    const [retry, setRetry] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true); setError('');
        api.get('/users/me', { signal: controller.signal }).then(({ data }) => {
            if (!controller.signal.aborted) {
                setProfile(Object.fromEntries(['fullName', 'phone', 'address', 'avatar'].map(key => [key, data[key] ?? ''])));
                setLoaded(true);
            }
        }).catch(failure => { if (!controller.signal.aborted) setError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [retry]);
    const submit = async event => {
        event.preventDefault();
        if (busy) return;
        setBusy(true); setError(''); setSuccess('');
        try { await api.put('/users/me', profile); setSuccess('Đã lưu thông tin tài khoản.'); }
        catch (failure) { setError(errorMessage(failure)); }
        finally { setBusy(false); }
    };
    return <Page title="Tài khoản"><section className="card card-pad auth-card">
        <ErrorNotice error={error} />
        {success && <p role="status">{success}</p>}
        {loading ? <p role="status">Đang tải thông tin…</p> : !loaded ? <button className="btn btn-ghost" onClick={() => setRetry(value => value + 1)}>Tải lại thông tin</button> : <form className="form-stack" onSubmit={submit}>
            {Object.entries({ fullName: 'Họ và tên', phone: 'Số điện thoại', address: 'Địa chỉ', avatar: 'Đường dẫn ảnh đại diện' }).map(([key, label]) =>
                <label className="field" key={key}><span className="label">{label}</span>
                    <input className="input" type={key === 'phone' ? 'tel' : 'text'} value={profile[key]}
                        onChange={event => setProfile({ ...profile, [key]: event.target.value })} />
                </label>)}
            <button className="btn btn-primary" disabled={busy} type="submit">{busy ? 'Đang lưu…' : 'Lưu thông tin'}</button>
        </form>}
    </section></Page>;
}
