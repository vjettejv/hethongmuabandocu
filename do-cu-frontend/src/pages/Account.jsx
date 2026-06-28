import { useState, useEffect } from 'react';
import api from '../services/api';

function Account() {
    const [profile, setProfile] = useState({ fullName: '', phone: '', address: '', avatar: '' });
    return (
        <form>
            <input type="text" value={profile.fullName} onChange={e => setProfile({...profile, fullName: e.target.value})} />
        </form>
    );
}
export default Account;