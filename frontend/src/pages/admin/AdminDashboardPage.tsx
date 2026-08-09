import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { adminApi } from '@/lib/api';

export function AdminDashboardPage() {
  const [stats, setStats] = useState<Record<string, number> | null>(null);

  useEffect(() => {
    adminApi
      .dashboard()
      .then((d) => setStats(d as Record<string, number>))
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Failed to load dashboard'));
  }, []);

  const cards: { key: string; label: string }[] = [
    { key: 'patients_total', label: 'Patients' },
    { key: 'patients_last_7_days', label: 'Patients (7d)' },
    { key: 'sessions_total', label: 'Sessions' },
    { key: 'sessions_completed', label: 'Completed' },
    { key: 'plans_generated', label: 'Treatment plans' },
    { key: 'reports_generated', label: 'Reports' },
    { key: 'ai_explanations', label: 'AI explanations' },
    { key: 'ai_fallback_rate', label: 'AI fallback rate' },
    { key: 'documents_indexed', label: 'Docs indexed' },
    { key: 'documents_total', label: 'Documents' },
    { key: 'rules_active', label: 'Active rules' },
    { key: 'questions_active', label: 'Active questions' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
      {!stats && <p className="text-sm text-slate-500">Loading…</p>}
      {stats && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {cards.map(({ key, label }) => (
            <Card key={key}>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-500">{label}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-2xl font-bold text-slate-900">
                  {key === 'ai_fallback_rate'
                    ? `${Math.round((stats[key] || 0) * 100)}%`
                    : stats[key] ?? 0}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
