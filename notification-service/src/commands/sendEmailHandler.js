const sendEmailHandler = async ({ to, subject, text, html }) => {
    return { message: 'Email queued' };
};

module.exports = sendEmailHandler;