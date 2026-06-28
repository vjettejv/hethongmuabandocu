const { Sequelize } = require('sequelize');
const { Message } = require('../models');

const getContactsHandler = async (userId) => {
    const messages = await Message.findAll({
        where: {
            [Sequelize.Op.or]: [{ senderId: userId }, { receiverId: userId }]
        },
        order: [['createdAt', 'DESC']]
    });

    const contactsMap = {};
    for (const msg of messages) {
        const contactId = msg.senderId === userId ? msg.receiverId : msg.senderId;
        if (!contactsMap[contactId]) {
            contactsMap[contactId] = { id: contactId, lastMessage: msg };
        }
    }
    
    return Object.values(contactsMap);
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