const { Sequelize } = require('sequelize');
const { Message } = require('../models');

const getContactsHandler = async (userId) => {
    const messages = await Message.findAll({
        where: {
            [Sequelize.Op.or]: [{ senderId: userId }, { receiverId: userId }]
        },
        order: [['createdAt', 'DESC']]
    });
    return messages;
};

const getHistoryHandler = async (userId, contactId) => {
    return await Message.findAll({
        where: {
            [Sequelize.Op.or]: [
                { senderId: userId, receiverId: contactId },
                { senderId: contactId, receiverId: userId }
            ]
        },
        order: [['createdAt', 'ASC']]
    });
};

module.exports = { getContactsHandler, getHistoryHandler };