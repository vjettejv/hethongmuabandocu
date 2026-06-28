import { useState, useEffect } from 'react';
import { io } from 'socket.io-client';

function Chat() {
    const [messages, setMessages] = useState([]);
    useEffect(() => {
        const socket = io();
        socket.on('receive_message', (msg) => {
            setMessages(prev => [...prev, msg]);
        });
        return () => socket.disconnect();
    }, []);
    return (
        <div>Chat</div>
    );
}
export default Chat;