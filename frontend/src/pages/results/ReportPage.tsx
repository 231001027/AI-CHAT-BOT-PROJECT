import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Download } from 'lucide-react';
import { toast } from 'sonner';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
import { Button, LinkButton } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { reportsApi } from '@/lib/api';
import { useSessionStore } from '@/store/session';

export function ReportPage() {
  const navigate = useNavigate();
  const sessionId = useSessionStore((s) => s.sessionId);
  const report = useSessionStore((s) => s.report);
  const recommendations = useSessionStore((s) => s.recommendations);
  const setReport = useSessionStore((s) => s.setReport);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!sessionId) {
      navigate('/chat/category', { replace: true });
      return;
    }
    if (report) return;
    let cancelled = false;
    (async () => {
      setBusy(true);
      try {
        const r = await reportsApi.generate(sessionId);
        if (!cancelled) setReport(r);
      } catch (e) {
        toast.error(e instanceof Error ? e.message : 'Could not generate report');
      } finally {
        if (!cancelled) setBusy(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [sessionId, report, navigate, setReport]);

  const json = (report?.report_json || {}) as Record<string, unknown>;

  return (
    <div className="container-page max-w-3xl py-10">
      <ProgressStepper current="results" />
      <h1 className="text-2xl font-bold text-slate-900">Visit report</h1>
      <p className="mt-2 text-slate-600">
        Preview of your guidance report. Download the PDF to keep a copy for your clinician.
      </p>

      {busy && !report && <p className="mt-8 text-sm text-slate-500">Generating report…</p>}

      {report && (
        <div className="mt-8 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Report preview</CardTitle>
              <p className="text-xs text-slate-500">
                Generated {new Date(report.generated_at).toLocaleString()}
              </p>
            </CardHeader>
            <CardContent className="space-y-3 text-sm text-slate-700">
              {typeof json.patient_name === 'string' && (
                <p>
                  <span className="font-medium">Patient:</span> {json.patient_name}
                </p>
              )}
              {Array.isArray(json.recommended_tests) && (
                <div>
                  <p className="font-medium">Recommended tests</p>
                  <ul className="mt-1 list-disc space-y-1 pl-5">
                    {(json.recommended_tests as { test_name?: string; reason_text?: string }[]).map(
                      (t, i) => (
                        <li key={i}>
                          {t.test_name}
                          {t.reason_text ? ` — ${t.reason_text}` : ''}
                        </li>
                      ),
                    )}
                  </ul>
                </div>
              )}
              {!Array.isArray(json.recommended_tests) && recommendations && (
                <ul className="list-disc space-y-1 pl-5">
                  {recommendations.recommended_tests.map((t) => (
                    <li key={t.test_code}>
                      {t.test_name} — {t.reason_text}
                    </li>
                  ))}
                </ul>
              )}
              <pre className="max-h-64 overflow-auto rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
                {JSON.stringify(json, null, 2)}
              </pre>
            </CardContent>
          </Card>

          <div className="flex flex-wrap gap-3">
            <Button asChild>
              <a href={reportsApi.downloadUrl(report.id)} target="_blank" rel="noreferrer">
                <Download className="h-4 w-4" />
                Download PDF
              </a>
            </Button>
            <LinkButton to="/results/recommendations" variant="secondary">
              Back to recommendations
            </LinkButton>
          </div>
        </div>
      )}
    </div>
  );
}
