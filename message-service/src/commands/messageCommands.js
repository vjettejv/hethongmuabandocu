const { Message } = require('../models');

const sendMessageHandler = async (senderId, receiverId, content, io) => {
    const msg = await Message.create({ senderId, receiverId, content });
    
    // Notify receiver
    const authUrl = process.env.AUTH_SERVICE_URL || 'http://auth-service:3001';
    const notifUrl = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:3006';
    const response = await fetch(`${authUrl}/${receiverId}`);
    if (response.ok) {
        const receiver = await response.json();
        if (receiver.email) {
            await fetch(`${notifUrl}/email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    to: receiver.email,
                    subject: 'Bạn có tin nhắn mới trên Đồ Cũ',
                    text: `Bạn vừa nhận được một tin nhắn mới.\n\nNội dung: ${content}\n\nHãy đăng nhập để trả lời!`
                })
            });
        }
    }
    
    // Emit via Socket
    if (io) io.to(`user_${receiverId}`).emit('receive_message', msg);
    
    return msg;
};

module.exports = { sendMessageHandler };