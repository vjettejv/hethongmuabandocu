const { Notification } = require('../models');

const getNotificationsHandler = async (userId) => {
    return await Notification.findAll({
        where: { userId },
        order: [['createdAt', 'DESC']],
        limit: 50
    });
};

module.exports = { getNotificationsHandler };