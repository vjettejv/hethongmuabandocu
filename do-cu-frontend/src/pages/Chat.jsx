import { useState, useEffect, useRef } from 'react';
import { useOutletContext, useSearchParams } from 'react-router-dom';
import api from '../services/api';
import { errorMessage, listData, mergeMessage } from '../services/contracts';
import Page, { ErrorNotice } from '../components/Page';

export default function Chat() {
    const { session, socket } = useOutletContext();
    const [params, setParams] = useSearchParams();
    const parsed = Number(params.get('to'));
    const peer = Number.isInteger(parsed) && parsed > 0 && parsed !== session.userId ? parsed : null;
    const currentPeer = useRef(peer);
    currentPeer.current = peer;
    const [contacts, setContacts] = useState([]);
    const [messages, setMessages] = useState([]);
    const [draft, setDraft] = useState('');
    const [busy, setBusy] = useState(false);
    const [loading, setLoading] = useState(false);
    const [contactLoading, setContactLoading] = useState(true);
    const [contactError, setContactError] = useState('');
    const [error, setError] = useState('');
    const [contactTick, setContactTick] = useState(0);
    const [historyTick, setHistoryTick] = useState(0);
    const [connected, setConnected] = useState(false);
    const end = useRef(null);

    useEffect(() => {
        const controller = new AbortController();
        setContactLoading(true); setContactError('');
        api.get('/messages/contacts', { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setContacts(listData(response));
        }).catch(failure => { if (!controller.signal.aborted) setContactError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setContactLoading(false); });
        return () => controller.abort();
    }, [contactTick, session.userId]);

    useEffect(() => {
        setMessages([]); setDraft(''); setError('');
    }, [peer]);
    useEffect(() => {
        if (!peer) { setLoading(false); return; }
        const controller = new AbortController();
        setLoading(true); setError('');
        api.get(`/messages/${peer}`, { signal: controller.signal }).then(response => {
            if (!controller.signal.aborted) setMessages(previous => previous.reduce(mergeMessage, listData(response)));
        }).catch(failure => { if (!controller.signal.aborted) setError(errorMessage(failure)); })
            .finally(() => { if (!controller.signal.aborted) setLoading(false); });
        return () => controller.abort();
    }, [peer, historyTick]);

    useEffect(() => {
        if (!socket) { setConnected(false); return; }
        const connect = () => { setConnected(true); setHistoryTick(value => value + 1); setContactTick(value => value + 1); };
        const disconnect = () => setConnected(false);
        const receive = message => {
            if (![Number(message.senderId), Number(message.receiverId)].includes(session.userId)) return;
            const other = Number(message.senderId) === session.userId ? Number(message.receiverId) : Number(message.senderId);
            if (other === currentPeer.current) setMessages(rows => mergeMessage(rows, message));
            setContactTick(value => value + 1);
        };
        setConnected(socket.connected);
        socket.on('connect', connect); socket.on('disconnect', disconnect); socket.on('receive_message', receive);
        return () => { socket.off('connect', connect); socket.off('disconnect', disconnect); socket.off('receive_message', receive); };
    }, [socket, session.userId]);

    useEffect(() => { end.current?.scrollIntoView({ block: 'nearest' }); }, [messages.length]);
    const submit = async event => {
        event.preventDefault();
        if (!peer || busy || !draft.trim()) return;
        const recipient = peer;
        const content = draft.trim();
        setBusy(true); setError('');
        try {
            const response = await api.post('/messages', { receiverId: recipient, content });
            if (currentPeer.current === recipient) {
                setMessages(rows => mergeMessage(rows, response.data.data));
                setDraft(value => value.trim() === content ? '' : value);
            }
            setContactTick(value => value + 1);
        } catch (failure) { if (currentPeer.current === recipient) setError(errorMessage(failure, 'Không thể gửi tin nhắn.')); }
        finally { setBusy(false); }
    };
    const selected = contacts.find(contact => Number(contact.id) === peer);
    const name = selected?.user?.fullName || selected?.user?.username || `Người dùng #${peer}`;
    const ordered = [...messages].sort((a,b) => Date.parse(a.createdAt) - Date.parse(b.createdAt) || a.id - b.id);
    return <Page title="Tin nhắn"><div className="chat-shell">
        <aside className="card card-pad" aria-label="Danh sách trò chuyện">
            <h2 className="toolbar-title">Trò chuyện</h2><ErrorNotice error={contactError} />
            <button className="btn btn-ghost" onClick={() => setContactTick(value => value + 1)}>Tải lại danh sách</button>
            {contactLoading && <p className="hint" role="status">Đang tải liên hệ…</p>}
            {!contactLoading && contacts.length === 0 && <p className="hint">Chưa có cuộc trò chuyện. Mở sản phẩm và chọn Chat nhanh để bắt đầu.</p>}
            <div className="chat-list">{contacts.map(contact => <button className={Number(contact.id) === peer ? 'chat-peer active' : 'chat-peer'} key={contact.id}
                onClick={() => setParams({ to: String(contact.id) })}>
                <strong>{contact.user?.fullName || contact.user?.username || `Người dùng #${contact.id}`}</strong>
                <div className="hint chat-preview">{contact.lastMessage?.content}</div>
            </button>)}</div>
        </aside>
        <section className="card card-pad chat-panel" aria-label="Nội dung trò chuyện">
            {!peer ? <p role="status">Chọn một cuộc trò chuyện để xem và gửi tin nhắn.</p> : <>
                <div className="toolbar"><h2 className="toolbar-title">{name}</h2><span className="hint">{connected ? 'Đã kết nối' : 'Đang kết nối lại…'}</span>
                    <button className="btn btn-ghost" onClick={() => setHistoryTick(value => value + 1)}>Tải lại tin nhắn</button></div>
                <ErrorNotice error={error} />
                <div className="chat-messages" aria-label="Lịch sử tin nhắn" role="log" aria-live="polite">
                    {loading && <p role="status">Đang tải tin nhắn…</p>}
                    {!loading && ordered.length === 0 && <p className="hint">Chưa có tin nhắn.</p>}
                    {ordered.map(message => <div key={message.id} className={Number(message.senderId) === session.userId ? 'bubble-row me' : 'bubble-row'}>
                        <div className={Number(message.senderId) === session.userId ? 'bubble me' : 'bubble'}>{message.content}</div>
                    </div>)}<div ref={end} />
                </div>
                <form className="chat-inputbar" onSubmit={submit}>
                    <input className="input" aria-label="Nội dung tin nhắn" placeholder="Nhập tin nhắn…" value={draft} onChange={event => setDraft(event.target.value)} required />
                    <button className="btn btn-primary" type="submit" disabled={busy || loading || !draft.trim()}>{busy ? 'Đang gửi…' : 'Gửi'}</button>
                </form>
            </>}
        </section>
    </div></Page>;
}
