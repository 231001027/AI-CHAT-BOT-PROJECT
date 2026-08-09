import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { adminApi, type Category, type Condition, type Question } from '@/lib/api';

export function AdminQuestionsPage() {
  const [categories, setCategories] = useState<Category[]>([]);
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [open, setOpen] = useState(false);
  const [catOpen, setCatOpen] = useState(false);
  const form = useForm({
    defaultValues: {
      condition_id: '',
      key: '',
      text: '',
      display_order: 0,
      is_entry: false,
    },
  });
  const catForm = useForm({
    defaultValues: {
      slug: '',
      name: '',
      flow_type: 'adult',
      description: '',
      display_order: 0,
    },
  });

  async function reload() {
    const [cats, conds, qs] = await Promise.all([
      adminApi.categories(),
      adminApi.conditions(),
      adminApi.questions(),
    ]);
    setCategories(cats);
    setConditions(conds);
    setQuestions(qs);
  }

  useEffect(() => {
    reload().catch((e) => toast.error(e instanceof Error ? e.message : 'Load failed'));
  }, []);

  async function createQuestion(data: {
    condition_id: string;
    key: string;
    text: string;
    display_order: number;
    is_entry: boolean;
  }) {
    try {
      await adminApi.createQuestion({
        ...data,
        question_type: 'single_select',
        display_order: Number(data.display_order) || 0,
      });
      toast.success('Question created');
      setOpen(false);
      form.reset();
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Create failed');
    }
  }

  async function createCategory(data: {
    slug: string;
    name: string;
    flow_type: string;
    description: string;
    display_order: number;
  }) {
    try {
      await adminApi.createCategory({
        ...data,
        display_order: Number(data.display_order) || 0,
      });
      toast.success('Category created');
      setCatOpen(false);
      catForm.reset();
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Create failed');
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-900">Question bank</h1>
        <div className="flex gap-2">
          <Dialog open={catOpen} onOpenChange={setCatOpen}>
            <DialogTrigger asChild>
              <Button variant="secondary" size="sm">
                Add category
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New category</DialogTitle>
              </DialogHeader>
              <form className="space-y-3" onSubmit={catForm.handleSubmit(createCategory)}>
                <div className="space-y-1">
                  <Label>Slug</Label>
                  <Input {...catForm.register('slug', { required: true })} />
                </div>
                <div className="space-y-1">
                  <Label>Name</Label>
                  <Input {...catForm.register('name', { required: true })} />
                </div>
                <div className="space-y-1">
                  <Label>Flow</Label>
                  <Select
                    value={catForm.watch('flow_type')}
                    onValueChange={(v) => catForm.setValue('flow_type', v)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="adult">Adult</SelectItem>
                      <SelectItem value="child">Child</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Description</Label>
                  <Input {...catForm.register('description')} />
                </div>
                <Button type="submit">Create</Button>
              </form>
            </DialogContent>
          </Dialog>

          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm">Add question</Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>New question</DialogTitle>
              </DialogHeader>
              <form className="space-y-3" onSubmit={form.handleSubmit(createQuestion)}>
                <div className="space-y-1">
                  <Label>Condition</Label>
                  <Select
                    value={form.watch('condition_id') || undefined}
                    onValueChange={(v) => form.setValue('condition_id', v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select condition" />
                    </SelectTrigger>
                    <SelectContent>
                      {conditions.map((c) => (
                        <SelectItem key={c.id} value={c.id}>
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <Label>Key</Label>
                  <Input {...form.register('key', { required: true })} />
                </div>
                <div className="space-y-1">
                  <Label>Text</Label>
                  <Input {...form.register('text', { required: true })} />
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" {...form.register('is_entry')} /> Entry question
                </label>
                <Button type="submit">Create</Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="space-y-4">
        {categories
          .slice()
          .sort((a, b) => a.display_order - b.display_order)
          .map((cat) => {
            const catConditions = conditions.filter((c) => c.category_id === cat.id);
            return (
              <Card key={cat.id}>
                <CardHeader>
                  <CardTitle className="text-base">
                    {cat.name}{' '}
                    <span className="text-xs font-normal text-slate-400">({cat.flow_type})</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {catConditions.length === 0 && (
                    <p className="text-sm text-slate-500">No conditions yet.</p>
                  )}
                  {catConditions.map((cond) => {
                    const qs = questions.filter((q) => q.condition_id === cond.id);
                    return (
                      <div key={cond.id} className="rounded-xl border border-slate-100 p-3">
                        <p className="font-medium text-slate-800">{cond.name}</p>
                        <ul className="mt-2 space-y-1 text-sm text-slate-600">
                          {qs.map((q) => (
                            <li key={q.id}>
                              {q.is_entry ? '★ ' : ''}
                              {q.text}
                              <span className="ml-2 text-xs text-slate-400">{q.key}</span>
                            </li>
                          ))}
                          {qs.length === 0 && (
                            <li className="text-slate-400">No questions</li>
                          )}
                        </ul>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
            );
          })}
      </div>
    </div>
  );
}
