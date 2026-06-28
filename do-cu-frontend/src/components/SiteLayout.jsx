import { Outlet } from 'react-router-dom';
import { useMemo, useState } from 'react';

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
  const [sessionTick, setSessionTick] = useState(0);
  const session = useMemo(() => {
    return getSession();
  }, [sessionTick]);

  return (
    <div>
      <Outlet />
    </div>
  );
}