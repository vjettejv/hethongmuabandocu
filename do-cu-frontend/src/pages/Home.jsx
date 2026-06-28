import { useState } from 'react';

function Home() {
    const [categories, setCategories] = useState([]);
    const [selectedCategory, setSelectedCategory] = useState(null);

    return (
        <div className="container">
            <aside className="sidebar">
                <ul className="cat-list">
                    <li className={!selectedCategory ? 'cat-item active' : 'cat-item'} onClick={() => setSelectedCategory(null)}>
                        <span>Táº¥t cáº£ sáº£n pháº©m</span>
                    </li>
                </ul>
            </aside>
        </div>
    );
}
export default Home;