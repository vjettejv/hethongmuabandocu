import { useState, useEffect } from 'react';
import api from '../services/api';

function Account() {
    const [profile, setProfile] = useState({ fullName: '', phone: '', address: '', avatar: '' });
    const handleUpdate = async (e) => {
        e.preventDefault();
        await api.put('/users/profile', profile);
    };
    return (
        <form onSubmit={handleUpdate}>
            <input type="text" value={profile.fullName} onChange={e => setProfile({...profile, fullName: e.target.value})} />
        </form>
    );
}
export default Account;