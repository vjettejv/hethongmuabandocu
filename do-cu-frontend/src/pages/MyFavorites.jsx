import { useState, useEffect } from 'react';
import api from '../services/api';

function MyFavorites() {
    const [favorites, setFavorites] = useState([]);
    useEffect(() => {
        api.get('/favorites').then(res => setFavorites(res.data));
    }, []);
    return (
        <div>MyFavorites Component</div>
    );
}
export default MyFavorites;