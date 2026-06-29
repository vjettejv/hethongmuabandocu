const sendEmailHandler = async ({ to, subject, text, html }) => {
    if (process.env.NODE_ENV !== 'production') {
        console.log(`[MOCK EMAIL] To: ${to}, Subject: ${subject}`);
        return { message: 'Email queued (Mock)', mock: true };
    }
    return { message: 'Email sent successfully' };
};

module.exports = sendEmailHandler;