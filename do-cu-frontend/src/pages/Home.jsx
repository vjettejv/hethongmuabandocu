import { useState } from 'react';

function Home() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');

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