import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import { errorMessage, listData, formatPrice, statusLabel } from '../services/contracts';
import Page, { ErrorNotice } from '../components/Page';

export default function Admin() {
    const [posts, setPosts] = useState([]);
    const [tab, setTab] = useState('pending');
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(null);
    const [error, setError] = useState('');
    const [retry, setRetry] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true); setError('');
        api.get('/admin/posts', { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setPosts(listData(response).sort((a,b) => b.id - a.id));
        }).catch(failure => { if (!controller.signal.aborted) setError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [retry]);
    const moderate = async (id, status) => {
        if (busy !== null) return;
        setBusy(id); setError('');
        try { await api.put(`/admin/posts/${id}`, { status }); setPosts(rows => rows.map(row => row.id === id ? { ...row, status } : row)); }
        catch (failure) { setError(errorMessage(failure)); }
        finally { setBusy(null); }
    };
    const filtered = posts.filter(post => tab === 'all' || (tab === 'pending' ? ['pending','available'].includes(post.status) : post.status === tab));
    const current = Math.min(page, Math.max(1, Math.ceil(filtered.length / 20)));
    return <Page title="Quản trị tin đăng">
        <div className="toolbar"><div className="tabs">{Object.entries({ pending: 'Chờ duyệt', approved: 'Đã duyệt', rejected: 'Từ chối', all: 'Tất cả' }).map(([key, label]) =>
            <button type="button" key={key} aria-pressed={tab === key} className={tab === key ? 'tab active' : 'tab'} onClick={() => { setTab(key); setPage(1); }}>{label}</button>)}</div>
            <button className="btn btn-ghost" onClick={() => setRetry(value => value + 1)}>Tải lại</button></div>
        <ErrorNotice error={error} />
        {loading ? <p role="status">Đang tải tin…</p> : filtered.length === 0 ? <p role="status">Không có tin trong mục này.</p> : <>
            <p className="hint">{filtered.length} tin</p><div className="table-wrap"><table className="table"><thead><tr><th>Tiêu đề</th><th>Giá</th><th>Trạng thái</th><th>Thao tác</th></tr></thead>
                <tbody>{filtered.slice((current - 1) * 20, current * 20).map(post => <tr key={post.id}>
                    <td><Link to={`/post/${post.id}`}>{post.title}</Link></td><td>{formatPrice(post.price)}</td><td><span className={`status ${post.status}`}>{statusLabel(post.status)}</span></td>
                    <td><div className="product-cta"><button className="btn btn-primary" disabled={busy !== null || post.status === 'approved'} onClick={() => moderate(post.id, 'approved')}>Duyệt</button>
                        <button className="btn btn-danger" disabled={busy !== null || post.status === 'rejected'} onClick={() => moderate(post.id, 'rejected')}>Từ chối</button></div></td>
                </tr>)}</tbody></table></div>
            {filtered.length > 20 && <nav className="pagination" aria-label="Phân trang quản trị">
                <button className="btn btn-ghost" disabled={current === 1} onClick={() => setPage(current - 1)}>Trang trước</button><span>Trang {current} / {Math.ceil(filtered.length / 20)}</span>
                <button className="btn btn-ghost" disabled={current * 20 >= filtered.length} onClick={() => setPage(current + 1)}>Trang sau</button>
            </nav>}
        </>}
    </Page>;
}
