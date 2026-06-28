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
    
    const contactsList = Object.values(contactsMap);
    
    for (let c of contactsList) {
        const response = await fetch(http://user-service:3000/\);
        if (response.ok) {
            const profile = await response.json();
            c.user = { id: c.id, fullName: profile.fullName, username: profile.fullName };
        }
    }
    return contactsList;
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