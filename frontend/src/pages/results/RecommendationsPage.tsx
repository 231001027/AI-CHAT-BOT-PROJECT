import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
import { TestExplanationCard } from '@/components/shared/TestExplanationCard';
import { Button, LinkButton } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { recommendationsApi, reportsApi } from '@/lib/api';
import { useSessionStore } from '@/store/session';

export function RecommendationsPage() {
  const navigate = useNavigate();
  const sessionId = useSessionStore((s) => s.sessionId);
  const recommendations = useSessionStore((s) => s.recommendations);
  const setRecommendations = useSessionStore((s) => s.setRecommendations);
  const setReport = useSessionStore((s) => s.setReport);
  const [loading, setLoading] = useState(!recommendations);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      navigate('/chat/category', { replace: true });
      return;
    }
    if (recommendations) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        let rec;
        try {
          rec = await recommendationsApi.get(sessionId);
        } catch {
          rec = await recommendationsApi.evaluate(sessionId);
        }
        if (!cancelled) setRecommendations(rec);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Failed to load recommendations');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId, recommendations, navigate, setRecommendations]);

  async function generateReport() {
    if (!sessionId) return;
    setGenerating(true);
    try {
      const report = await reportsApi.generate(sessionId);
      setReport(report);
      navigate('/results/report');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not generate report');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="container-page max-w-3xl py-10">
      <ProgressStepper current="results" />
      <h1 className="text-2xl font-bold text-slate-900">Recommended tests</h1>
      <p className="mt-2 text-slate-600">
        Based on your answers, these tests may help a clinician assess your concern.
      </p>

      {loading && <p className="mt-8 text-sm text-slate-500">Loading recommendations…</p>}

      {recommendations && (
        <div className="mt-8 space-y-4">
          {recommendations.recommended_tests.length === 0 ? (
            <Card>
              <CardContent className="pt-6 text-sm text-slate-600">
                No specific tests were matched. Please speak with clinic staff for next steps.
              </CardContent>
            </Card>
          ) : (
            recommendations.recommended_tests.map((t) => (
              <TestExplanationCard key={t.test_code} test={t} sessionId={sessionId!} />
            ))
          )}

          {recommendations.general_recommendations.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">General guidance</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                  {recommendations.general_recommendations.map((g) => (
                    <li key={g}>{g}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <div className="flex flex-wrap gap-3">
            <Button type="button" onClick={generateReport} disabled={generating}>
              {generating ? 'Generating…' : 'Generate report'}
            </Button>
            <LinkButton to="/chat/summary" variant="secondary">
              Back to summary
            </LinkButton>
          </div>
        </div>
      )}
    </div>
  );
}
