import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import Swal from 'sweetalert2';

function Register() {
    const [formData, setFormData] = useState({ username: '', email: '', password: '' });
    const [otp, setOtp] = useState('');
    const [step, setStep] = useState(1); // BÆ°á»›c 1: Äiá»n form | BÆ°á»›c 2: Nháº­p OTP

    const navigate = useNavigate();
    return (
        <div>Register Component</div>
    );
}
export default Register;