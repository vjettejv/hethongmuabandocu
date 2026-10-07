import { Navigate, Outlet, useLocation, useOutletContext } from 'react-router-dom';
import useSession from '../hooks/useSession';

export default function ProtectedRoute() {
  const session = useSession();
  const location = useLocation();
  const context = useOutletContext();
  if (!session.isAuthenticated) return <Navigate to="/login" state={{ from: location.pathname + location.search }} replace />;
  return <Outlet context={context} />;
}
