const { Message } = require('../models');

const sendMessageHandler = async (senderId, receiverId, content, io) => {
    const msg = await Message.create({ senderId, receiverId, content });
    
    // Emit via Socket
    if (io) io.to(`user_${receiverId}`).emit('receive_message', msg);
    
    return msg;
};

module.exports = { sendMessageHandler };