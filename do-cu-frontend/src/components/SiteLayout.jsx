import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useMemo, useState } from 'react';
import Navbar from './Navbar';
import Footer from './Footer';

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