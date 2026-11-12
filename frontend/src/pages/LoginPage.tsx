import { FormEvent, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Eye, EyeOff, LogIn } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { authenticateStaff, signInStaff } from '@/lib/staffAuth';

export function LoginPage() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const submittedId = String(data.get('userId') ?? userId);
    const submittedPassword = String(data.get('password') ?? password);
    const account = authenticateStaff(submittedId, submittedPassword);
    if (!account) {
      setError('User ID or password is not recognised.');
      return;
    }
    signInStaff(account);
    navigate('/');
  }

  return (
    <div className="container-page flex min-h-[70vh] items-center justify-center py-12">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-soft"
      >
        <p className="text-xs font-semibold uppercase tracking-wide text-brand-600">NIEPMD staff</p>
        <h1 className="mt-2 text-2xl font-bold text-slate-900">Sign in</h1>
        <p className="mt-2 text-sm text-slate-600">Use your department user ID and password.</p>

        <label className="mt-6 block text-sm font-medium text-slate-700" htmlFor="user-id">
          User ID
        </label>
        <input
          id="user-id"
          name="userId"
          autoComplete="username"
          value={userId}
          onChange={(event) => {
            setUserId(event.target.value);
            setError('');
          }}
          className="mt-1.5 w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none ring-brand-500 focus:ring-2"
          placeholder="name@niepmdshc"
          required
        />

        <label className="mt-4 block text-sm font-medium text-slate-700" htmlFor="password">
          Password
        </label>
        <div className="relative mt-1.5">
          <input
            id="password"
            name="password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="current-password"
            value={password}
            onChange={(event) => {
              setPassword(event.target.value);
              setError('');
            }}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 pr-12 text-sm outline-none ring-brand-500 focus:ring-2"
            required
          />
          <button
            type="button"
            onClick={() => setShowPassword((visible) => !visible)}
            className="absolute inset-y-0 right-0 flex w-12 items-center justify-center text-slate-500 hover:text-slate-800"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
          </button>
        </div>

        {error && (
          <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
            {error}
          </p>
        )}

        <Button type="submit" className="mt-6 w-full">
          <LogIn size={16} />
          Sign in
        </Button>
      </form>
    </div>
  );
}
