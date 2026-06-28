import { useState, useEffect } from 'react';
import api from '../services/api';

function Home() {
    const [posts, setPosts] = useState([]);
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

    useEffect(() => {
        api.get('/posts').then(res => setPosts(res.data.data || res.data));
    }, []);

    return (
        <div className="container">
            <aside className="sidebar">
                <ul className="cat-list">
                    <li className={!selectedCategory ? 'cat-item active' : 'cat-item'} onClick={() => setSelectedCategory(null)}>
                        <span>Táº¥t cáº£ sáº£n pháº©m</span>
                    </li>
                </ul>
            </aside>
            <div className="toolbar">
                <input className="input" type="text" value={searchTerm} onChange={e => setSearchTerm(e.target.value)} />
            </div>
        </div>
    );
}
export default Home;