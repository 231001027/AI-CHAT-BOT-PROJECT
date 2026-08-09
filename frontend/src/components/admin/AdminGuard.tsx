import { Navigate, Outlet } from 'react-router-dom';
import { useSessionStore } from '@/store/session';

export function AdminGuard() {
  const token = useSessionStore((s) => s.authToken);
  if (!token) return <Navigate to="/admin/login" replace />;
  return <Outlet />;
}
