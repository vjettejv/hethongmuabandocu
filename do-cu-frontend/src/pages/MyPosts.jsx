import { useState, useEffect } from 'react';
import api from '../services/api';

function MyPosts() {
    const [myPosts, setMyPosts] = useState([]);
    const handleDelete = async (id) => {
        await api.delete(`/posts/${id}`);
        setMyPosts(myPosts.filter(p => p.id !== id));
    };

    return (
        <div className="container">
            {myPosts.map(post => (
                <button key={post.id} onClick={() => handleDelete(post.id)}>Xoa</button>
            ))}
        </div>
    );
}
export default MyPosts;