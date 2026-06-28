const AuthUser = require('../models/AuthUser');

const verifyOtpHandler = async ({ email, otp }) => {
    const user = await AuthUser.findOne({ where: { email } });
    if (!user) throw new Error('User not found');
    
    if (user.otp !== otp) {
        throw new Error('MÃ£ OTP khÃ´ng chÃ­nh xÃ¡c');
    }
    
    user.isVerified = true;
    user.otp = null;
    await user.save();
    
    try {
        await fetch(`http://user-service:3002/${user.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fullName: user.username })
        });
    } catch(err) {
        console.error("Failed to create profile", err);
    }
    
    return { message: 'Verified successfully' };
};

module.exports = verifyOtpHandler;