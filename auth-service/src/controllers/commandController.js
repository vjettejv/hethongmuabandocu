const registerHandler = require('../commands/registerHandler');
const loginHandler = require('../commands/loginHandler');
const verifyOtpHandler = require('../commands/verifyOtpHandler');

const register = async (req, res) => {
    try {
        const result = await registerHandler(req.body);
        res.status(201).json(result);
    } catch (error) {
        if (error.message === 'Vui lòng điền đầy đủ thông tin' || error.message === 'Email đã được sử dụng' || error.message === 'Tên đăng nhập đã tồn tại') {
            return res.status(400).json({ message: error.message });
        }
        res.status(500).json({ error: error.message });
    }
};

const login = async (req, res) => {
    try {
        const result = await loginHandler(req.body);
        res.json(result);
    } catch (error) {
        if (error.message === 'Invalid credentials') {
            return res.status(401).json({ error: error.message });
        }
        res.status(500).json({ error: error.message });
    }
};

const verifyOtp = async (req, res) => {
    try {
        const result = await verifyOtpHandler(req.body);
        res.json(result);
    } catch (error) {
        if (error.message === 'User not found') return res.status(404).json({ error: error.message });
        if (error.message === 'Mã OTP không chính xác') return res.status(400).json({ error: error.message });
        res.status(500).json({ error: error.message });
    }
};

module.exports = { register, login, verifyOtp };
