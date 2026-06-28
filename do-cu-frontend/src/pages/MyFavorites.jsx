import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { serverOrigin } from '../services/api';

function MyFavorites() {
    const [favorites, setFavorites] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        api.get('/favorites/my-favorites')
            .then(res => setFavorites(res.data))
            .catch(err => console.error("Lỗi tải tin yêu thích", err));
    }, []);

    const getImageUrl = (post) => {
        const path = post?.imageUrl || (post?.Images && post.Images.length > 0 ? post.Images[0].imageUrl : null) || (post?.images && post.images.length > 0 ? post.images[0].imageUrl : null);
        if (!path) return 'https://placehold.co/300x200?text=Chua+Co+Anh';
        if (path.startsWith('http')) return path;
        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        return `${serverOrigin}${cleanPath}`;
    };

    return (
        <div className="container">
            <div className="card card-pad">
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>Tin yêu thích</h2>
                        <div className="hint">Những sản phẩm bạn đang quan tâm</div>
                    </div>
                </div>

                <div className="grid" style={{ marginTop: 20 }}>
                    {favorites.length > 0 ? (
                        favorites.map(post => (
                            <article key={post.id} className="product" onClick={() => navigate(`/post/${post.id}`)}>
                                <img
                                    className="product-img"
                                    src={getImageUrl(post)}
                                    alt={post.title}
                                    onError={(e) => e.target.src = 'https://placehold.co/600x400?text=Loi+Anh'}
                                />
                                <div className="product-body">
                                    <h3 className="product-title" title={post.title}>{post.title}</h3>
                                    <div className="product-price">{parseFloat(post.price).toLocaleString()} đ</div>
                                    <div className="product-cta">
                                        <button className="btn btn-primary" type="button" onClick={(e) => { e.stopPropagation(); navigate(`/post/${post.id}`); }}>Xem chi tiết</button>
                                    </div>
                                </div>
                            </article>
                        ))
                    ) : (
                        <div className="hint" style={{ gridColumn: '1 / -1', padding: '20px 0' }}>Bạn chưa có tin yêu thích nào.</div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default MyFavorites;
