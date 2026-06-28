import { useState, useEffect } from 'react';
import api, { serverOrigin } from '../services/api';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';

function MyPosts() {
    const [myPosts, setMyPosts] = useState([]);
    const [contacts, setContacts] = useState([]);
    const navigate = useNavigate();
    useEffect(() => {
        // Lấy danh sách tin của chính mình
        api.get('/posts/my-posts')
            .then(res => setMyPosts(res.data.data || res.data))
            .catch(err => console.log(err));
    }, []);

    useEffect(() => {
        let mounted = true;
        api
            .get('/messages/contacts')
            .then((res) => {
                const data = res.data?.data || res.data || [];
                if (!mounted) return;
                setContacts(Array.isArray(data) ? data : []);
            })
            .catch((err) => {
                console.error('Lỗi tải danh sách liên hệ:', err);
                if (!mounted) return;
                setContacts([]);
            });
        return () => {
            mounted = false;
        };
    }, []);

    const handleDelete = async (id) => {
        // Dùng SweetAlert2 thay cho window.confirm mặc định để giao diện chuyên nghiệp hơn
        Swal.fire({
            title: 'XÁC NHẬN XÓA?',
            text: "Tin đăng này sẽ bị xóa vĩnh viễn khỏi hệ thống!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'ĐỒNG Ý XÓA',
            cancelButtonText: 'HỦY'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    await api.delete(`/posts/${id}`);
                    setMyPosts(myPosts.filter(p => p.id !== id));
                    Swal.fire('ĐÃ XÓA!', 'Tin của bạn đã được xóa thành công.', 'success');
                } catch (err) {
                    Swal.fire('LỖI!', 'Không thể xóa tin lúc này.', 'error');
                }
            }
        });
    };

    // Hàm lấy ảnh chuẩn xác như trang chủ
    const getImageUrl = (post) => {
        const imageList = post.Images || post.images;
        if (imageList && imageList.length > 0) {
            const path = imageList[0].imageUrl;
            if (!path) return 'https://placehold.co/100x100?text=LOI+ANH';
            if (path.startsWith('http')) return path;
            const cleanPath = path.startsWith('/') ? path : `/${path}`;
            return `${serverOrigin}${cleanPath}`;
        }
        return 'https://placehold.co/100x100?text=CHUA+CO+ANH';
    };

    return (
        <div className="container">
            <div className="card card-pad">
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>Tin của tôi</h2>
                        <div className="hint">Theo dõi trạng thái duyệt và quản lý tin đăng.</div>
                    </div>
                    <button className="btn btn-ghost" type="button" onClick={() => navigate('/')}>
                        Về trang chủ
                    </button>
                    <button className="btn btn-primary" type="button" onClick={() => navigate('/create-post')}>
                        Đăng tin mới
                    </button>
                </div>

                <div className="card card-pad" style={{ marginTop: 14 }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                        <div style={{ fontWeight: 900 }}>Người đã liên hệ</div>
                        <span className="badge">{contacts.length}</span>
                    </div>
                    <div className="hint" style={{ marginTop: 6 }}>
                        Chọn một người để mở đúng cuộc chat họ đã nhắn với bạn.
                    </div>

                    <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 12 }}>
                        {contacts.length === 0 ? (
                            <div className="hint" style={{ padding: 6 }}>Chưa có ai liên hệ.</div>
                        ) : (
                            contacts.map((c) => {
                                const id = c?.user?.id;
                                if (!id) return null;
                                const name = c.user.fullName?.trim() || c.user.username?.trim() || `User #${id}`;
                                const preview = c.lastMessage?.content || '';
                                return (
                                    <div key={id} className="card card-pad" style={{ padding: 12, display: 'flex', gap: 12, alignItems: 'center', justifyContent: 'space-between' }}>
                                        <div style={{ minWidth: 0 }}>
                                            <div style={{ fontWeight: 900 }}>{name}</div>
                                            <div className="hint" style={{ marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 740 }}>
                                                {preview ? preview : '—'}
                                            </div>
                                        </div>
                                        <button className="btn btn-ghost" type="button" onClick={() => navigate(`/chat?to=${id}`)}>
                                            Mở chat
                                        </button>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>

                {myPosts.length === 0 ? (
                    <div className="card card-pad" style={{ marginTop: 14, textAlign: 'center' }}>
                        <div style={{ fontWeight: 900, marginBottom: 6 }}>Bạn chưa có tin nào</div>
                        <div className="hint">Hãy đăng tin đầu tiên để bắt đầu mua bán.</div>
                        <div style={{ marginTop: 12 }}>
                            <button className="btn btn-primary" type="button" onClick={() => navigate('/create-post')}>
                                Đăng tin ngay
                            </button>
                        </div>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 14 }}>
                        {myPosts.map((post) => {
                            const statusClass = post.status === 'approved' ? 'approved' : post.status === 'rejected' ? 'rejected' : 'pending';
                            const statusLabel =
                                post.status === 'approved' ? 'Đã duyệt' : post.status === 'rejected' ? 'Bị từ chối' : 'Chờ duyệt';

                            return (
                                <div key={post.id} className="card card-pad" style={{ display: 'flex', gap: 14, alignItems: 'center' }}>
                                    <img
                                        src={getImageUrl(post)}
                                        alt={post.title}
                                        style={{ width: 110, height: 90, objectFit: 'cover', borderRadius: 12, border: '1px solid rgba(15,23,42,0.10)' }}
                                    />

                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'flex-start' }}>
                                            <div style={{ minWidth: 0 }}>
                                                <div style={{ fontWeight: 900, fontSize: 14, lineHeight: 1.25, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                                    {post.title}
                                                </div>
                                                <div className="hint" style={{ marginTop: 6 }}>
                                                    ID: #{post.id}
                                                </div>
                                            </div>
                                            <span className={`status ${statusClass}`}>{statusLabel}</span>
                                        </div>

                                        <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginTop: 10, flexWrap: 'wrap' }}>
                                            <div className="product-price" style={{ fontSize: 15 }}>
                                                {post.price?.toLocaleString()} đ
                                            </div>
                                            <button className="btn btn-ghost" type="button" onClick={() => navigate(`/post/${post.id}`)}>
                                                Xem tin
                                            </button>
                                            <button className="btn btn-danger" type="button" onClick={() => handleDelete(post.id)}>
                                                Xóa tin
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}

export default MyPosts;