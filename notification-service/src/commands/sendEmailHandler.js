const transporter = require('../config/mailer');

const sendEmailHandler = async ({ to, subject, text, html }) => {
    if (process.env.NODE_ENV !== 'production' || process.env.MOCK_EMAIL === 'true' || !process.env.SMTP_USER) {
        console.log(`[MOCK EMAIL] To: ${to}, Subject: ${subject}`);
        return { message: 'Email queued (Mock)', mock: true };
    }


    const info = await transporter.sendMail({
        from: `"Đồ Cũ Marketplace" <${process.env.SMTP_USER || 'noreply@docu.com'}>`,
        to,
        subject,
        text,
        html
    });
    
    return { message: 'Email sent successfully', messageId: info.messageId };
};

module.exports = sendEmailHandler;