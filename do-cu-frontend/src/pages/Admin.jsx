import { useState, useEffect } from 'react';
import api, { serverOrigin } from '../services/api';
import { useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';

function Admin() {
    const [posts, setPosts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [newCat, setNewCat] = useState({ name: '', description: '' });
    const [tab, setTab] = useState('posts');
    const navigate = useNavigate();

    useEffect(() => {
        loadData();
    }, []);

    const loadData = () => {
        // Lấy TOÀN BỘ bài đăng (kể cả pending)
        api.get('/admin/posts').then(res => {
            const data = res.data.data || res.data;
            setPosts(Array.isArray(data) ? data : []);
        }).catch(err => console.error("Lỗi tải bài đăng:", err));

        // Lấy danh mục
        api.get('/categories').then(res => {
            const data = res.data.data || res.data;
            setCategories(Array.isArray(data) ? data : []);
        }).catch(err => console.error("Lỗi tải danh mục:", err));
    };

    // --- QUẢN LÝ BÀI ĐĂNG ---
    const handleApprove = async (id, currentStatus) => {
        const newStatus = currentStatus === 'approved' ? 'pending' : 'approved';
        try {
            await api.put(`/admin/posts/${id}`, { status: newStatus });
            Swal.fire({
                icon: 'success',
                title: newStatus === 'approved' ? 'ĐÃ DUYỆT BÀI' : 'ĐÃ HẠ BÀI',
                timer: 1000,
                showConfirmButton: false
            });
            loadData();
        } catch (err) {
            Swal.fire('LỖI', 'Không thể cập nhật trạng thái', 'error');
        }
    };

    const deletePost = async (id) => {
        Swal.fire({
            title: 'XÁC NHẬN XÓA?',
            text: "Bài đăng này sẽ bị xóa vĩnh viễn khỏi hệ thống!",
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#dc3545',
            cancelButtonColor: '#6c757d',
            confirmButtonText: 'ĐỒNG Ý XÓA',
            cancelButtonText: 'HỦY'
        }).then(async (result) => {
            if (result.isConfirmed) {
                try {
                    await api.delete(`/admin/posts/${id}`);
                    Swal.fire('ĐÃ XÓA!', 'Bài đăng đã được gỡ bỏ.', 'success');
                    loadData();
                } catch (err) {
                    Swal.fire('LỖI', 'Có lỗi khi xóa bài đăng', 'error');
                }
            }
        });
    };

    // --- QUẢN LÝ DANH MỤC ---
    const handleAddCategory = async (e) => {
        e.preventDefault();
        try {
            await api.post('/admin/categories', newCat);
            Swal.fire('THÀNH CÔNG', 'Đã thêm danh mục mới!', 'success');
            setNewCat({ name: '', description: '' });
            loadData();
        } catch (err) {
            Swal.fire('LỖI', 'Không thể thêm danh mục', 'error');
        }
    };

    // Hàm lấy ảnh chuẩn hóa như trang Home
    const getAdminImg = (p) => {
        const img = p.Images?.[0]?.imageUrl || p.images?.[0]?.imageUrl;
        if (!img) return 'https://placehold.co/50x50?text=NO+IMG';
        if (img.startsWith('http')) return img;
        const cleanPath = img.startsWith('/') ? img : `/${img}`;
        return `${serverOrigin}${cleanPath}`;
    };

    return (
        <div className="container">
            <div className="card card-pad">
                <div className="toolbar">
                    <div className="toolbar-grow">
                        <h2 className="toolbar-title" style={{ margin: 0 }}>Quản trị</h2>
                        <div className="hint">Duyệt bài đăng và quản lý danh mục.</div>
                    </div>
                    <div className="tabs" role="tablist" aria-label="Admin tabs">
                        <button className={tab === 'posts' ? 'tab active' : 'tab'} type="button" onClick={() => setTab('posts')}>
                            Bài đăng
                        </button>
                        <button className={tab === 'categories' ? 'tab active' : 'tab'} type="button" onClick={() => setTab('categories')}>
                            Danh mục
                        </button>
                    </div>
                    <button className="btn btn-ghost" type="button" onClick={loadData}>
                        Làm mới
                    </button>
                    <button className="btn btn-ghost" type="button" onClick={() => navigate('/')}>
                        Về trang chủ
                    </button>
                </div>

                {tab === 'posts' && (
                    <div style={{ marginTop: 14 }}>
                        <div className="card card-pad" style={{ marginBottom: 12 }}>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12 }}>
                                <div style={{ fontWeight: 900 }}>Danh sách bài đăng</div>
                                <span className="badge">{posts.length} tin</span>
                            </div>
                        </div>

                        <div className="table-wrap">
                            <table className="table">
                                <thead>
                                    <tr>
                                        <th style={{ width: 80 }}>ID</th>
                                        <th style={{ width: 84 }}>Ảnh</th>
                                        <th>Tiêu đề</th>
                                        <th>Mô tả</th>
                                        <th style={{ width: 140 }}>Giá</th>
                                        <th style={{ width: 140 }}>Trạng thái</th>
                                        <th style={{ width: 220 }}>Thao tác</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {posts.map((p) => {
                                        const statusClass = p.status === 'approved' ? 'approved' : 'pending';
                                        const statusLabel = p.status === 'approved' ? 'Đã duyệt' : 'Chờ duyệt';
                                        return (
                                            <tr key={p.id}>
                                                <td>#{p.id}</td>
                                                <td>
                                                    <img
                                                        src={getAdminImg(p)}
                                                        style={{ width: 50, height: 40, objectFit: 'cover', borderRadius: 10, border: '1px solid rgba(15,23,42,0.10)' }}
                                                        alt=""
                                                        onError={(e) => (e.target.src = 'https://placehold.co/50x40?text=IMG')}
                                                    />
                                                </td>
                                                <td style={{ fontWeight: 900 }}>
                                                    <div style={{ maxWidth: 360, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }} title={p.title}>
                                                        {p.title}
                                                    </div>
                                                </td>
                                                <td>
                                                    <div style={{ maxWidth: 420, overflow: 'hidden', whiteSpace: 'nowrap', textOverflow: 'ellipsis' }} title={p.description}>
                                                        {p.description || '—'}
                                                    </div>
                                                </td>
                                                <td style={{ fontWeight: 900, color: 'var(--primary)' }}>{p.price?.toLocaleString()} đ</td>
                                                <td>
                                                    <span className={`status ${statusClass}`}>{statusLabel}</span>
                                                </td>
                                                <td>
                                                    <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                                                        <button
                                                            className={p.status === 'approved' ? 'btn btn-ghost' : 'btn btn-primary'}
                                                            type="button"
                                                            onClick={() => handleApprove(p.id, p.status)}
                                                        >
                                                            {p.status === 'approved' ? 'Hạ bài' : 'Duyệt'}
                                                        </button>
                                                        <button className="btn btn-danger" type="button" onClick={() => deletePost(p.id)}>
                                                            Xóa
                                                        </button>
                                                    </div>
                                                </td>
                                            </tr>
                                        );
                                    })}
                                    {posts.length === 0 && (
                                        <tr>
                                            <td colSpan="7" style={{ padding: 20, color: 'var(--muted)', fontWeight: 800 }}>
                                                Chưa có bài đăng nào.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {tab === 'categories' && (
                    <div style={{ marginTop: 14 }}>
                        <div className="card card-pad">
                            <div style={{ fontWeight: 900, marginBottom: 6 }}>Thêm danh mục</div>
                            <form onSubmit={handleAddCategory} style={{ display: 'grid', gridTemplateColumns: '1fr 2fr auto', gap: 10, alignItems: 'end' }}>
                                <div className="field">
                                    <div className="label">Tên danh mục</div>
                                    <input
                                        className="input"
                                        type="text"
                                        placeholder="VD: Đồ gia dụng"
                                        value={newCat.name}
                                        onChange={(e) => setNewCat({ ...newCat, name: e.target.value })}
                                        required
                                    />
                                </div>
                                <div className="field">
                                    <div className="label">Mô tả</div>
                                    <input
                                        className="input"
                                        type="text"
                                        placeholder="Mô tả ngắn..."
                                        value={newCat.description}
                                        onChange={(e) => setNewCat({ ...newCat, description: e.target.value })}
                                    />
                                </div>
                                <button className="btn btn-primary" type="submit" style={{ height: 44 }}>
                                    Thêm
                                </button>
                            </form>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginTop: 12 }}>
                            {categories.map((c) => (
                                <div key={c.id} className="card card-pad">
                                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: 10, alignItems: 'baseline' }}>
                                        <div style={{ fontWeight: 900 }}>{c.name}</div>
                                        <span className="badge">#{c.id}</span>
                                    </div>
                                    <div className="hint" style={{ marginTop: 8 }}>
                                        {c.description || 'Không có mô tả.'}
                                    </div>
                                </div>
                            ))}
                            {categories.length === 0 && (
                                <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
                                    <div style={{ fontWeight: 900, marginBottom: 6 }}>Chưa có danh mục</div>
                                    <div className="hint">Hãy thêm danh mục đầu tiên để người dùng dễ lọc sản phẩm.</div>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default Admin;