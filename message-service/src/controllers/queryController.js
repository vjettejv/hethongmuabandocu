const { getContactsHandler, getHistoryHandler } = require('../queries/messageQueries');
const { getNotificationsHandler } = require('../queries/notificationQueries');

const getContacts = async (req, res) => {
    try {
        const contacts = await getContactsHandler(req.user.id);
        res.json({ data: contacts });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const getHistory = async (req, res) => {
    try {
        const history = await getHistoryHandler(req.user.id, req.params.contactId);
        res.json({ data: history });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

const getNotifications = async (req, res) => {
    try {
        const notifs = await getNotificationsHandler(req.user.id);
        res.json({ data: notifs });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
};

module.exports = { getContacts, getHistory, getNotifications };