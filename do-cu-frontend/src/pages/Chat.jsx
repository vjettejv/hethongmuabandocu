import { useEffect, useMemo, useRef, useState } from 'react';
import api, { serverOrigin } from '../services/api';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { io } from 'socket.io-client';
import './Chat.css';

function Chat() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const [messages, setMessages] = useState([]);
    const [text, setText] = useState('');
    const [receiver, setReceiver] = useState(null);
    const [contacts, setContacts] = useState([]);
    
    // Auto-fill message from URL (e.g. from PostDetail)
    useEffect(() => {
        const msg = searchParams.get('msg');
        if (msg) {
            setText(msg);
        }
    }, [searchParams]);

    const messagesEndRef = useRef(null); // Dùng để tự động cuộn xuống cuối
    const socketRef = useRef(null); // Ref để lưu Socket.IO connection

    // Lấy ID của người đang đăng nhập (để biết tin nhắn nào là của mình)
    const currentUserId = parseInt(localStorage.getItem('userId')) || 0;
    const isAdmin = localStorage.getItem('userRoleId') === '2';
    
    const receiverId = useMemo(() => {
        const to = searchParams.get('to');
        const parsed = to ? Number(to) : NaN;
        if (Number.isFinite(parsed) && parsed > 0) return parsed;
        
        // Default receiver: Admin shouldn't default to 4 (themselves).
        return isAdmin ? null : 4;
    }, [searchParams, isAdmin]);
    
    const receiverLabel = useMemo(() => {
        if (receiverId === 4) return 'Hỗ trợ';
        const fullName = receiver?.fullName?.trim();
        if (fullName) return fullName;
        const username = receiver?.username?.trim();
        if (username) return username;
        return 'Người dùng';
    }, [receiverId, receiver]);

    // Tải danh sách "người đã liên hệ" (inbox)
    useEffect(() => {
        let mounted = true;
        api
            .get('/messages/contacts')
            .then((res) => {
                const data = res.data?.data || res.data || [];
                if (!mounted) return;
                setContacts(Array.isArray(data) ? data : []);
            })
            .catch((err) => {
                console.error('Lỗi tải danh sách liên hệ:', err);
                if (!mounted) return;
                setContacts([]);
            });

        return () => {
            mounted = false;
        };
    }, []);

    // 🔌 Kết nối Socket.IO và setup real-time chat
    useEffect(() => {
        // Khởi tạo kết nối Socket.IO
        const socket = io(serverOrigin, {
            reconnection: true,
            reconnectionDelay: 1000,
            reconnectionDelayMax: 5000,
            reconnectionAttempts: 5
        });

        socketRef.current = socket;

        socket.on('connect', () => {
            console.log('✅ Kết nối Socket.IO thành công');
            // Báo danh ID người dùng để server tạo "phòng riêng"
            if (currentUserId) {
                socket.emit('join_user_room', currentUserId);
                console.log(`👤 Đã join phòng: user_${currentUserId}`);
            }
        });

        socket.on('disconnect', () => {
            console.log('❌ Mất kết nối Socket.IO');
        });

        socket.on('connect_error', (error) => {
            console.error('Socket.IO lỗi kết nối:', error);
        });

        return () => {
            socket.disconnect();
            socketRef.current = null;
        };
    }, [currentUserId]);

    // Lắng nghe tin nhắn mới từ server (real-time)
    useEffect(() => {
        if (!socketRef.current) return;

        const handleReceiveMessage = (newMessage) => {
            console.log('Nhận tin nhắn từ server:', newMessage);
            // Chỉ thêm tin nhắn nếu nó thuộc về cuộc hội thoại hiện tại
            if (
                (newMessage.senderId === receiverId && newMessage.receiverId === currentUserId) ||
                (newMessage.senderId === currentUserId && newMessage.receiverId === receiverId)
            ) {
                setMessages(prev => {
                    if (prev.some(msg => msg.id === newMessage.id)) {
                        return prev; // bỏ qua nếu đã có
                    }
                    return [...prev, newMessage];
                });
            }
        };

        socketRef.current.on('receive_message', handleReceiveMessage);

        return () => {
            socketRef.current?.off('receive_message', handleReceiveMessage);
        };
    }, [receiverId, currentUserId]);

    // Tải lịch sử chat
    useEffect(() => {
        if (!receiverId) {
            setMessages([]);
            return;
        }
        api.get(`/messages/${receiverId}`)
            .then(res => setMessages(res.data.data || res.data || []))
            .catch(err => console.error("Lỗi tải tin nhắn:", err));
    }, [receiverId]);

    // Lấy thông tin người nhận để hiển thị tên thay vì ID
    useEffect(() => {
        if (!receiverId) {
            setReceiver(null);
            return;
        }
        api.get(`/users/${receiverId}`)
            .then(res => setReceiver(res.data.data || res.data || null))
            .catch(err => {
                console.error("Lỗi tải thông tin người nhận:", err);
                setReceiver(null);
            });
    }, [receiverId]);

    // Tự động cuộn xuống tin nhắn mới nhất mỗi khi mảng messages thay đổi
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const sendMessage = async () => {
        if (!text.trim()) return;
        const messageText = text.trim();
        setText('');

        try {
            // 1. Lưu tin nhắn vào DB qua API
            const response = await api.post('/messages', { receiverId, content: messageText });
            const savedMessage = response.data?.data;

            if (savedMessage) {
                setMessages(prev => {
                    if (prev.some(msg => msg.id === savedMessage.id)) {
                        return prev;
                    }
                    return [...prev, savedMessage];
                });
            }

            // Remove 'msg' from URL after sending to prevent pre-filling again on refresh
            if (searchParams.has('msg')) {
                const newParams = new URLSearchParams(searchParams);
                newParams.delete('msg');
                navigate(`/chat?${newParams.toString()}`, { replace: true });
            }

            // 2. Gửi tin nhắn qua Socket.IO để người nhận nhận được real-time
            if (socketRef.current && savedMessage) {
                socketRef.current.emit('send_message', {
                    senderId: currentUserId,
                    receiverId,
                    content: messageText
                });
                console.log('Tin nhắn đã gửi qua Socket.IO');
            }
        } catch (error) {
            console.error("Lỗi gửi tin nhắn:", error);
            // Có thể thêm báo lỗi nếu gửi xịt
        }
    };

    // Hàm bắt sự kiện nhấn phím Enter
    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    };

    // Hàm format timestamp
    const formatTime = (date) => {
        if (!date) return '';
        const d = new Date(date);
        const hours = String(d.getHours()).padStart(2, '0');
        const mins = String(d.getMinutes()).padStart(2, '0');
        return `${hours}:${mins}`;
    };

    // Hàm lấy initials từ tên
    const getInitials = (name = '', id = '') => {
        if (name.trim()) {
            const parts = name.trim().split(' ');
            return parts.map(p => p[0]).join('').substring(0, 2).toUpperCase();
        }
        return `U${id}`.substring(0, 2).toUpperCase();
    };

    return (
        <div className="chat-container">
            {/* ===== SIDEBAR: CONTACTS LIST ===== */}
            <div className="chat-sidebar">
                <div className="chat-sidebar-header">
                    <h2>Hộp thư</h2>
                    <p className="chat-sidebar-subtitle">Chọn người để chat</p>
                </div>

                <div className="chat-list-wrapper">
                    {/* Support Contact - Chỉ hiển thị cho user thường, không phải admin */}
                    {!isAdmin && (
                        <div
                            className={`chat-contact ${receiverId === 4 ? 'active' : ''}`}
                            role="button"
                            tabIndex={0}
                            onClick={() => navigate('/chat?to=4')}
                            onKeyDown={(e) => e.key === 'Enter' && navigate('/chat?to=4')}
                        >
                            <div className="chat-contact-avatar support">HT</div>
                            <div className="chat-contact-info">
                                <p className="chat-contact-name">Hỗ trợ</p>
                                <p className="chat-contact-preview">Nhắn tin cho admin</p>
                            </div>
                        </div>
                    )}

                    {/* User Contacts */}
                    {contacts.filter((c) => c?.user?.id && c.user.id !== 4).length > 0 ? (
                        contacts
                            .filter((c) => c?.user?.id && c.user.id !== 4)
                            .map((c) => {
                                const id = c.user.id;
                                const name = c.user.fullName?.trim() || c.user.username?.trim() || `User #${id}`;
                                const preview = c.lastMessage?.content || 'Không có tin nhắn';
                                const initials = getInitials(name, id);
                                return (
                                    <div
                                        key={id}
                                        className={`chat-contact ${receiverId === id ? 'active' : ''}`}
                                        role="button"
                                        tabIndex={0}
                                        onClick={() => navigate(`/chat?to=${id}`)}
                                        onKeyDown={(e) => e.key === 'Enter' && navigate(`/chat?to=${id}`)}
                                    >
                                        <div className="chat-contact-avatar">
                                            {initials}
                                            <div className="chat-contact-online"></div>
                                        </div>
                                        <div className="chat-contact-info">
                                            <p className="chat-contact-name">{name}</p>
                                            <p className="chat-contact-preview">{preview}</p>
                                        </div>
                                    </div>
                                );
                            })
                    ) : (
                        <div className="chat-empty-state">
                            <p>Chưa có người liên hệ</p>
                            <p>Bạn có thể nhắn tin từ trang chi tiết sản phẩm</p>
                        </div>
                    )}
                </div>
            </div>

            {/* ===== MAIN CHAT PANEL ===== */}
            <div className="chat-main">
                {/* Header */}
                <div className="chat-header">
                    <div className="chat-header-left">
                        <div className="chat-header-info">
                            <h3>{receiverLabel}</h3>
                            <p className="chat-header-status">
                                <span className="status-dot"></span>
                                Đang hoạt động
                            </p>
                        </div>
                    </div>
                    <div className="chat-header-actions">
                        <button
                            className="chat-header-btn"
                            onClick={() => {
                                if (receiverId) {
                                    api.get(`/messages/${receiverId}`)
                                        .then(res => setMessages(res.data.data || res.data || []))
                                        .catch(err => console.error("Lỗi tải tin nhắn:", err));
                                }
                            }}
                        >
                            Làm mới
                        </button>
                    </div>
                </div>

                {/* Messages Area */}
                <div className="chat-messages" aria-live="polite" aria-atomic="false">
                    {messages.length === 0 ? (
                        <div className="chat-empty-placeholder">
                            <p>Chưa có tin nhắn</p>
                            <p>Hãy gửi tin nhắn đầu tiên để bắt đầu cuộc trò chuyện</p>
                        </div>
                    ) : (
                        messages.map((m, idx) => {
                            const isMe = m.senderId === currentUserId;
                            const initials = getInitials(isMe ? 'Bạn' : receiverLabel, m.senderId);
                            return (
                                <div key={idx} className={`chat-message-group ${isMe ? 'me' : ''}`}>
                                    {!isMe && <div className="chat-message-avatar">{initials}</div>}
                                    <div className={`chat-message ${isMe ? 'me' : ''}`}>
                                        <div className={`chat-bubble ${isMe ? 'me' : ''}`}>
                                            {m.content}
                                        </div>
                                        <div className="chat-timestamp">
                                            {formatTime(m.createdAt || new Date())}
                                        </div>
                                    </div>
                                </div>
                            );
                        })
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="chat-inputbar">
                    <textarea
                        className="chat-input"
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={!receiverId}
                        placeholder={receiverId ? "Nhập tin nhắn (Shift+Enter để xuống dòng)..." : "Vui lòng chọn một người để bắt đầu trò chuyện"}
                        rows={1}
                        style={{ height: '40px', overflow: 'hidden' }}
                        onInput={(e) => {
                            e.target.style.height = 'auto';
                            e.target.style.height = Math.min(e.target.scrollHeight, 100) + 'px';
                        }}
                    />
                    <button
                        className="chat-send-btn"
                        onClick={sendMessage}
                        disabled={!text.trim() || !receiverId}
                        title="Gửi tin nhắn (Enter)"
                    >
                        Gửi
                    </button>
                </div>
            </div>
        </div>
    );
}

export default Chat;