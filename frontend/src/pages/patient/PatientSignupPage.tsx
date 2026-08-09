import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { toast } from 'sonner';
import { UserPlus } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { patientsApi } from '@/lib/api';
import { useSessionStore } from '@/store/session';

const patientSignupSchema = z
  .object({
    user_id: z.string().max(40).optional(),
    password: z
      .string()
      .min(8, 'Enter date of birth as DD/MM/YYYY or YYYY-MM-DD')
      .max(32),
  })
  .superRefine((data, ctx) => {
    const id = data.user_id?.trim();
    if (id && !/^\d+\/\d{4}$/.test(id)) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ['user_id'],
        message: 'User ID must look like 123/2026 (or leave blank to auto-assign)',
      });
    }
  });

type PatientSignupForm = z.infer<typeof patientSignupSchema>;

export function PatientSignupPage() {
  const navigate = useNavigate();
  const resetClinical = useSessionStore((s) => s.resetClinical);
  const setPatient = useSessionStore((s) => s.setPatient);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PatientSignupForm>({
    resolver: zodResolver(patientSignupSchema),
    defaultValues: { user_id: '', password: '' },
  });

  async function onSubmit(data: PatientSignupForm) {
    try {
      const patient = await patientsApi.signup({
        user_id: data.user_id?.trim() || null,
        password: data.password.trim(),
        relationship: 'myself',
        department: 'audiology',
        consent_given: false,
        consent_by: null,
      });
      resetClinical();
      setPatient(patient);
      toast.success(
        patient.user_code
          ? `Account created — save your User ID: ${patient.user_code}`
          : 'Account created',
      );
      navigate('/register/relationship');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Sign up failed');
    }
  }

  return (
    <div className="container-page flex min-h-[70vh] items-center justify-center py-12">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <img src="/niepmd-logo.png" alt="NIEPMD" className="mx-auto h-14 w-auto" />
          <CardTitle>Create patient account</CardTitle>
          <p className="text-sm text-slate-500">
            Sign up with your date of birth. Leave User ID blank to get one assigned.
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="user_id">User ID (optional)</Label>
              <Input
                id="user_id"
                placeholder="Leave blank to auto-assign"
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
                autoComplete="bday"
                {...register('password')}
              />
              {errors.password && (
                <p className="text-xs text-red-600">{errors.password.message}</p>
              )}
              <p className="text-xs text-slate-500">
                This date becomes your login password.
              </p>
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              <UserPlus size={16} />
              {isSubmitting ? 'Creating…' : 'Sign up'}
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-500">
            Already have an account?{' '}
            <Link to="/login" className="font-medium text-brand-700 hover:underline">
              Sign in
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
