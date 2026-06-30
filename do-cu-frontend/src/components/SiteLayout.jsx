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
    return getSession();
  }, [sessionTick]);

  const handleLogout = () => {
    localStorage.clear();
    setSessionTick((x) => x + 1);
    navigate('/', { replace: true });
  };

  useEffect(() => {
    if (!session.isAuthenticated || !session.userId) return;

    const socket = io(serverOrigin, {
      reconnection: true,
    });

    socket.on('connect', () => {
      socket.emit('join_user_room', session.userId);
    });

    socket.on('receive_notification', (data) => {
      window.dispatchEvent(new CustomEvent('new_notification', { detail: data }));
      Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'info',
        title: data.title || 'ThÃ´ng bÃ¡o',
        text: data.message,
        showConfirmButton: false,
        timer: 5000,
        timerProgressBar: true,
      });
    });
    // Missing socket.disconnect() in cleanup
  }, [session.isAuthenticated, session.userId]);

  return (
    <div className="app-shell">
      <Navbar session={session} currentPath={location.pathname} onLogout={handleLogout} />
      <main className="app-main">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}