import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
import { Button, LinkButton } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { recommendationsApi, sessionsApi, type SessionSummary } from '@/lib/api';
import { useSessionStore } from '@/store/session';

export function SummaryPage() {
  const navigate = useNavigate();
  const sessionId = useSessionStore((s) => s.sessionId);
  const setAnswers = useSessionStore((s) => s.setAnswers);
  const setRecommendations = useSessionStore((s) => s.setRecommendations);
  const [summary, setSummary] = useState<SessionSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      navigate('/chat/category', { replace: true });
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await sessionsApi.summary(sessionId);
        if (cancelled) return;
        setSummary(data);
        setAnswers(data.answers);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Failed to load summary');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId, navigate, setAnswers]);

  async function continueToResults() {
    if (!sessionId) return;
    setEvaluating(true);
    try {
      const rec = await recommendationsApi.evaluate(sessionId);
      setRecommendations(rec);
      navigate('/results/recommendations');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not evaluate recommendations');
    } finally {
      setEvaluating(false);
    }
  }

  return (
    <div className="container-page max-w-2xl py-10">
      <ProgressStepper current="summary" />
      <h1 className="text-2xl font-bold text-slate-900">Review your answers</h1>
      <p className="mt-2 text-slate-600">
        Please check these details. If something looks wrong, go back and restart the questionnaire
        for this visit.
      </p>

      {loading && <p className="mt-8 text-sm text-slate-500">Loading summary…</p>}

      {summary && (
        <div className="mt-8 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Visit details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-1 text-sm text-slate-600">
              <p>
                <span className="font-medium text-slate-800">Patient:</span> {summary.patient.name},{' '}
                {summary.patient.age}
              </p>
              {summary.category && (
                <p>
                  <span className="font-medium text-slate-800">Category:</span> {summary.category.name}
                </p>
              )}
              {summary.condition && (
                <p>
                  <span className="font-medium text-slate-800">Condition:</span>{' '}
                  {summary.condition.name}
                </p>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Answers</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {summary.answers.map((a) => (
                <div key={`${a.question_id}-${a.answered_at}`} className="rounded-xl bg-slate-50 p-3">
                  <p className="text-sm font-medium text-slate-800">
                    {a.question_text || a.question_key}
                  </p>
                  <p className="mt-1 text-sm text-brand-700">{a.answer_label}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3">
            <Button type="button" onClick={continueToResults} disabled={evaluating}>
              {evaluating ? 'Evaluating…' : 'See recommended tests'}
            </Button>
            <LinkButton to="/chat/category" variant="secondary">
              Correct / restart pathway
            </LinkButton>
            <Link
              to="/contact"
              className="inline-flex items-center text-sm font-medium text-brand-600 hover:underline"
            >
              Contact clinic for corrections
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
