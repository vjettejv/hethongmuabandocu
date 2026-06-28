import { useState } from 'react';

function Chat() {
    const [contacts, setContacts] = useState([]);
    return (
        <div className="chat-container">
            <aside className="chat-sidebar">
                {contacts.map(c => <div key={c.id}>{c.username}</div>)}
            </aside>
        </div>
    );
}
export default Chat;