import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { adminApi } from '@/lib/api';

export function AdminAiLogsPage() {
  const [logs, setLogs] = useState<Record<string, unknown>[]>([]);

  useEffect(() => {
    adminApi
      .aiLogs()
      .then(setLogs)
      .catch((e) => toast.error(e instanceof Error ? e.message : 'Failed to load AI logs'));
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">AI explanation logs</h1>
      <div className="space-y-3">
        {logs.map((log) => (
          <Card key={String(log.id)}>
            <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
              <div>
                <CardTitle className="text-base">{String(log.recommended_test_name)}</CardTitle>
                <p className="mt-1 text-xs text-slate-400">
                  {log.created_at ? new Date(String(log.created_at)).toLocaleString() : ''}
                </p>
              </div>
              <Badge variant="outline">{String(log.source)}</Badge>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm text-slate-700">
                {String(log.response_text || '').slice(0, 500)}
                {String(log.response_text || '').length > 500 ? '…' : ''}
              </p>
            </CardContent>
          </Card>
        ))}
        {logs.length === 0 && <p className="text-sm text-slate-500">No AI logs yet.</p>}
      </div>
    </div>
  );
}
