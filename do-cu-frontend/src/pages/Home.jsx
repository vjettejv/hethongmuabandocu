import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import api, { serverOrigin } from '../services/api';
import Swal from 'sweetalert2';

function Home() {
    const [posts, setPosts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const navigate = useNavigate();

    const userRoleId = localStorage.getItem('userRoleId');
    const isAuthenticated = !!localStorage.getItem('token');
    useEffect(() => {
        // 1. Lấy danh sách danh mục từ Backend
        api.get('/categories')
            .then(res => setCategories(res.data.data || res.data))
            .catch(err => console.error("Lỗi lấy danh mục:", err));

        // 2. Lấy danh sách bài đăng từ Search Service (để tối ưu tìm kiếm)
        const endpoint = searchTerm ? '/search' : '/posts';
        api.get(endpoint, { params: { categoryId: selectedCategory, keyword: searchTerm, query: searchTerm, status: 'approved' } })
            .then(res => {
                setPosts(res.data.data || res.data);
            })
            .catch(err => console.error("Lỗi lấy bài đăng:", err));
    }, [selectedCategory, searchTerm]);

    // HÀM ĐỆ QUY HIỂN THỊ DANH MỤC PHÂN CẤP (CHA - CON)
    const renderCategories = (parentId = null, level = 0) => {
        return categories
            .filter(cat => {
                // Kiểm tra nếu parentId là null/0 thì đó là danh mục gốc
                return parentId === null
                    ? (!cat.parentId || cat.parentId === 0)
                    : cat.parentId === parentId;
            })
            .map(cat => (
                <div key={cat.id}>
                    <li
                        className={selectedCategory === cat.id ? 'cat-item active' : 'cat-item'}
                        onClick={() => setSelectedCategory(cat.id)}
                    >
                        <span className="cat-indent" style={{ ['--indent']: `${level * 14}px` }} aria-hidden="true" />
                        <span>{cat.name}</span>
                    </li>
                    {renderCategories(cat.id, level + 1)}
                </div>
            ));
    };

    // Hàm xử lý đường dẫn ảnh từ Database
    const getImageUrl = (post) => {
        // Hỗ trợ cả post từ post-service (có Images) và từ search-service (có imageUrl trực tiếp)
        const path = post.imageUrl || (post.Images && post.Images.length > 0 ? post.Images[0].imageUrl : null) || (post.images && post.images.length > 0 ? post.images[0].imageUrl : null);
        if (path) {
            if (path.startsWith('http')) return path; // Ảnh từ link ngoài
            const cleanPath = path.startsWith('/') ? path : `/${path}`;
            return `${serverOrigin}${cleanPath}`; // Ảnh upload cục bộ
        }
        return 'https://placehold.co/300x200?text=KHONG+CO+ANH';
    };

    return (
        <div className="container">
            <div className="home-grid">
                <aside className="sidebar">
                    <div className="card card-pad">
                        <p className="sidebar-title">DANH MỤC</p>
                        <ul className="cat-list">
                            <li
                                className={!selectedCategory ? 'cat-item active' : 'cat-item'}
                                onClick={() => setSelectedCategory(null)}
                            >
                                <span>Tất cả sản phẩm</span>
                            </li>
                            {renderCategories()}
                        </ul>
                    </div>
                </aside>

                <section>
                    <div className="toolbar">
                        <div className="toolbar-grow">
                            <h2 className="toolbar-title">Khám phá đồ cũ</h2>
                            <div className="hint">Tìm nhanh theo từ khóa, lọc theo danh mục.</div>
                        </div>
                        <span className="badge">{posts.length} tin</span>
                    </div>

                    <div className="card card-pad" style={{ marginBottom: 14 }}>
                        <div className="toolbar" style={{ marginBottom: 0 }}>
                            <div className="toolbar-grow">
                                <input
                                    className="input"
                                    type="text"
                                    placeholder="Tìm kiếm theo tên sản phẩm..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                />
                            </div>
                            {isAuthenticated && (
                                <button className="btn btn-primary" type="button" onClick={() => navigate('/create-post')}>
                                    Đăng tin
                                </button>
                            )}
                            {userRoleId?.toString() === '2' && (
                                <button className="btn btn-ghost" type="button" onClick={() => navigate('/admin')}>
                                    Quản trị
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="grid">
                        {posts.length > 0 ? (
                            posts.map((post) => (
                                <article key={post.id} className="product" onClick={() => navigate(`/post/${post.id}`)}>
                                    <img
                                        className="product-img"
                                        src={getImageUrl(post)}
                                        alt={post.title}
                                        onError={(e) => (e.target.src = 'https://placehold.co/600x400?text=LOI+ANH')}
                                    />
                                    <div className="product-body">
                                        <h3 className="product-title" title={post.title}>
                                            {post.title}
                                        </h3>
                                        <div className="product-price">{post.price?.toLocaleString()} đ</div>
                                        <div className="product-cta">
                                            <button className="btn btn-ghost" type="button" onClick={(e) => { e.stopPropagation(); navigate(`/post/${post.id}`); }}>
                                                Xem chi tiết
                                            </button>
                                            <button
                                                className="btn btn-primary"
                                                type="button"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/post/${post.id}`);
                                                }}
                                            >
                                                Mua nhanh
                                            </button>
                                        </div>
                                    </div>
                                </article>
                            ))
                        ) : (
                            <div className="card card-pad" style={{ gridColumn: '1 / -1' }}>
                                <div style={{ fontWeight: 900, marginBottom: 6 }}>Không tìm thấy sản phẩm</div>
                                <div className="hint">Hãy thử đổi từ khóa hoặc chọn danh mục khác.</div>
                            </div>
                        )}
                    </div>
                </section>
            </div>
        </div>
    );
}

export default Home;