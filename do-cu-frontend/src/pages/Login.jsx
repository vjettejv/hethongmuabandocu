import { useState } from 'react';
import api from '../services/api';

function Login() {
    const [formData, setFormData] = useState({ email: '', password: '' });
    const handleLogin = async (e) => {
        e.preventDefault();
        const res = await api.post('/auth/login', formData);
        localStorage.setItem('token', res.data.token);
    };
    return (
        <form onSubmit={handleLogin}>
            <input type="email" onChange={e => setFormData({ ...formData, email: e.target.value })} />
            <input type="password" onChange={e => setFormData({ ...formData, password: e.target.value })} />
        </form>
    );
}
export default Login;