import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { ProgressStepper } from '@/components/shared/ProgressStepper';
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
import { patientsApi } from '@/lib/api';
import {
  districtsForState,
  INDIAN_STATES,
} from '@/data/indianDistricts';
import {
  ageYearsForChildCategory,
  CHILD_AGE_CATEGORIES,
  CHILD_AGE_LIMIT,
  CLINICAL_DEPARTMENTS,
  childCategoryFromDob,
  dobFromAgeYears,
  registrationSchema,
  type ChildAgeCategory,
  type RegistrationForm,
} from '@/lib/schemas';
import { useSessionStore } from '@/store/session';

export function RegisterPage() {
  const navigate = useNavigate();
  const patient = useSessionStore((s) => s.patient);
  const relationship = useSessionStore((s) => s.relationship);
  const setPatient = useSessionStore((s) => s.setPatient);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<RegistrationForm>({
    resolver: zodResolver(registrationSchema),
    defaultValues: {
      relationship: relationship || 'myself',
      consent_given: false,
      gender: '',
      name: '',
      age: undefined as unknown as number,
      state: '',
      district: '',
      phone: '',
      consent_by: '',
      child_subtype: '',
      department: '' as unknown as RegistrationForm['department'],
    },
  });

  useEffect(() => {
    if (!relationship) {
      navigate('/register/relationship', { replace: true });
      return;
    }

    setValue('relationship', relationship);
  }, [relationship, navigate, setValue]);

  const age = watch('age');
  const rel = watch('relationship');
  const childSubtype = watch('child_subtype');
  const department = watch('department');
  const state = watch('state');
  const district = watch('district');
  const ageNumber = typeof age === 'number' && !Number.isNaN(age) ? age : undefined;
  const needsConsent = rel === 'my_child' || (ageNumber !== undefined && ageNumber < CHILD_AGE_LIMIT);
  const showChildAgeCategory = rel === 'my_child';
  const districtOptions = state ? districtsForState(state) : [];

  function onStateChange(nextState: string) {
    setValue('state', nextState, { shouldValidate: true });
    setValue('district', '', { shouldValidate: true });
  }

  function onAgeChange(raw: string) {
    if (raw === '') {
      setValue('age', undefined as unknown as number, { shouldValidate: true });
      return;
    }
    const years = Number(raw);
    if (!Number.isFinite(years)) return;
    const clamped = Math.max(0, Math.min(120, Math.trunc(years)));
    setValue('age', clamped, { shouldValidate: true });

    if (rel === 'my_child') {
      const band = childCategoryFromDob(dobFromAgeYears(clamped));
      if (band) setValue('child_subtype', band, { shouldValidate: true });
    }
  }

  function onChildCategoryChange(value: string) {
    const category = value as ChildAgeCategory;
    setValue('child_subtype', category, { shouldValidate: true });
    setValue('age', ageYearsForChildCategory(category), { shouldValidate: true });
  }

  async function onSubmit(data: RegistrationForm) {
    try {
      const years = data.age;
      const dob = dobFromAgeYears(years);
      const subtype =
        data.relationship === 'my_child'
          ? data.child_subtype || childCategoryFromDob(dob) || undefined
          : undefined;

      const body = {
        name: data.name,
        age: years,
        gender: data.gender,
        district: `${data.district}, ${data.state}`,
        phone: data.phone || null,
        relationship: data.relationship,
        department: data.department,
        date_of_birth: dob,
        child_subtype: subtype || null,
        consent_given: needsConsent ? data.consent_given : false,
        consent_by: needsConsent ? data.consent_by || null : null,
      };

      const saved = patient
        ? await patientsApi.update(patient.id, body)
        : await patientsApi.register(body);
      setPatient(saved);
      toast.success(
        saved.user_code ? `Registration saved — User ID ${saved.user_code}` : 'Registration saved',
      );
      navigate('/chat/category');
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Registration failed');
    }
  }

  if (!relationship) return null;

  return (
    <div className="container-page max-w-2xl py-10">
      <ProgressStepper current="register" />
      <Card>
        <CardHeader>
          <CardTitle>Patient registration</CardTitle>
          <p className="text-sm text-slate-500">
            Tell us who you are registering so we can open the right screening pathway.
            {patient?.user_code ? ` User ID: ${patient.user_code}` : null}
          </p>
        </CardHeader>
        <CardContent>
          <form className="space-y-4" onSubmit={handleSubmit(onSubmit)}>
            <div className="space-y-2">
              <Label htmlFor="name">Full name</Label>
              <Input id="name" {...register('name')} />
              {errors.name && <p className="text-xs text-red-600">{errors.name.message}</p>}
            </div>

            <div className="space-y-2">
              <Label>Concern type</Label>
              <Select
                value={department || '__none__'}
                onValueChange={(v) =>
                  setValue(
                    'department',
                    (v === '__none__' ? '' : v) as RegistrationForm['department'],
                    { shouldValidate: true },
                  )
                }
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select concern type" />
                </SelectTrigger>
                <SelectContent>
                  {CLINICAL_DEPARTMENTS.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {errors.department && (
                <p className="text-xs text-red-600">{errors.department.message}</p>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {showChildAgeCategory ? (
                <div className="space-y-2">
                  <Label>Child age category</Label>
                  <Select
                    value={childSubtype || '__none__'}
                    onValueChange={(v) => {
                      if (v === '__none__') return;
                      onChildCategoryChange(v);
                    }}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select age range" />
                    </SelectTrigger>
                    <SelectContent>
                      {CHILD_AGE_CATEGORIES.map((opt) => (
                        <SelectItem key={opt.value} value={opt.value}>
                          {opt.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {errors.child_subtype && (
                    <p className="text-xs text-red-600">{errors.child_subtype.message}</p>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <Label htmlFor="age">Age (years)</Label>
                  <Input
                    id="age"
                    type="number"
                    min={0}
                    max={120}
                    inputMode="numeric"
                    value={ageNumber === undefined ? '' : ageNumber}
                    onChange={(e) => onAgeChange(e.target.value)}
                  />
                  {ageNumber !== undefined && (
                    <p className="text-xs text-slate-500">
                      {ageNumber < CHILD_AGE_LIMIT ? 'Child pathway' : 'Adult pathway'}
                    </p>
                  )}
                  {errors.age && <p className="text-xs text-red-600">{errors.age.message}</p>}
                </div>
              )}
              <div className="space-y-2">
                <Label>Gender</Label>
                <Select
                  value={watch('gender') || '__none__'}
                  onValueChange={(v) => {
                    if (v === '__none__') return;
                    setValue('gender', v, { shouldValidate: true });
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="female">Female</SelectItem>
                    <SelectItem value="male">Male</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                    <SelectItem value="prefer_not_to_say">Prefer not to say</SelectItem>
                  </SelectContent>
                </Select>
                {errors.gender && <p className="text-xs text-red-600">{errors.gender.message}</p>}
              </div>
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label>State / UT</Label>
                <Select
                  value={state || '__none__'}
                  onValueChange={(v) => {
                    if (v === '__none__') return;
                    onStateChange(v);
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select state" />
                  </SelectTrigger>
                  <SelectContent>
                    {INDIAN_STATES.map((s) => (
                      <SelectItem key={s} value={s}>
                        {s}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.state && <p className="text-xs text-red-600">{errors.state.message}</p>}
              </div>
              <div className="space-y-2">
                <Label>District</Label>
                <Select
                  key={state || 'no-state'}
                  value={district || '__none__'}
                  onValueChange={(v) => {
                    if (v === '__none__') return;
                    setValue('district', v, { shouldValidate: true });
                  }}
                  disabled={!state}
                >
                  <SelectTrigger>
                    <SelectValue placeholder={state ? 'Select district' : 'Select state first'} />
                  </SelectTrigger>
                  <SelectContent>
                    {districtOptions.map((d) => (
                      <SelectItem key={d} value={d}>
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {errors.district && (
                  <p className="text-xs text-red-600">{errors.district.message}</p>
                )}
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="phone">Phone (optional)</Label>
              <Input id="phone" {...register('phone')} />
            </div>

            {needsConsent && (
              <div className="space-y-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
                <p className="text-sm font-medium text-amber-950">
                  Guardian consent is required before we can process a child&apos;s information.
                </p>
                <div className="space-y-2">
                  <Label htmlFor="consent_by">Consent given by</Label>
                  <Input id="consent_by" placeholder="Parent / guardian name" {...register('consent_by')} />
                  {errors.consent_by && (
                    <p className="text-xs text-red-600">{errors.consent_by.message}</p>
                  )}
                </div>
                <label className="flex items-start gap-2 text-sm text-amber-950">
                  <input type="checkbox" className="mt-1" {...register('consent_given')} />
                  I confirm I am authorised to provide consent for this child&apos;s data to be used
                  for this screening visit.
                </label>
                {errors.consent_given && (
                  <p className="text-xs text-red-600">{errors.consent_given.message}</p>
                )}
              </div>
            )}

            <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
              {isSubmitting ? 'Saving…' : 'Continue'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
