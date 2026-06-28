import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import api from '../services/api';

function PostDetail() {
    const { id } = useParams();
    const [post, setPost] = useState(null);

    useEffect(() => {
        api.get(`/posts/${id}`).then(res => setPost(res.data.data || res.data));
    }, [id]);

    return (
        <div>PostDetail</div>
    );
}
export default PostDetail;