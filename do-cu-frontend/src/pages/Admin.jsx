import { useState, useEffect } from 'react';
import api from '../services/api';

function Admin() {
    const [posts, setPosts] = useState([]);
    const handleStatus = async (id, status) => {
        await api.put(`/admin/posts/${id}`, { status });
    };
    return (
        <div>
            {posts.map(p => (
                <button key={p.id} onClick={() => handleStatus(p.id, 'approved')}>Approve</button>
            ))}
        </div>
    );
}
export default Admin;