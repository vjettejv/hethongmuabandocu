const { Sequelize } = require('sequelize');
const { Message } = require('../models');

const getContactsHandler = async (userId) => {
    return [];
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