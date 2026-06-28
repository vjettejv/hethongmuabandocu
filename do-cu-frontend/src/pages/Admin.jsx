import { useState, useEffect } from 'react';
import api from '../services/api';

function Admin() {
    const [posts, setPosts] = useState([]);
    useEffect(() => {
        api.get('/posts').then(res => setPosts(res.data));
    }, []);
    return (
        <div>Admin</div>
    );
}
export default Admin;