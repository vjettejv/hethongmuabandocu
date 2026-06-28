const verifyOtpHandler = async ({ email, otp }) => {
    return { message: 'Verified successfully' };
};

module.exports = verifyOtpHandler;