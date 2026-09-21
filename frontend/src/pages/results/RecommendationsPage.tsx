import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
import { TestExplanationCard } from '@/components/shared/TestExplanationCard';
import { Button, LinkButton } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { recommendationsApi, reportsApi } from '@/lib/api';
import { useSessionStore } from '@/store/session';

const MANAGEMENT_POINTS = {
  1: 'An individualized goal plan targeting the specific language skills found to be weak.',
  2: 'For children: structured language stimulation, building vocabulary, and helping form longer sentences.',
  3: 'For adults with aphasia: structured relearning and compensatory strategies to regain functional communication.',
  4: 'Regular progress reviews and goal updates.',
  5: "Children — modelling, expansion and recasting of the child's utterances, play-based language stimulation, parent-implemented intervention training.",
  6: 'Adults — Melodic Intonation Therapy, semantic feature analysis, script training for functional phrases, and Augmentative and Alternative Communication (AAC) support where needed.',
} as const;

function isChildAge(age: number | undefined | null, flowType?: string | null): boolean {
  if (typeof age === 'number' && Number.isFinite(age)) return age < 18;
  return flowType === 'child';
}

export function RecommendationsPage() {
  const navigate = useNavigate();
  const sessionId = useSessionStore((s) => s.sessionId);
  const patient = useSessionStore((s) => s.patient);
  const category = useSessionStore((s) => s.category);
  const recommendations = useSessionStore((s) => s.recommendations);
  const setRecommendations = useSessionStore((s) => s.setRecommendations);
  const setReport = useSessionStore((s) => s.setReport);
  const [loading, setLoading] = useState(!recommendations);
  const [generating, setGenerating] = useState(false);
  const [activeTab, setActiveTab] = useState('recommendation');

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

  const child = isChildAge(patient?.age, category?.flow_type);
  const managementItems = child
    ? [MANAGEMENT_POINTS[1], MANAGEMENT_POINTS[2], MANAGEMENT_POINTS[4], MANAGEMENT_POINTS[5]]
    : [MANAGEMENT_POINTS[1], MANAGEMENT_POINTS[3], MANAGEMENT_POINTS[4], MANAGEMENT_POINTS[6]];
  const displayTests = (recommendations?.recommended_tests ?? []).filter(
    (t) => t.test_code !== 'SLP_EVAL',
  );

  return (
    <div className="container-page max-w-6xl py-10">
      <ProgressStepper current="results" />
      <h1 className="text-2xl font-bold text-slate-900">Recommendation</h1>
      <p className="mt-2 text-slate-600">
        Based on your answers, these tests may help a clinician assess your concern.
      </p>

      {loading && <p className="mt-8 text-sm text-slate-500">Loading recommendations…</p>}

      {recommendations && (
        <div className="mt-8 space-y-4">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
            <TabsList className="grid h-auto w-full grid-cols-2 rounded-none bg-transparent p-0">
              <TabsTrigger
                value="recommendation"
                className="rounded-none rounded-t-lg border border-slate-400 bg-slate-100 px-4 py-3 text-sm font-normal text-slate-700 shadow-none data-[state=active]:z-10 data-[state=active]:-mb-px data-[state=active]:border-b-white data-[state=active]:bg-white data-[state=active]:font-bold data-[state=active]:text-slate-900 data-[state=active]:shadow-none"
              >
                Recommendation
              </TabsTrigger>
              <TabsTrigger
                value="management"
                className="rounded-none rounded-t-lg border border-l-0 border-slate-400 bg-slate-100 px-4 py-3 text-sm font-normal text-slate-700 shadow-none data-[state=active]:z-10 data-[state=active]:-mb-px data-[state=active]:border-b-white data-[state=active]:bg-white data-[state=active]:font-bold data-[state=active]:text-slate-900 data-[state=active]:shadow-none"
              >
                Management
              </TabsTrigger>
            </TabsList>

            <div className="border border-slate-400 bg-white p-5 sm:p-6">
              <TabsContent value="recommendation" className="mt-0">
                {displayTests.length === 0 ? (
                  <Card>
                    <CardContent className="pt-6 text-sm text-slate-600">
                      No specific tests were matched. Please speak with clinic staff for next steps.
                    </CardContent>
                  </Card>
                ) : (
                  <div
                    className={
                      displayTests.length >= 2
                        ? 'grid items-stretch gap-4 md:grid-cols-2'
                        : 'space-y-4'
                    }
                  >
                    {displayTests.map((t) => (
                      <TestExplanationCard key={t.test_code} test={t} sessionId={sessionId!} />
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="management" className="mt-0 text-sm text-slate-700">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Management</p>
                <h2 className="mt-1 text-lg font-bold text-slate-900">Management — What We Do</h2>
                <ul className="mt-3 list-disc space-y-1.5 pl-5">
                  {managementItems.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </TabsContent>
            </div>
          </Tabs>

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
