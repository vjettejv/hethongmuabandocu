import { useState, useEffect } from 'react';
import api from '../services/api';

function MyFavorites() {
    const [favorites, setFavorites] = useState([]);
    return (
        <div>
            {favorites.map(fav => (
                <div key={fav.id}>{fav.postId}</div>
            ))}
        </div>
    );
}
export default MyFavorites;