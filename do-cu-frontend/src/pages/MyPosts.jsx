import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import Swal from 'sweetalert2';
import api from '../services/api';
import { errorMessage, listData, statusLabel } from '../services/contracts';
import PostCard from '../components/PostCard';
import Page, { ErrorNotice } from '../components/Page';

export default function MyPosts() {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(null);
    const [error, setError] = useState('');
    const [retry, setRetry] = useState(0);
    const [page, setPage] = useState(1);
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true); setError('');
        api.get('/posts/my-posts', { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setPosts(listData(response).sort((a,b) => b.id - a.id));
        }).catch(failure => { if (!controller.signal.aborted) setError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [retry]);
    const remove = async post => {
        if (busy !== null) return;
        const result = await Swal.fire({ title: 'Xóa tin này?', text: post.title, icon: 'warning', showCancelButton: true, confirmButtonText: 'Xóa tin', cancelButtonText: 'Hủy' });
        if (!result.isConfirmed) return;
        setBusy(post.id); setError('');
        try { await api.delete(`/posts/${post.id}`); setPosts(rows => rows.filter(row => row.id !== post.id)); }
        catch (failure) { setError(errorMessage(failure)); }
        finally { setBusy(null); }
    };
    const current = Math.min(page, Math.max(1, Math.ceil(posts.length / 12)));
    return <Page title="Tin của tôi">
        <div className="toolbar"><Link className="btn btn-primary" to="/create-post">Đăng tin mới</Link><button className="btn btn-ghost" onClick={() => setRetry(value => value + 1)}>Tải lại</button></div>
        <ErrorNotice error={error} />
        {loading ? <p role="status">Đang tải tin…</p> : posts.length === 0 ? <p role="status">Bạn chưa có tin đăng.</p> : <>
            <div className="grid">{posts.slice((current - 1) * 12, current * 12).map(post => <PostCard key={post.id} post={post}>
                <span className={`status ${post.status}`}>{statusLabel(post.status)}</span>
                <button className="btn btn-danger" disabled={busy !== null} onClick={() => remove(post)}>Xóa tin</button>
            </PostCard>)}</div>
            {posts.length > 12 && <nav className="pagination" aria-label="Phân trang tin của tôi">
                <button className="btn btn-ghost" disabled={current === 1} onClick={() => setPage(current - 1)}>Trang trước</button>
                <span>Trang {current}</span><button className="btn btn-ghost" disabled={current * 12 >= posts.length} onClick={() => setPage(current + 1)}>Trang sau</button>
            </nav>}
        </>}
    </Page>;
}
