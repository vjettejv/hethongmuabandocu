const { Message } = require('../models');

const sendMessageHandler = async (senderId, receiverId, content, io) => {
    const msg = await Message.create({ senderId, receiverId, content });
    
    // Notify receiver
    try {
        const authUrl = process.env.AUTH_SERVICE_URL || 'http://auth-service:3001';
        const notifUrl = process.env.NOTIFICATION_SERVICE_URL || 'http://notification-service:3006';
        const response = await fetch(\/\);
        if (response.ok) {
            const receiver = await response.json();
            if (receiver.email) {
                await fetch(\/email, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        to: receiver.email,
                        subject: 'Báº¡n cÃ³ tin nháº¯n má»›i trÃªn Äá»“ CÅ©',
                        text: Báº¡n vá»«a nháº­n Ä‘Æ°á»£c má»™t tin nháº¯n má»›i.\n\nNá»™i dung: \\n\nHÃ£y Ä‘Äƒng nháº­p Ä‘á»ƒ tráº£ lá»i!
                    })
                });
            }
        }
    } catch(e) { console.error('Notification failed', e.message); }
    
    // Emit via Socket
    if (io) io.to(user_\).emit('receive_message', msg);
    
    return msg;
};

module.exports = { sendMessageHandler };