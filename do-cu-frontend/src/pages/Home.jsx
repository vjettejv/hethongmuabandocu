import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import api, { serverOrigin } from '../services/api';
import { formatPrice, imageSource } from '../services/contracts';

const PAGE_SIZE = 12;

function rowsFrom(response) {
    const rows = response.data?.data ?? response.data;
    if (!Array.isArray(rows)) throw new Error('Invalid list response');
    return rows;
}

function Home() {
    const [posts, setPosts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [page, setPage] = useState(1);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [reloadTick, setReloadTick] = useState(0);

    useEffect(() => {
        const controller = new AbortController();
        setLoading(true);
        setError('');
        Promise.all([
            api.get('/posts', { signal: controller.signal }),
            api.get('/categories', { signal: controller.signal }),
        ]).then(([postResponse, categoryResponse]) => {
            if (controller.signal.aborted) return;
            setPosts(rowsFrom(postResponse));
            setCategories(rowsFrom(categoryResponse));
        }).catch(() => {
            if (!controller.signal.aborted) setError('Không tải được sản phẩm. Vui lòng thử lại.');
        }).finally(() => {
            if (!controller.signal.aborted) setLoading(false);
        });
        return () => controller.abort();
    }, [reloadTick]);

    const filteredPosts = useMemo(() => {
        const query = searchTerm.trim().toLocaleLowerCase('vi-VN');
        return posts.filter(post =>
            post.status === 'approved' &&
            (selectedCategory === null || String(post.categoryId) === String(selectedCategory)) &&
            (!query || `${post.title ?? ''} ${post.description ?? ''}`.toLocaleLowerCase('vi-VN').includes(query))
        ).sort((a, b) => Date.parse(b.createdAt) - Date.parse(a.createdAt) || b.id - a.id);
    }, [posts, selectedCategory, searchTerm]);
    const totalPages = Math.max(1, Math.ceil(filteredPosts.length / PAGE_SIZE));
    const currentPage = Math.min(page, totalPages);
    const visiblePosts = filteredPosts.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE);

    const selectCategory = (id) => {
        setSelectedCategory(id);
        setPage(1);
    };

    return (
        <div className="container home-grid">
            <aside className="sidebar card card-pad" aria-label="Danh mục sản phẩm">
                <h2 className="sidebar-title">DANH MỤC</h2>
                <ul className="cat-list">
                    <li>
                        <button type="button" className={selectedCategory === null ? 'cat-item active' : 'cat-item'}
                            aria-pressed={selectedCategory === null} onClick={() => selectCategory(null)}>
                            Tất cả sản phẩm
                        </button>
                    </li>
                    {categories.map(category => (
                        <li key={category.id}>
                            <button type="button" className={selectedCategory === category.id ? 'cat-item active' : 'cat-item'}
                                aria-pressed={selectedCategory === category.id} onClick={() => selectCategory(category.id)}>
                                {category.name}
                            </button>
                        </li>
                    ))}
                </ul>
            </aside>
            <section aria-label="Sản phẩm">
                <div className="toolbar">
                    <h1 className="toolbar-title">Sản phẩm</h1>
                    <span className="badge" aria-live="polite">{filteredPosts.length} sản phẩm</span>
                </div>
                <div className="toolbar">
                    <input className="input" type="search" aria-label="Tìm sản phẩm"
                        placeholder="Tìm sản phẩm…" value={searchTerm}
                        onChange={event => { setSearchTerm(event.target.value); setPage(1); }} />
                </div>
                {loading ? <p role="status">Đang tải sản phẩm…</p> : error ? (
                    <div className="card card-pad" role="alert">
                        <p>{error}</p>
                        <button type="button" className="btn btn-primary" onClick={() => setReloadTick(tick => tick + 1)}>Thử lại</button>
                    </div>
                ) : filteredPosts.length === 0 ? <p role="status">Không có sản phẩm phù hợp.</p> : (
                    <>
                        <div className="grid">
                            {visiblePosts.map(post => {
                                const image = imageSource(post.Images?.[0]?.imageUrl, serverOrigin);
                                return (
                                    <Link key={post.id} to={`/post/${post.id}`} className="product">
                                        {image ? <img className="product-img" src={image} alt={post.title} loading="lazy" /> :
                                            <div className="product-img product-placeholder">Chưa có ảnh</div>}
                                        <div className="product-body">
                                            <h2 className="product-title">{post.title}</h2>
                                            <div className="product-price">{formatPrice(post.price)}</div>
                                            <span className="hint">{post.Category?.name}</span>
                                        </div>
                                    </Link>
                                );
                            })}
                        </div>
                        {totalPages > 1 && <nav className="pagination" aria-label="Phân trang sản phẩm">
                            <button type="button" className="btn btn-ghost" disabled={currentPage === 1}
                                onClick={() => setPage(currentPage - 1)}>Trang trước</button>
                            <span aria-live="polite">Trang {currentPage} / {totalPages}</span>
                            <button type="button" className="btn btn-ghost" disabled={currentPage === totalPages}
                                onClick={() => setPage(currentPage + 1)}>Trang sau</button>
                        </nav>}
                    </>
                )}
            </section>
        </div>
    );
}
export default Home;
