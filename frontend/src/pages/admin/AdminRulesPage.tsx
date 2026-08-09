import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { adminApi } from '@/lib/api';

export function AdminRulesPage() {
  const [rules, setRules] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    adminApi
      .rules()
      .then(setRules)
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Failed to load rules'));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Clinical rules</h1>
      <div className="space-y-3">
        {rules.map((r) => (
          <Card key={String(r.id)}>
            <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
              <div>
                <CardTitle className="text-base">{String(r.name)}</CardTitle>
                <p className="mt-1 text-sm text-slate-500">{String(r.description || '')}</p>
              </div>
              <div className="flex gap-2">
                {r.is_baseline ? <Badge variant="secondary">Baseline</Badge> : null}
                <Badge variant={r.is_active ? 'success' : 'outline'}>
                  {r.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="text-xs text-slate-500">
              Priority {String(r.priority)} ·{' '}
              {Array.isArray(r.tests) ? `${r.tests.length} tests` : '0 tests'}
            </CardContent>
          </Card>
        ))}
        {rules.length === 0 && <p className="text-sm text-slate-500">No rules found.</p>}
      </div>
    </div>
  );
}
