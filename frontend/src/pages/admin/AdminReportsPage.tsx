import { useEffect, useState } from 'react';
import { Download } from 'lucide-react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { adminApi, reportsApi, type Report } from '@/lib/api';

export function AdminReportsPage() {
  const [reports, setReports] = useState<Report[]>([]);

  useEffect(() => {
    adminApi
      .reports()
      .then(setReports)
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Failed to load reports'));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Generated reports</h1>
      <div className="space-y-3">
        {reports.map((r) => (
          <Card key={r.id}>
            <CardHeader className="flex flex-row items-center justify-between gap-3 space-y-0">
              <div>
                <CardTitle className="text-base">Report {r.id.slice(0, 8)}…</CardTitle>
                <p className="text-xs text-slate-400">
                  {new Date(r.generated_at).toLocaleString()} · session {r.session_id.slice(0, 8)}…
                </p>
              </div>
              <Button asChild size="sm" variant="secondary">
                <a href={reportsApi.downloadUrl(r.id)} target="_blank" rel="noreferrer">
                  <Download className="h-4 w-4" />
                  PDF
                </a>
              </Button>
            </CardHeader>
            <CardContent className="text-xs text-slate-500">
              Patient {r.patient_id.slice(0, 8)}…
            </CardContent>
          </Card>
        ))}
        {reports.length === 0 && <p className="text-sm text-slate-500">No reports yet.</p>}
      </div>
    </div>
  );
}
