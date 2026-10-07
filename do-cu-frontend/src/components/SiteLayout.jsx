import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';
import { io } from 'socket.io-client';
import { serverOrigin } from '../services/api';
import { clearSession } from '../services/session';
import useSession from '../hooks/useSession';
import Swal from 'sweetalert2';

export default function SiteLayout() {
    const navigate = useNavigate();
    const location = useLocation();
    const session = useSession();
    const [socket, setSocket] = useState(null);
    const handleLogout = () => { clearSession(); navigate('/', { replace: true }); };
    useEffect(() => {
        if (!session.isAuthenticated || !session.userId) { setSocket(null); return; }
        const connection = io(serverOrigin, { reconnection: true });
        const join = () => connection.emit('join_user_room', session.userId);
        const notify = data => {
            window.dispatchEvent(new CustomEvent('new_notification', { detail: data }));
            Swal.fire({ toast: true, position: 'top-end', icon: 'info', title: data.title || 'Thông báo',
                text: data.message, showConfirmButton: false, timer: 5000, timerProgressBar: true });
        };
        connection.on('connect', join);
        connection.on('receive_notification', notify);
        setSocket(connection);
        return () => {
            connection.off('connect', join);
            connection.off('receive_notification', notify);
            connection.disconnect();
        };
    }, [session.isAuthenticated, session.userId]);
    return <div className="app-shell">
        <Navbar session={session} currentPath={location.pathname} onLogout={handleLogout} />
        <main className="app-main"><Outlet context={{ session, socket }} /></main>
        <Footer />
    </div>;
}
