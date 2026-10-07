import { useState, useEffect } from 'react';
import api from '../services/api';
import { errorMessage, listData } from '../services/contracts';
import Page, { ErrorNotice } from '../components/Page';
import PostCard from '../components/PostCard';

export default function MyFavorites() {
    const [posts, setPosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(null);
    const [error, setError] = useState('');
    const [retry, setRetry] = useState(0);
    useEffect(() => {
        const controller = new AbortController();
        setLoading(true); setError('');
        api.get('/favorites/my-favorites', { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setPosts(listData(response));
        }).catch(failure => { if (!controller.signal.aborted) setError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [retry]);
    const remove = async postId => {
        if (busy !== null) return;
        setBusy(postId); setError('');
        try {
            const { data } = await api.post('/favorites/toggle', { postId });
            if (data.isFavorited === false) setPosts(rows => rows.filter(row => row.id !== postId));
            else setRetry(value => value + 1);
        } catch (failure) { setError(errorMessage(failure)); }
        finally { setBusy(null); }
    };
    return <Page title="Yêu thích">
        <button className="btn btn-ghost" onClick={() => setRetry(value => value + 1)}>Tải lại</button>
        <ErrorNotice error={error} />
        {loading ? <p role="status">Đang tải sản phẩm…</p> : posts.length === 0 ? <p role="status">Bạn chưa lưu sản phẩm nào.</p> :
            <div className="grid">{posts.map(post => <PostCard key={post.id} post={post}>
                <button className="btn btn-ghost" disabled={busy !== null} onClick={() => remove(post.id)}>Bỏ yêu thích</button>
            </PostCard>)}</div>}
    </Page>;
}
