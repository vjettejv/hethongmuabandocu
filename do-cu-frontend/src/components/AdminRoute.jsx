import { Navigate, Outlet, useOutletContext } from 'react-router-dom';
import useSession from '../hooks/useSession';

export default function AdminRoute() {
  const session = useSession();
  const context = useOutletContext();
  if (!session.isAuthenticated) return <Navigate to="/login" state={{ from: '/admin' }} replace />;
  if (!session.isAdmin) return <Navigate to="/" replace />;
  return <Outlet context={context} />;
}
