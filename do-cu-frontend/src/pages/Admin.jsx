import { useState, useEffect } from 'react';
import api from '../services/api';

function Admin() {
    const [posts, setPosts] = useState([]);
    const [tab, setTab] = useState('pending');
    return (
        <div>Admin tabs</div>
    );
}
export default Admin;