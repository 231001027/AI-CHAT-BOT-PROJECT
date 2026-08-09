import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { LogIn } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { patientsApi } from '@/lib/api';
import { useSessionStore } from '@/store/session';

const patientLoginSchema = z.object({
  user_id: z
    .string()
    .min(3, 'Enter your User ID')
    .max(40, 'User ID is too long'),
  password: z
    .string()
    .min(8, 'Enter date of birth as DD/MM/YYYY or YYYY-MM-DD')
    .max(32),
});

type PatientLoginForm = z.infer<typeof patientLoginSchema>;

export function PatientLoginPage() {
  const navigate = useNavigate();
  const resetClinical = useSessionStore((s) => s.resetClinical);
  const setPatient = useSessionStore((s) => s.setPatient);
  const setRelationship = useSessionStore((s) => s.setRelationship);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PatientLoginForm>({
    resolver: zodResolver(patientLoginSchema),
    defaultValues: { user_id: '', password: '' },
  });

  async function onSubmit(data: PatientLoginForm) {
    try {
      const patient = await patientsApi.login({
        user_id: data.user_id.trim(),
        password: data.password.trim(),
      });
      resetClinical();
      setPatient(patient);
      if (patient.user_type) {
        setRelationship(patient.user_type);
      }
      toast.success(
        patient.user_code
          ? `Welcome back — User ID ${patient.user_code}`
          : 'Signed in successfully',
      );
      if (patient.profile?.flow_type) {
        navigate('/chat/category');
      } else {
        navigate('/register/relationship');
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Login failed. Check User ID and date of birth.');
    }
  }

  return (
    <div className="container-page flex min-h-[70vh] items-center justify-center py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <img src="/niepmd-logo.png" alt="NIEPMD" className="mx-auto h-14 w-auto" />
          <CardTitle>Patient login</CardTitle>
          <p className="text-sm text-slate-500">
            Sign in with your User ID and date of birth to continue Take Test.
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="user_id">User ID</Label>
              <Input
                id="user_id"
                placeholder="e.g. 123/2026"
                autoComplete="username"
                {...register('user_id')}
              />
              {errors.user_id && (
                <p className="text-xs text-red-600">{errors.user_id.message}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Date of birth</Label>
              <Input
                id="password"
                type="text"
                placeholder="DD/MM/YYYY or YYYY-MM-DD"
                autoComplete="current-password"
                {...register('password')}
              />
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password.message}</p>
              )}
              <p className="text-xs text-slate-500">
                Use the date of birth recorded at registration as your password.
              </p>
            </div>
            <Button type="submit" disabled={isSubmitting} className="w-full">
              <LogIn size={16} />
              {isSubmitting ? 'Signing in…' : 'Sign in'}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-500">
            New here?{' '}
            <Link to="/signup" className="font-medium text-brand-700 hover:underline">
              Sign up
            </Link>
            {' · '}
            <Link to="/register/relationship" className="font-medium text-brand-700 hover:underline">
              Take Test
            </Link>
            {' · '}
            <Link to="/admin/login" className="font-medium text-brand-700 hover:underline">
              Admin login
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
