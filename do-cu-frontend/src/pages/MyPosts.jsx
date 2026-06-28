import { useState, useEffect } from 'react';
import api from '../services/api';

function MyPosts() {
    const [myPosts, setMyPosts] = useState([]);
    useEffect(() => {
        api.get('/posts/my-posts').then(res => setMyPosts(res.data.data || res.data));
    }, []);

    return (
        <div>MyPosts Component</div>
    );
}
export default MyPosts;