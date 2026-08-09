import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  HelpCircle,
  Scale,
  FileText,
  Bot,
  Stethoscope,
  ClipboardList,
  LogOut,
} from 'lucide-react';
import { useSessionStore } from '@/store/session';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/Button';

const NAV = [
  { to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/admin/questions', label: 'Questions', icon: HelpCircle },
  { to: '/admin/rules', label: 'Rules', icon: Scale },
  { to: '/admin/documents', label: 'Documents', icon: FileText },
  { to: '/admin/ai-logs', label: 'AI logs', icon: Bot },
  { to: '/admin/doctors', label: 'Doctors', icon: Stethoscope },
  { to: '/admin/reports', label: 'Reports', icon: ClipboardList },
];

export function AdminLayout() {
  const doctor = useSessionStore((s) => s.doctor);
  const logout = useSessionStore((s) => s.logout);
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="container-page flex h-14 items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <img src="/niepmd-logo.png" alt="" className="h-8 w-auto" />
            <div>
              <p className="text-sm font-semibold text-slate-900">NIEPMD Admin</p>
              <p className="text-xs text-slate-500">{doctor?.email || 'Staff console'}</p>
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              logout();
              navigate('/admin/login');
            }}
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </header>
      <div className="container-page grid gap-6 py-6 lg:grid-cols-[220px_1fr]">
        <nav className="flex flex-row gap-1 overflow-x-auto lg:flex-col">
          {NAV.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-sm font-medium',
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:bg-white hover:text-brand-700',
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <main className="min-w-0">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
