const { sendMessageHandler } = require('../commands/messageCommands');
const { createNotificationHandler, markAllReadHandler } = require('../commands/notificationCommands');

const sendMessage = async (req, res) => {
    try {
        const { receiverId, content } = req.body;
        const msg = await sendMessageHandler(req.user.id, receiverId, content, req.app.get('io'));
        res.json({ data: msg });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const createNotification = async (req, res) => {
    try {
        const notif = await createNotificationHandler(req.body, req.app.get('io'));
        res.json({ success: true, data: notif });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const markAllRead = async (req, res) => {
    try {
        const result = await markAllReadHandler(req.user.id);
        res.json(result);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { sendMessage, createNotification, markAllRead };