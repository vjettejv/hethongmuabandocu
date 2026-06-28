// File: src/pages/PostDetail.jsx
import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api, { serverOrigin } from '../services/api';
import Swal from 'sweetalert2';

function PostDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [post, setPost] = useState(null);
    const [seller, setSeller] = useState(null);
    const [reviews, setReviews] = useState([]);
    const [rating, setRating] = useState(5);
    const [hoverRating, setHoverRating] = useState(0);
    const [comment, setComment] = useState('');
    const [reviewImage, setReviewImage] = useState(null);
    const [editingReviewId, setEditingReviewId] = useState(null);
    const [filterRating, setFilterRating] = useState(0);
    const [filterHasImage, setFilterHasImage] = useState('all');
    const [currentImageIndex, setCurrentImageIndex] = useState(0);
    const [isFavorited, setIsFavorited] = useState(false);
    const myUserId = localStorage.getItem('userId');

    const StarRating = ({ value, onSelect, interactive = true }) => (
        <div style={{ display: 'flex', gap: 4, cursor: interactive ? 'pointer' : 'default' }}>
            {[1, 2, 3, 4, 5].map(star => (
                <span
                    key={star}
                    onClick={() => interactive && onSelect(star)}
                    onMouseEnter={() => interactive && setHoverRating(star)}
                    onMouseLeave={() => interactive && setHoverRating(0)}
                    style={{
                        fontSize: interactive ? 28 : 18,
                        color: star <= (interactive ? (hoverRating || value) : value) ? '#f59e0b' : '#d1d5db',
                        transition: 'color 0.15s, transform 0.15s',
                        transform: interactive && star <= hoverRating ? 'scale(1.2)' : 'scale(1)',
                        userSelect: 'none'
                    }}
                >
                    ★
                </span>
            ))}
        </div>
    );
    useEffect(() => {
        api.get(`/posts/${id}`)
            .then(res => {
                setPost(res.data.data || res.data);
            })
            .catch(err => {
                console.error(err);
                Swal.fire('Lỗi', 'Không thể tải thông tin sản phẩm', 'error');
            });
        
        if (myUserId) {
            api.get(`/favorites/check/${id}`)
                .then(res => setIsFavorited(res.data.isFavorited))
                .catch(err => console.error("Lỗi kiểm tra favorite", err));
        }
    }, [id, myUserId]);

    const fetchReviews = () => {
        if (!post?.userId) return;
        let url = `/reviews/user/${post.userId}?`;
        if (filterRating > 0) url += `rating=${filterRating}&`;
        if (filterHasImage !== 'all') url += `hasImage=${filterHasImage}`;
        
        api.get(url)
            .then((res) => setReviews(res.data || []))
            .catch(err => console.error("Lỗi lấy review:", err));
    };

    useEffect(() => {
        if (!post?.userId) return;
        api.get(`/users/${post.userId}`)
            .then((res) => setSeller(res.data?.data || res.data || null))
            .catch(() => setSeller(null));
            
        fetchReviews();
    }, [post?.userId, filterRating, filterHasImage]);

    const handlePostReview = async () => {
        if (!myUserId) {
            Swal.fire('Lỗi', 'Vui lòng đăng nhập để đánh giá', 'warning');
            return;
        }
        if (myUserId == post.userId) {
            Swal.fire('Lỗi', 'Bạn không thể tự đánh giá mình', 'error');
            return;
        }
        try {
            const formData = new FormData();
            formData.append('reviewerId', myUserId);
            formData.append('revieweeId', post.userId);
            formData.append('postId', post.id);
            formData.append('rating', rating);
            formData.append('comment', comment);
            if (reviewImage) formData.append('image', reviewImage);

            if (editingReviewId) {
                const res = await api.put(`/reviews/${editingReviewId}`, formData, { headers: { 'Content-Type': 'multipart/form-data' }});
                setReviews(reviews.map(r => r.id === editingReviewId ? res.data : r));
                setEditingReviewId(null);
                Swal.fire('Thành công', 'Đã cập nhật đánh giá', 'success');
            } else {
                const res = await api.post('/reviews', formData, { headers: { 'Content-Type': 'multipart/form-data' }});
                setReviews([res.data, ...reviews]);
                Swal.fire('Thành công', 'Cảm ơn bạn đã đánh giá', 'success');
            }
            setComment('');
            setRating(5);
            setReviewImage(null);
            document.getElementById('review-image-input').value = '';
        } catch (err) {
            Swal.fire('Lỗi', 'Không thể gửi đánh giá', 'error');
        }
    };

    const handleDeleteReview = async (id) => {
        const result = await Swal.fire({
            title: 'Xác nhận xóa?',
            text: 'Bạn có chắc muốn xóa đánh giá này không?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Xóa',
            cancelButtonText: 'Hủy'
        });
        
        if (result.isConfirmed) {
            try {
                await api.delete(`/reviews/${id}`);
                setReviews(reviews.filter(r => r.id !== id));
                Swal.fire('Đã xóa', 'Đánh giá đã bị xóa', 'success');
            } catch (err) {
                Swal.fire('Lỗi', 'Không thể xóa đánh giá', 'error');
            }
        }
    };

    const handleEditClick = (r) => {
        setEditingReviewId(r.id);
        setRating(r.rating);
        setComment(r.comment || '');
        setReviewImage(null);
        document.getElementById('review-image-input').value = '';
        window.scrollTo({ top: document.getElementById('review-section').offsetTop, behavior: 'smooth' });
    };

    const handleToggleFavorite = async () => {
        if (!myUserId) {
            Swal.fire('Lỗi', 'Vui lòng đăng nhập để lưu tin', 'warning');
            return;
        }
        try {
            const res = await api.post('/favorites/toggle', { postId: post.id });
            setIsFavorited(res.data.isFavorited);
            Swal.fire('Thành công', res.data.message === 'Added to favorites' ? 'Đã lưu vào danh sách yêu thích' : 'Đã xóa khỏi danh sách yêu thích', 'success');
        } catch (err) {
            Swal.fire('Lỗi', 'Không thể thao tác', 'error');
        }
    };

    // Hàm xử lý ảnh chuẩn xác
    const getImageUrl = (path) => {
        if (!path) return 'https://placehold.co/600x400?text=Chua+Co+Anh';
        if (path.startsWith('http')) return path;
        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        return `${serverOrigin}${cleanPath}`;
    };

    // Lấy danh sách ảnh
    const imagesList = post?.Images || post?.images || [];
    const allImageUrls = imagesList.length > 0 
        ? imagesList.map(img => getImageUrl(img.imageUrl)) 
        : [getImageUrl(post?.image || post?.imageUrl)];

    if (!post) return <div style={{ textAlign: 'center', marginTop: '50px' }}>Đang tải dữ liệu...</div>;

    return (
        <div className="container">
            <div className="detail">
                <div className="card card-pad" style={{ position: 'relative' }}>
                    <img
                        className="detail-img"
                        src={allImageUrls[currentImageIndex]}
                        alt={`${post.title} - Ảnh ${currentImageIndex + 1}`}
                        onError={(e) => (e.target.src = 'https://placehold.co/900x600?text=Loi+Hien+Thi+Anh')}
                        style={{ width: '100%', height: 'auto', maxHeight: '500px', objectFit: 'contain', borderRadius: '8px' }}
                    />
                    
                    {/* Controls */}
                    {allImageUrls.length > 1 && (
                        <>
                            <button 
                                onClick={() => setCurrentImageIndex(prev => prev === 0 ? allImageUrls.length - 1 : prev - 1)}
                                style={{ position: 'absolute', top: '50%', left: '20px', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.5)', color: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}
                            >
                                &#10094;
                            </button>
                            <button 
                                onClick={() => setCurrentImageIndex(prev => prev === allImageUrls.length - 1 ? 0 : prev + 1)}
                                style={{ position: 'absolute', top: '50%', right: '20px', transform: 'translateY(-50%)', background: 'rgba(0,0,0,0.5)', color: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '20px' }}
                            >
                                &#10095;
                            </button>
                            <div style={{ position: 'absolute', bottom: '20px', left: '50%', transform: 'translateX(-50%)', display: 'flex', gap: '8px' }}>
                                {allImageUrls.map((_, idx) => (
                                    <span 
                                        key={idx} 
                                        onClick={() => setCurrentImageIndex(idx)}
                                        style={{ width: '10px', height: '10px', borderRadius: '50%', background: currentImageIndex === idx ? '#ee4d2d' : 'rgba(255,255,255,0.7)', cursor: 'pointer', border: '1px solid rgba(0,0,0,0.2)' }}
                                    />
                                ))}
                            </div>
                        </>
                    )}
                </div>

                <div className="card card-pad">
                    <div className="toolbar" style={{ marginBottom: 10 }}>
                        <button className="btn btn-ghost" type="button" onClick={() => navigate(-1)}>
                            Quay lại
                        </button>
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                        <h1 style={{ margin: 0, fontSize: 26, lineHeight: 1.2 }}>{post.title}</h1>
                        <button
                            type="button"
                            onClick={handleToggleFavorite}
                            title={isFavorited ? 'Bỏ lưu tin' : 'Lưu tin yêu thích'}
                            style={{ 
                                background: isFavorited ? '#ff4d4f' : '#f1f5f9',
                                color: isFavorited ? '#fff' : '#64748b',
                                border: 'none',
                                borderRadius: '50%',
                                width: '44px',
                                height: '44px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '22px',
                                cursor: 'pointer',
                                transition: 'all 0.2s ease',
                                flexShrink: 0,
                                boxShadow: isFavorited ? '0 4px 12px rgba(255, 77, 79, 0.3)' : 'none'
                            }}
                        >
                            {isFavorited ? '♥' : '♡'}
                        </button>
                    </div>
                    <div className="product-price" style={{ fontSize: 22, marginTop: 10 }}>
                        {post.price?.toLocaleString()} đ
                    </div>

                    <div className="kv" style={{ marginTop: 14 }}>
                        <div className="kv-item">
                            <div className="kv-label">Người bán</div>
                            <div className="kv-value">
                                {seller?.fullName?.trim() ? seller.fullName : seller?.username?.trim() ? seller.username : 'Đang cập nhật'}
                            </div>
                        </div>
                        <div className="kv-item">
                            <div className="kv-label">Tình trạng</div>
                            <div className="kv-value">{post.condition || '—'}</div>
                        </div>
                        <div className="kv-item">
                            <div className="kv-label">Danh mục</div>
                            <div className="kv-value">{post.Category?.name || 'Đang cập nhật'}</div>
                        </div>
                    </div>

                    <div style={{ marginTop: 14 }}>
                        <div className="label">Mô tả</div>
                        <div className="hint" style={{ whiteSpace: 'pre-line', marginTop: 6 }}>
                            {post.description || 'Chưa có mô tả.'}
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: 10, marginTop: 16 }}>
                        <button 
                            className="btn btn-primary" 
                            type="button" 
                            onClick={() => {
                                const urlParams = new URLSearchParams();
                                urlParams.set('to', post.userId);
                                urlParams.set('msg', `Chào bạn, mình quan tâm đến sản phẩm:\n[${post.title}]\n(${window.location.origin}/post/${post.id})`);
                                navigate(`/chat?${urlParams.toString()}`);
                            }}
                        >
                            Nhắn tin cho người bán
                        </button>
                        <button
                            className="btn btn-ghost"
                            type="button"
                            onClick={() => {
                                Swal.fire('Gợi ý', 'Bạn có thể nhắn tin để thương lượng và hẹn giao dịch.', 'info');
                            }}
                        >
                            Mẹo mua an toàn
                        </button>
                    </div>
                </div>

                <div className="card card-pad" style={{ marginTop: 20 }} id="review-section">
                    <h2 style={{ margin: '0 0 16px 0', fontSize: 20 }}>Đánh giá người bán</h2>
                    
                    <div style={{ marginBottom: 20 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                            <span>Điểm:</span>
                            <StarRating value={rating} onSelect={setRating} interactive={true} />
                            <span style={{ color: '#f59e0b', fontWeight: 700 }}>{rating} Sao</span>
                        </div>
                        <textarea 
                            className="input" 
                            rows="3" 
                            placeholder="Chia sẻ trải nghiệm của bạn về người bán này..."
                            value={comment}
                            onChange={e => setComment(e.target.value)}
                            style={{ marginBottom: 10 }}
                        />
                        <div>
                            <input 
                                type="file" 
                                id="review-image-input"
                                accept="image/*" 
                                onChange={(e) => setReviewImage(e.target.files[0])}
                                style={{ fontSize: '14px', marginBottom: 10 }}
                            />
                        </div>
                        <div style={{ display: 'flex', gap: '10px' }}>
                            <button className="btn btn-primary" onClick={handlePostReview}>
                                {editingReviewId ? 'Cập nhật đánh giá' : 'Gửi đánh giá'}
                            </button>
                            {editingReviewId && (
                                <button className="btn btn-ghost" onClick={() => {
                                    setEditingReviewId(null);
                                    setComment('');
                                    setRating(5);
                                    setReviewImage(null);
                                    document.getElementById('review-image-input').value = '';
                                }}>
                                    Hủy sửa
                                </button>
                            )}
                        </div>
                    </div>

                    <div style={{ borderTop: '1px solid #ddd', paddingTop: 16 }}>
                        <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap' }}>
                            <select className="input" style={{ width: 'auto' }} value={filterRating} onChange={(e) => setFilterRating(Number(e.target.value))}>
                                <option value={0}>Tất cả số sao</option>
                                <option value={5}>5 Sao</option>
                                <option value={4}>4 Sao</option>
                                <option value={3}>3 Sao</option>
                                <option value={2}>2 Sao</option>
                                <option value={1}>1 Sao</option>
                            </select>
                            <select className="input" style={{ width: 'auto' }} value={filterHasImage} onChange={(e) => setFilterHasImage(e.target.value)}>
                                <option value="all">Tất cả đánh giá</option>
                                <option value="true">Có hình ảnh</option>
                                <option value="false">Không có hình ảnh</option>
                            </select>
                        </div>

                        {reviews.length > 0 ? reviews.map(r => (
                            <div key={r.id} style={{ marginBottom: 14, padding: 10, background: '#f9f9f9', borderRadius: 8 }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 4 }}>
                                    <div>
                                        <StarRating value={r.rating} onSelect={() => {}} interactive={false} />
                                        <small className="hint">{new Date(r.createdAt).toLocaleDateString('vi-VN')}</small>
                                    </div>
                                    {String(r.reviewerId) === String(myUserId) && (
                                        <div style={{ display: 'flex', gap: '8px' }}>
                                            <button onClick={() => handleEditClick(r)} style={{ border: 'none', background: 'transparent', color: '#3b82f6', cursor: 'pointer', fontSize: '13px' }}>Sửa</button>
                                            <button onClick={() => handleDeleteReview(r.id)} style={{ border: 'none', background: 'transparent', color: '#ef4444', cursor: 'pointer', fontSize: '13px' }}>Xóa</button>
                                        </div>
                                    )}
                                </div>
                                <div style={{ marginTop: '8px', marginBottom: r.imageUrl ? '8px' : '0' }}>{r.comment || 'Không có bình luận'}</div>
                                {r.imageUrl && (
                                    <img 
                                        src={getImageUrl(r.imageUrl)} 
                                        alt="Review Image" 
                                        style={{ width: '100px', height: '100px', objectFit: 'cover', borderRadius: '4px', cursor: 'pointer', border: '1px solid #ddd' }} 
                                        onClick={() => window.open(getImageUrl(r.imageUrl), '_blank')}
                                    />
                                )}
                            </div>
                        )) : <div className="hint">Chưa có đánh giá nào phù hợp.</div>}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default PostDetail;