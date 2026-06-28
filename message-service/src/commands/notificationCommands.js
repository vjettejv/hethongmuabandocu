const { Notification } = require('../models');

const createNotificationHandler = async (data, io) => {
    const { receiverId, title, message, link } = data;
    const notif = await Notification.create({ userId: receiverId, title, message, link });
    
    if (io) io.to(`user_${receiverId}`).emit('receive_notification', notif);
    return notif;
};

const markAllReadHandler = async (userId) => {
    await Notification.update({ isRead: true }, { where: { userId, isRead: false } });
    return { success: true };
};

module.exports = { createNotificationHandler, markAllReadHandler };