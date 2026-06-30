import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../services/api';

function PostDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const [post, setPost] = useState(null);

    return (
        <div>
            <button onClick={() => navigate(`/chat?to=${post?.userId}`)}>Chat nhanh</button>
        </div>
    );
}
export default PostDetail;