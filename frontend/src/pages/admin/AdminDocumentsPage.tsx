import { useEffect, useState } from 'react';
import { toast } from 'sonner';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { adminApi } from '@/lib/api';

type DocItem = Record<string, unknown>;

export function AdminDocumentsPage() {
  const [items, setItems] = useState<DocItem[]>([]);
  const [indexing, setIndexing] = useState(true);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState('');
  const [uploading, setUploading] = useState(false);

  async function reload() {
    const res = await adminApi.documents();
    setItems(res.items || []);
    setIndexing(Boolean(res.indexing_available ?? true));
  }

  useEffect(() => {
    reload().catch((e) => toast.error(e instanceof Error ? e.message : 'Failed to load documents'));
  }, []);

  async function onUpload(e: React.FormEvent) {
    e.preventDefault();
    if (!file) {
      toast.error('Choose a file');
      return;
    }
    setUploading(true);
    try {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('title', title || file.name);
      fd.append('category', 'guideline');
      await adminApi.uploadDocument(fd);
      toast.success('Document uploaded');
      setFile(null);
      setTitle('');
      await reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-slate-900">Knowledge documents</h1>
      {!indexing && (
        <p className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Vector indexing is currently unavailable. Uploads will be stored but may not be searchable
          for AI explanations yet.
        </p>
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Upload document</CardTitle>
        </CardHeader>
        <CardContent>
          <form className="flex flex-col gap-3 sm:flex-row sm:items-end" onSubmit={onUpload}>
            <div className="flex-1 space-y-1">
              <Label>Title</Label>
              <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Optional title" />
            </div>
            <div className="flex-1 space-y-1">
              <Label>File</Label>
              <Input
                type="file"
                accept=".pdf,.txt,.md,.docx"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </div>
            <Button type="submit" disabled={uploading}>
              {uploading ? 'Uploading…' : 'Upload'}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {items.map((d) => (
          <Card key={String(d.id)}>
            <CardHeader className="pb-2">
              <CardTitle className="text-base">{String(d.title || d.filename || d.id)}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-slate-500">
              {String(d.category || '')}
              {d.vector_indexed ? ' · Indexed' : ' · Not indexed'}
            </CardContent>
          </Card>
        ))}
        {items.length === 0 && <p className="text-sm text-slate-500">No documents yet.</p>}
      </div>
    </div>
  );
}
