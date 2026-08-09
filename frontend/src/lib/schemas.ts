import { z } from 'zod';

export const relationshipSchema = z.enum(['myself', 'my_child', 'someone_else']);

/** Under this age → child pathway; this age and above → adult. */
export const CHILD_AGE_LIMIT = 13;

export const clinicalDepartmentSchema = z.enum(['audiology', 'speech_language']);
export type ClinicalDepartment = z.infer<typeof clinicalDepartmentSchema>;

export const CLINICAL_DEPARTMENTS: { value: ClinicalDepartment; label: string }[] = [
  { value: 'audiology', label: 'Hearing and Ear related problems' },
  { value: 'speech_language', label: 'Speech and Speech related problems' },
];

/** Child screening age bands — labels match the clinic pathway (under 13). */
export const childAgeCategorySchema = z.enum([
  'newborn',
  'infant_toddler',
  'preschool',
  'school_age',
]);

export type ChildAgeCategory = z.infer<typeof childAgeCategorySchema>;

export const CHILD_AGE_CATEGORIES: {
  value: ChildAgeCategory;
  label: string;
  /** Representative age in whole years stored on the patient record. */
  ageYears: number;
}[] = [
  { value: 'newborn', label: '0–6 months', ageYears: 0 },
  { value: 'infant_toddler', label: '6–24 months', ageYears: 1 },
  { value: 'preschool', label: '2–5 years', ageYears: 3 },
  { value: 'school_age', label: '5–12 years', ageYears: 8 },
];

export function ageYearsForChildCategory(category: ChildAgeCategory): number {
  return CHILD_AGE_CATEGORIES.find((c) => c.value === category)?.ageYears ?? 0;
}

/** Whole years completed since a YYYY-MM-DD date of birth. */
export function ageYearsFromDob(dob: string): number {
  const birth = new Date(`${dob}T00:00:00`);
  if (Number.isNaN(birth.getTime())) return 0;
  const today = new Date();
  let age = today.getFullYear() - birth.getFullYear();
  const monthDiff = today.getMonth() - birth.getMonth();
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age -= 1;
  }
  return Math.max(0, age);
}

/** Map a DOB to the clinic child age band, or null if 13+. */
export function childCategoryFromDob(dob: string): ChildAgeCategory | null {
  const birth = new Date(`${dob}T00:00:00`);
  if (Number.isNaN(birth.getTime())) return null;
  const today = new Date();
  let months =
    (today.getFullYear() - birth.getFullYear()) * 12 + (today.getMonth() - birth.getMonth());
  if (today.getDate() < birth.getDate()) months -= 1;
  if (months < 0) return null;
  if (months <= 6) return 'newborn';
  if (months < 24) return 'infant_toddler';
  if (months < 60) return 'preschool';
  if (months < CHILD_AGE_LIMIT * 12) return 'school_age';
  return null;
}

export function todayIsoDate(): string {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

/** Approximate YYYY-MM-DD from whole years of age (for API fields that still require DOB). */
export function dobFromAgeYears(age: number): string {
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const birth = new Date(today);
  birth.setFullYear(today.getFullYear() - Math.max(0, Math.min(120, Math.trunc(age))));
  const y = birth.getFullYear();
  const m = String(birth.getMonth() + 1).padStart(2, '0');
  const d = String(birth.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

export const registrationSchema = z
  .object({
    name: z.string().min(2, 'Name must be at least 2 characters').max(200),
    age: z.preprocess(
      (value) => {
        if (value === '' || value === null || value === undefined) return undefined;
        const n = typeof value === 'number' ? value : Number(value);
        return Number.isFinite(n) ? n : undefined;
      },
      z
        .number({ required_error: 'Enter age', invalid_type_error: 'Enter age' })
        .int()
        .min(0)
        .max(120),
    ),
    gender: z.string().min(1, 'Select a gender').max(40),
    state: z.string().min(2, 'Select a state').max(120),
    district: z.string().min(2, 'Select a district').max(120),
    phone: z.string().max(30).optional().or(z.literal('')),
    relationship: relationshipSchema,
    department: clinicalDepartmentSchema,
    child_subtype: z.union([childAgeCategorySchema, z.literal('')]).optional(),
    consent_given: z.boolean().default(false),
    consent_by: z.string().max(200).optional().or(z.literal('')),
  })
  .superRefine((data, ctx) => {
    const isChild = data.relationship === 'my_child' || data.age < CHILD_AGE_LIMIT;
    if (data.relationship === 'my_child' && !data.child_subtype) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Select the child’s age category',
        path: ['child_subtype'],
      });
    }
    if (data.relationship === 'my_child' && data.age >= CHILD_AGE_LIMIT) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        message: 'Child registration is for ages under 13. Use adult registration for 13+.',
        path: ['age'],
      });
    }
    if (isChild) {
      if (!data.consent_given) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Guardian consent is required for a child',
          path: ['consent_given'],
        });
      }
      if (!data.consent_by || data.consent_by.trim().length < 2) {
        ctx.addIssue({
          code: z.ZodIssueCode.custom,
          message: 'Enter the name of the person giving consent',
          path: ['consent_by'],
        });
      }
    }
  });

export type RegistrationForm = z.infer<typeof registrationSchema>;

export const loginSchema = z.object({
  email: z.string().email('Enter a valid email'),
  password: z.string().min(1, 'Password is required'),
});

export type LoginForm = z.infer<typeof loginSchema>;

export const categoryCreateSchema = z.object({
  slug: z
    .string()
    .min(2)
    .max(80)
    .regex(/^[a-z0-9_-]+$/, 'Lowercase letters, numbers, _ or - only'),
  name: z.string().min(2).max(200),
  flow_type: z.enum(['adult', 'child']),
  description: z.string().optional(),
  display_order: z.coerce.number().int().default(0),
});

export const questionCreateSchema = z.object({
  condition_id: z.string().uuid(),
  key: z
    .string()
    .min(2)
    .max(80)
    .regex(/^[a-z0-9_]+$/, 'Lowercase letters, numbers, _ only'),
  text: z.string().min(3).max(500),
  help_text: z.string().optional(),
  display_order: z.coerce.number().int().default(0),
  question_type: z.enum(['single_select', 'multi_select', 'yes_no']).default('single_select'),
  is_entry: z.boolean().default(false),
});
