import { useState, useEffect } from 'react';
import api from '../services/api';

function MyFavorites() {
    const [favorites, setFavorites] = useState([]);
    const handleRemove = async (postId) => {
        await api.delete(`/favorites/${postId}`);
    };
    return (
        <div>
            {favorites.map(fav => (
                <button key={fav.id} onClick={() => handleRemove(fav.postId)}>Remove</button>
            ))}
        </div>
    );
}
export default MyFavorites;