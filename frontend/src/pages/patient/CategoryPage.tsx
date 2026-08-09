import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import {
  catalogApi,
  sessionsApi,
  type Category,
  type Condition,
  type FlowType,
} from '@/lib/api';
import { useSessionStore } from '@/store/session';

export function CategoryPage() {
  const navigate = useNavigate();
  const patient = useSessionStore((s) => s.patient);
  const setCategory = useSessionStore((s) => s.setCategory);
  const setCondition = useSessionStore((s) => s.setCondition);
  const setSessionId = useSessionStore((s) => s.setSessionId);
  const setAnswers = useSessionStore((s) => s.setAnswers);

  const [categories, setCategories] = useState<Category[]>([]);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<Category | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);

  const flowType: FlowType =
    patient?.profile?.flow_type ||
    (patient && patient.age < 13 ? 'child' : 'adult');
  const department = patient?.profile?.department || undefined;

  useEffect(() => {
    if (!patient) {
      navigate('/register/relationship', { replace: true });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const cats = await catalogApi.categories(flowType, department);
        if (!cancelled) setCategories(cats);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Failed to load categories');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [patient, flowType, department, navigate]);

  async function pickCategory(cat: Category) {
    setSelectedCategory(cat);
    setCategory(cat);
    setCondition(null);
    try {
      const list = await catalogApi.conditions(cat.id);
      setConditions(list);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Failed to load conditions');
    }
  }

  async function startSession(cond: Condition) {
    if (!patient) return;
    setStarting(true);
    try {
      setCondition(cond);
      const state = await sessionsApi.start(patient.id, cond.id);
      setSessionId(state.session_id);
      setAnswers([]);
      navigate('/chat/questionnaire');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not start session');
    } finally {
      setStarting(false);
    }
  }

  return (
    <div className="container-page max-w-3xl py-10">
      <ProgressStepper current="category" />
      <h1 className="text-2xl font-bold text-slate-900">What brings you in today?</h1>
      <p className="mt-2 text-slate-600">
        Showing {flowType} pathway categories
        {patient ? ` for ${patient.name}` : ''}.
      </p>

      {loading && <p className="mt-8 text-sm text-slate-500">Loading categories…</p>}

      {!loading && !selectedCategory && (
        <div className="mt-8 grid gap-4">
          {categories.map((cat) => (
            <button key={cat.id} type="button" onClick={() => pickCategory(cat)} className="text-left">
              <Card className="transition hover:border-brand-300 hover:shadow-card">
                <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
                  <div>
                    <CardTitle className="text-base">{cat.name}</CardTitle>
                    <CardDescription className="mt-1">{cat.description}</CardDescription>
                  </div>
                  <Badge variant="outline">{cat.flow_type}</Badge>
                </CardHeader>
              </Card>
            </button>
          ))}
        </div>
      )}

      {selectedCategory && (
        <div className="mt-8 space-y-4">
          <div className="flex items-center justify-between gap-3">
            <h2 className="text-lg font-semibold text-slate-900">
              Choose a condition — {selectedCategory.name}
            </h2>
            <Button type="button" variant="ghost" size="sm" onClick={() => setSelectedCategory(null)}>
              Back
            </Button>
          </div>
          <div className="grid gap-3">
            {conditions.map((cond) => (
              <Card key={cond.id}>
                <CardHeader>
                  <CardTitle className="text-base">{cond.name}</CardTitle>
                  <CardDescription>{cond.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button
                    type="button"
                    size="sm"
                    disabled={starting}
                    onClick={() => startSession(cond)}
                  >
                    {starting ? 'Starting…' : 'Start questionnaire'}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
