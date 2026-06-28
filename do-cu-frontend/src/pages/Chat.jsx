import { useState } from 'react';

function Chat() {
    const [messages, setMessages] = useState([]);
    return (
        <div className="chat-container">
            <div className="chat-main">
                {messages.map((m, idx) => <div key={idx}>{m.content}</div>)}
            </div>
        </div>
    );
}
export default Chat;