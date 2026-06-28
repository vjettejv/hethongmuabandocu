import { useState } from 'react';

function Login() {
    const [formData, setFormData] = useState({ email: '', password: '' });
    return (
        <form>
            <input type="email" onChange={e => setFormData({ ...formData, email: e.target.value })} />
            <input type="password" onChange={e => setFormData({ ...formData, password: e.target.value })} />
        </form>
    );
}
export default Login;