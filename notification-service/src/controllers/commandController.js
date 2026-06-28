const sendEmailHandler = require('../commands/sendEmailHandler');

const sendEmail = async (req, res) => {
    try {
        const result = await sendEmailHandler(req.body);
        res.status(200).json(result);
    } catch (error) {
        console.error('Email error:', error);
        res.status(500).json({ error: error.message });
    }
};

module.exports = { sendEmail };