import { useState } from 'react';
import api from '../services/api';

function Login() {
    const [formData, setFormData] = useState({ email: '', password: '' });
    const handleLogin = async (e) => {
        e.preventDefault();
        await api.post('/auth/login', formData);
    };
    return (
        <form onSubmit={handleLogin}>
            <input type="email" onChange={e => setFormData({ ...formData, email: e.target.value })} />
            <input type="password" onChange={e => setFormData({ ...formData, password: e.target.value })} />
        </form>
    );
}
export default Login;