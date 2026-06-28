import { Navigate, Outlet } from 'react-router-dom';

export default function AdminRoute() {
  const roleId = localStorage.getItem('userRoleId');
  if (roleId?.toString() !== '2') return <Navigate to="/" replace />;
  return <Outlet />;
}

