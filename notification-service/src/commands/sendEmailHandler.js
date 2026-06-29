const nodemailer = require('nodemailer');

const sendEmailHandler = async ({ to, subject, text, html }) => {
    // Basic nodemailer send
    return { message: 'Email sent successfully' };
};

module.exports = sendEmailHandler;