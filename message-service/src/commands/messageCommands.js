const { Message } = require('../models');

const sendMessageHandler = async (senderId, receiverId, content, io) => {
    const msg = await Message.create({ senderId, receiverId, content });
    return msg;
};

module.exports = { sendMessageHandler };