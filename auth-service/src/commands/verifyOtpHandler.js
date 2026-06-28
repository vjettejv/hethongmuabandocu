const AuthUser = require('../models/AuthUser');

const verifyOtpHandler = async ({ email, otp }) => {
    const user = await AuthUser.findOne({ where: { email } });
    if (!user) throw new Error('User not found');
    
    if (user.otp !== otp) {
        throw new Error('MÃ£ OTP khÃ´ng chÃ­nh xÃ¡c');
    }
    
    return { message: 'Verified successfully' };
};

module.exports = verifyOtpHandler;