import { useNavigate } from 'react-router-dom';
import { User, Baby, Users } from 'lucide-react';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import type { UserType } from '@/lib/api';
import { useSessionStore } from '@/store/session';

const OPTIONS: { value: UserType; title: string; desc: string; icon: typeof User }[] = [
  { value: 'myself', title: 'Myself', desc: 'I am seeking help for my own hearing or ear concerns.', icon: User },
  { value: 'my_child', title: 'My Child', desc: 'I am a parent or guardian registering a child under 13.', icon: Baby },
  { value: 'someone_else', title: 'Someone Else', desc: 'I am helping a family member, friend, or patient.', icon: Users },
];

export function RelationshipPage() {
  const navigate = useNavigate();
  const setRelationship = useSessionStore((s) => s.setRelationship);
  const setSessionId = useSessionStore((s) => s.setSessionId);
  const setCategory = useSessionStore((s) => s.setCategory);
  const setCondition = useSessionStore((s) => s.setCondition);
  const setAnswers = useSessionStore((s) => s.setAnswers);
  const setRecommendations = useSessionStore((s) => s.setRecommendations);
  const setReport = useSessionStore((s) => s.setReport);

  function choose(value: UserType) {
    // Keep logged-in patient; clear only in-progress Take Test state.
    setSessionId(null);
    setCategory(null);
    setCondition(null);
    setAnswers([]);
    setRecommendations(null);
    setReport(null);
    setRelationship(value);
    navigate('/register');
  }

  return (
    <div className="container-page max-w-3xl py-10">
      <ProgressStepper current="register" />
      <h1 className="text-2xl font-bold text-slate-900 sm:text-3xl">Who needs care today?</h1>
      <p className="mt-2 text-slate-600">This helps us choose the right screening pathway.</p>
      <div className="mt-8 grid gap-4 sm:grid-cols-3">
        {OPTIONS.map(({ value, title, desc, icon: Icon }) => (
          <button key={value} type="button" onClick={() => choose(value)} className="text-left">
            <Card className="h-full transition hover:border-brand-300 hover:shadow-card">
              <CardHeader>
                <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
                  <Icon className="h-5 w-5" />
                </div>
                <CardTitle>{title}</CardTitle>
                <CardDescription>{desc}</CardDescription>
              </CardHeader>
              <CardContent />
            </Card>
          </button>
        ))}
      </div>
    </div>
  );
}
