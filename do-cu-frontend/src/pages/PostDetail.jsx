import { useState, useEffect } from 'react';
import { Link, useParams, useNavigate, useLocation } from 'react-router-dom';
import api, { serverOrigin } from '../services/api';
import useSession from '../hooks/useSession';
import { errorMessage, imageSource, formatPrice } from '../services/contracts';
import { ErrorNotice } from '../components/Page';

function PostDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [post, setPost] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [favorite, setFavorite] = useState(false);
    const [favoriteBusy, setFavoriteBusy] = useState(false);
    const [favoriteError, setFavoriteError] = useState('');
    const session = useSession();
    const location = useLocation();

    useEffect(() => {
        setFavorite(false); setFavoriteError('');
        if (!session.isAuthenticated) { setFavoriteBusy(false); return; }
        const controller = new AbortController();
        setFavoriteBusy(true);
        api.get(`/favorites/check/${id}`, { signal: controller.signal }).then(({ data }) => {
            if (!controller.signal.aborted) setFavorite(data.isFavorited === true);
        }).catch(failure => { if (!controller.signal.aborted) setFavoriteError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setFavoriteBusy(false); });
        return () => controller.abort();
    }, [id, session.isAuthenticated]);

    const toggleFavorite = async () => {
        if (!session.isAuthenticated) { navigate('/login', { state: { from: location.pathname } }); return; }
        if (favoriteBusy) return;
        setFavoriteBusy(true); setFavoriteError('');
        try { const { data } = await api.post('/favorites/toggle', { postId: Number(id) }); setFavorite(data.isFavorited === true); }
        catch (failure) { setFavoriteError(errorMessage(failure)); }
        finally { setFavoriteBusy(false); }
    };

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError('');
        setPost(null);
        api.get(`/posts/${id}`, { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setPost(response.data?.data ?? response.data);
        }).catch(() => {
            if (!controller.signal.aborted) setError('Không tải được sản phẩm.');
        }).finally(() => {
            if (!controller.signal.aborted) setLoading(false);
        });
        return () => controller.abort();
    }, [id]);

    if (loading) return <div className="container" role="status">Đang tải sản phẩm…</div>;
    if (error || !post) return <div className="container" role="alert"><p>{error || 'Không tìm thấy sản phẩm.'}</p><Link to="/">Về trang chủ</Link></div>;
    const image = imageSource(post.Images?.[0]?.imageUrl, serverOrigin);

    return (
        <div className="container">
            <Link to="/" className="btn btn-ghost">Về trang chủ</Link>
            <div className="detail">
                {image ? <img className="detail-img" src={image} alt={post.title} /> :
                    <div className="detail-img product-placeholder">Chưa có ảnh</div>}
                <section className="card card-pad">
                    <h1>{post.title}</h1>
                    <p className="product-price">{formatPrice(post.price)}</p>
                    <p className="hint">{post.Category?.name}</p>
                    <p style={{ whiteSpace: 'pre-wrap' }}>{post.description}</p>
                    <ErrorNotice error={favoriteError} />
                    <div className="product-cta">
                        <button type="button" className="btn btn-primary" disabled={session.userId === Number(post.userId)} onClick={() => navigate(`/chat?to=${post.userId}`)}>Chat nhanh</button>
                        <button type="button" className="btn btn-ghost" disabled={favoriteBusy} aria-pressed={favorite} onClick={toggleFavorite}>
                            {favoriteBusy ? 'Đang xử lý…' : favorite ? 'Bỏ yêu thích' : 'Yêu thích'}
                        </button>
                    </div>
                </section>
            </div>
        </div>
    );
}
export default PostDetail;
