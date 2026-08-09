import { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { toast } from 'sonner';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { adminApi, type Doctor } from '@/lib/api';

export function AdminDoctorsPage() {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [open, setOpen] = useState(false);
  const form = useForm({
    defaultValues: {
      name: '',
      email: '',
      password: '',
      role: 'audiologist',
      specialization: '',
      phone: '',
    },
  });

  async function reload() {
    setDoctors(await adminApi.doctors());
  }

  useEffect(() => {
    reload().catch((e) => toast.error(e instanceof Error ? e.message : 'Failed to load doctors'));
  }, []);

  async function onCreate(data: {
    name: string;
    email: string;
    password: string;
    role: string;
    specialization: string;
    phone: string;
  }) {
    try {
      await adminApi.createDoctor({
        ...data,
        specialization: data.specialization || null,
        phone: data.phone || null,
      });
      toast.success('Doctor created');
      setOpen(false);
      form.reset();
      await reload();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Create failed');
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-bold text-slate-900">Doctors</h1>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">Add doctor</Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New staff account</DialogTitle>
            </DialogHeader>
            <form className="space-y-3" onSubmit={form.handleSubmit(onCreate)}>
              <div className="space-y-1">
                <Label>Name</Label>
                <Input {...form.register('name', { required: true })} />
              </div>
              <div className="space-y-1">
                <Label>Email</Label>
                <Input type="email" {...form.register('email', { required: true })} />
              </div>
              <div className="space-y-1">
                <Label>Password</Label>
                <Input type="password" {...form.register('password', { required: true, minLength: 8 })} />
              </div>
              <div className="space-y-1">
                <Label>Specialization</Label>
                <Input {...form.register('specialization')} />
              </div>
              <Button type="submit">Create</Button>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <div className="space-y-3">
        {doctors.map((d) => (
          <Card key={d.id}>
            <CardHeader className="flex flex-row items-start justify-between gap-3 space-y-0">
              <div>
                <CardTitle className="text-base">{d.name}</CardTitle>
                <p className="text-sm text-slate-500">{d.email}</p>
              </div>
              <div className="flex gap-2">
                <Badge variant="secondary">{d.role}</Badge>
                <Badge variant={d.is_active ? 'success' : 'outline'}>
                  {d.is_active ? 'Active' : 'Inactive'}
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="text-sm text-slate-500">
              {d.specialization || 'No specialization listed'}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
