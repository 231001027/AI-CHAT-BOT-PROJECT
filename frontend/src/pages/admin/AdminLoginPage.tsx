import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { Eye, EyeOff, Shield } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { authApi } from '@/lib/api';
import { loginSchema, type LoginForm } from '@/lib/schemas';
import { useSessionStore } from '@/store/session';

export function AdminLoginPage() {
  const navigate = useNavigate();
  const setAuth = useSessionStore((s) => s.setAuth);
  const [showPassword, setShowPassword] = useState(false);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: '', password: '' },
  });

  async function onSubmit(data: LoginForm) {
    try {
      const res = await authApi.login(data.email.trim(), data.password);
      setAuth(res.access_token, res.doctor);
      toast.success(`Welcome, ${res.doctor.name}`);
      navigate('/admin/dashboard');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Login failed. Check email and password.');
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-b from-brand-50 to-white px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <img src="/niepmd-logo.png" alt="NIEPMD" className="mx-auto h-14 w-auto" />
          <CardTitle>Admin login</CardTitle>
          <p className="text-sm text-slate-500">
            Sign in with your staff email ID and password.
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="email">Email ID</Label>
              <Input
                id="email"
                type="email"
                placeholder="admin@niepmd.gov.in"
                autoComplete="username"
                {...register('email')}
              />
              {errors.email && <p className="text-xs text-red-600">{errors.email.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter password"
                  autoComplete="current-password"
                  className="pr-10"
                  {...register('password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-slate-500 hover:text-slate-700"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password.message}</p>
              )}
            </div>
            <Button type="submit" className="w-full" disabled={isSubmitting}>
              <Shield size={16} />
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Patient?{' '}
            <Link to="/login" className="font-medium text-brand-700 hover:underline">
              Patient login
            </Link>
            {' · '}
            <Link to="/" className="font-medium text-brand-700 hover:underline">
              Back home
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
