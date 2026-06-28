import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useMemo, useState } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import { io } from 'socket.io-client';
import { serverOrigin } from '../services/api';
import Swal from 'sweetalert2';

function getSession() {
  const token = localStorage.getItem('token');
  const userId = localStorage.getItem('userId');
  const userRoleId = localStorage.getItem('userRoleId');
  return {
    token,
    userId: userId ? Number(userId) : null,
    userRoleId: userRoleId ? userRoleId.toString() : null,
    isAuthenticated: !!token,
    isAdmin: userRoleId?.toString() === '2',
  };
}

export default function SiteLayout() {
  const navigate = useNavigate();
  const location = useLocation();
  const [sessionTick, setSessionTick] = useState(0);

  const session = useMemo(() => {
    sessionTick;
    return getSession();
  }, [sessionTick]);

  useEffect(() => {
    const onStorage = () => setSessionTick((x) => x + 1);
    window.addEventListener('storage', onStorage);
    return () => window.removeEventListener('storage', onStorage);
  }, []);

  const handleLogout = () => {
    localStorage.clear();
    setSessionTick((x) => x + 1);
    navigate('/', { replace: true });
  };

  // Global Real-time Notifications
  useEffect(() => {
    if (!session.isAuthenticated || !session.userId) return;

    // Connect to message-service via Socket.IO
    const socket = io(serverOrigin, {
      reconnection: true,
    });

    socket.on('connect', () => {
      socket.emit('join_user_room', session.userId);
    });

    // Listen for system notifications (e.g. post approved)
    socket.on('receive_notification', (data) => {
      // Dispatch event to Navbar to update the bell icon count
      window.dispatchEvent(new CustomEvent('new_notification', { detail: data }));
      
      Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'info',
        title: data.title || 'Thông báo',
        text: data.message,
        showConfirmButton: false,
        timer: 5000,
        timerProgressBar: true,
      });
    });

    // Listen for new chat messages globally
    socket.on('receive_message', (msg) => {
      // Don't show toast if we sent it ourselves
      if (msg.senderId === session.userId) return;

      // Check current URL directly to avoid re-running useEffect
      const currentPath = window.location.pathname;
      const currentSearch = new URLSearchParams(window.location.search);
      const isChattingWithSender = currentPath.startsWith('/chat') && 
          currentSearch.get('to') === String(msg.senderId);
          
      if (!isChattingWithSender) {
        Swal.fire({
          toast: true,
          position: 'bottom-end',
          icon: 'success',
          title: 'Có tin nhắn mới!',
          text: msg.content.length > 30 ? msg.content.substring(0, 30) + '...' : msg.content,
          showConfirmButton: false,
          timer: 4000,
        });
      }
    });

    return () => socket.disconnect();
  }, [session.isAuthenticated, session.userId]);

  return (
    <div className="app-shell">
      <Navbar session={session} currentPath={location.pathname} onLogout={handleLogout} />

      <main className="app-main">
        <Outlet />
      </main>

      <Footer />

      {/* Floating Chat Button - Only show if logged in and not on chat or admin pages */}
      {session.isAuthenticated && !location.pathname.startsWith('/chat') && !location.pathname.startsWith('/admin') && (
        <button 
          className="floating-chat-btn" 
          onClick={() => navigate('/chat')}
          aria-label="Mở hộp thoại chat"
        >
          <svg viewBox="0 0 24 24" width="24" height="24" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path>
          </svg>
          <span className="floating-chat-text">Chat</span>
        </button>
      )}
    </div>
  );
}

