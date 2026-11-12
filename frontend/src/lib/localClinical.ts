/**
 * Embedded clinical engine for production when FastAPI is not hosted.
 * Uses a snapshot of categories / questions / rules so Take Test works on Vercel.
 */

import snapshot from '@/data/clinicalSnapshot.json';
import type {
  AnswerOut,
  Category,
  ClinicalDepartment,
  Condition,
  FlowType,
  Option,
  Patient,
  Question,
  Recommendation,
  Report,
  SessionState,
  SessionSummary,
  UserType,
} from '@/lib/api';

type SnapQuestion = {
  id: string;
  condition_id: string;
  key: string;
  text: string;
  help_text?: string | null;
  display_order: number;
  question_type: string;
  is_entry: boolean;
};

type SnapOption = {
  id: string;
  question_id: string;
  label: string;
  value: string;
  display_order: number;
  next_question_id?: string | null;
  is_terminal: boolean;
};

type SnapRule = {
  id: string;
  category_id?: string | null;
  condition_id?: string | null;
  name: string;
  description: string;
  rule_definition: Record<string, unknown>;
  priority: number;
  is_baseline: boolean;
};

type SnapTest = {
  id: string;
  rule_id: string;
  test_code: string;
  test_name: string;
  reason_text: string;
  display_order: number;
};

type SnapCatalog = {
  code: string;
  name: string;
  description: string;
  preparation?: string | null;
  duration_minutes?: number | null;
};

const categories = snapshot.categories as Category[];
const conditions = snapshot.conditions as Condition[];
const questions = snapshot.questions as SnapQuestion[];
const options = snapshot.options as SnapOption[];
const rules = snapshot.rules as SnapRule[];
const recommendedTests = snapshot.recommended_tests as SnapTest[];
const testCatalog = snapshot.test_catalog as SnapCatalog[];

type LocalSession = {
  session_id: string;
  patient_id: string;
  condition_id: string;
  category_id: string;
  status: string;
  is_complete: boolean;
  current_question_id: string | null;
  answers: AnswerOut[];
  facts: Record<string, string | number>;
  created_at: string;
  completed_at?: string | null;
};

type LocalStore = {
  patients: Record<string, Patient>;
  sessions: Record<string, LocalSession>;
  plans: Record<string, Recommendation>;
  reports: Record<string, Report>;
  userCodeSeq: number;
};

const STORE_KEY = 'niepmd-local-clinical-v1';

function loadStore(): LocalStore {
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return JSON.parse(raw) as LocalStore;
  } catch {
    /* ignore */
  }
  return { patients: {}, sessions: {}, plans: {}, reports: {}, userCodeSeq: 0 };
}

function saveStore(store: LocalStore) {
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(store));
  } catch {
    /* ignore */
  }
}

function uid(): string {
  return crypto.randomUUID();
}

function catalogByCode(code: string): SnapCatalog | undefined {
  return testCatalog.find((t) => t.code === code);
}

function optionsFor(questionId: string): Option[] {
  return options
    .filter((o) => o.question_id === questionId)
    .sort((a, b) => a.display_order - b.display_order)
    .map((o) => ({
      id: o.id,
      label: o.label,
      value: o.value,
      display_order: o.display_order,
      next_question_id: o.next_question_id,
      is_terminal: o.is_terminal,
    }));
}

function toQuestion(q: SnapQuestion): Question {
  return {
    id: q.id,
    condition_id: q.condition_id,
    key: q.key,
    text: q.text,
    help_text: q.help_text,
    display_order: q.display_order,
    question_type: q.question_type,
    is_entry: q.is_entry,
    options: optionsFor(q.id),
  };
}

function entryQuestion(conditionId: string): SnapQuestion | undefined {
  const list = questions
    .filter((q) => q.condition_id === conditionId)
    .sort((a, b) => a.display_order - b.display_order);
  return list.find((q) => q.is_entry) ?? list[0];
}

function questionCount(conditionId: string): number {
  return questions.filter((q) => q.condition_id === conditionId).length;
}

function sessionState(session: LocalSession): SessionState {
  const q = session.current_question_id
    ? questions.find((item) => item.id === session.current_question_id)
    : undefined;
  return {
    session_id: session.session_id,
    patient_id: session.patient_id,
    condition_id: session.condition_id,
    category_id: session.category_id,
    status: session.status,
    is_complete: session.is_complete,
    question: q ? toQuestion(q) : null,
    progress: {
      answered: session.answers.length,
      total: questionCount(session.condition_id),
    },
  };
}

function inferFlow(age: number, relationship: UserType): FlowType {
  if (relationship === 'my_child') return 'child';
  return age < 13 ? 'child' : 'adult';
}

const TRUTHY = new Set(['yes', 'y', 'true', '1', 'present', 'sudden', 'both', 'left', 'right', 'often', 'always']);
const FALSY = new Set(['no', 'n', 'false', '0', 'absent', 'none', 'never', 'not_sure', 'unsure', 'dont_know']);

function isTruthy(value: unknown): boolean {
  if (value == null) return false;
  if (typeof value === 'boolean') return value;
  if (typeof value === 'number') return value !== 0;
  const text = String(value).trim().toLowerCase();
  if (!text) return false;
  if (FALSY.has(text)) return false;
  if (TRUTHY.has(text)) return true;
  return true;
}

function equals(left: unknown, right: unknown): boolean {
  const a = typeof left === 'number' || typeof right === 'number' ? Number(left) : String(left).trim().toLowerCase();
  const b = typeof left === 'number' || typeof right === 'number' ? Number(right) : String(right).trim().toLowerCase();
  if (typeof a === 'number' && typeof b === 'number' && !Number.isNaN(a) && !Number.isNaN(b)) return a === b;
  return String(a) === String(b);
}

function evaluateLeaf(node: Record<string, unknown>, facts: Record<string, unknown>): boolean {
  const field = String(node.field ?? '');
  const op = String(node.op ?? 'eq');
  const actual = facts[field];
  const expected = node.value;

  if (op === 'exists') return field in facts && facts[field] != null;
  if (op === 'truthy') return isTruthy(actual);
  if (op === 'falsy') return !isTruthy(actual);
  if (actual == null) return false;

  if (op === 'in' || op === 'not_in') {
    const list = Array.isArray(expected) ? expected : [];
    const found = list.some((item) => equals(actual, item));
    return op === 'in' ? found : !found;
  }
  if (op === 'contains') return String(actual).toLowerCase().includes(String(expected).toLowerCase());
  if (op === 'eq' || op === '==' || op === '=') return equals(actual, expected);
  if (op === 'ne' || op === '!=') return !equals(actual, expected);

  const left = Number(actual);
  const right = Number(expected);
  if (Number.isNaN(left) || Number.isNaN(right)) return false;
  if (op === 'gt' || op === '>') return left > right;
  if (op === 'gte' || op === '>=') return left >= right;
  if (op === 'lt' || op === '<') return left < right;
  if (op === 'lte' || op === '<=') return left <= right;
  return false;
}

function evaluatePredicate(node: unknown, facts: Record<string, unknown>): boolean {
  if (!node || typeof node !== 'object') return false;
  const obj = node as Record<string, unknown>;
  if (Array.isArray(obj.all)) return obj.all.length > 0 && obj.all.every((child) => evaluatePredicate(child, facts));
  if (Array.isArray(obj.any)) return obj.any.some((child) => evaluatePredicate(child, facts));
  if ('not' in obj) return !evaluatePredicate(obj.not, facts);
  return evaluateLeaf(obj, facts);
}

export const localClinical = {
  register(body: Record<string, unknown>): Patient {
    const store = loadStore();
    const relationship = (body.relationship as UserType) || 'myself';
    const age = Number(body.age) || 0;
    const flow_type = inferFlow(age, relationship);
    store.userCodeSeq += 1;
    const year = new Date().getFullYear();
    const patient: Patient = {
      id: uid(),
      name: String(body.name ?? ''),
      age,
      gender: String(body.gender ?? ''),
      district: String(body.district ?? ''),
      phone: (body.phone as string | null) ?? null,
      user_type: relationship,
      user_code: `${store.userCodeSeq}/${year}`,
      date_of_birth: (body.date_of_birth as string | null) ?? null,
      created_at: new Date().toISOString(),
      profile: {
        id: uid(),
        flow_type,
        department: (body.department as ClinicalDepartment | null) ?? null,
        child_subtype: (body.child_subtype as string | null) ?? null,
        consent_given: Boolean(body.consent_given),
        consent_by: (body.consent_by as string | null) ?? null,
        consent_at: body.consent_given ? new Date().toISOString() : null,
      },
    };
    store.patients[patient.id] = patient;
    saveStore(store);
    return patient;
  },

  update(patientId: string, body: Record<string, unknown>): Patient {
    const store = loadStore();
    const existing = store.patients[patientId];
    if (!existing) return this.register(body);
    const age = body.age != null ? Number(body.age) : existing.age;
    const relationship = (body.relationship as UserType) || existing.user_type;
    const updated: Patient = {
      ...existing,
      name: body.name != null ? String(body.name) : existing.name,
      age,
      gender: body.gender != null ? String(body.gender) : existing.gender,
      district: body.district != null ? String(body.district) : existing.district,
      phone: body.phone !== undefined ? (body.phone as string | null) : existing.phone,
      user_type: relationship,
      date_of_birth:
        body.date_of_birth !== undefined ? (body.date_of_birth as string | null) : existing.date_of_birth,
      profile: {
        id: existing.profile?.id ?? uid(),
        flow_type: inferFlow(age, relationship),
        department:
          body.department !== undefined
            ? (body.department as ClinicalDepartment | null)
            : existing.profile?.department ?? null,
        child_subtype:
          body.child_subtype !== undefined
            ? (body.child_subtype as string | null)
            : existing.profile?.child_subtype ?? null,
        consent_given:
          body.consent_given !== undefined ? Boolean(body.consent_given) : Boolean(existing.profile?.consent_given),
        consent_by:
          body.consent_by !== undefined ? (body.consent_by as string | null) : existing.profile?.consent_by ?? null,
        consent_at: existing.profile?.consent_at ?? null,
      },
    };
    store.patients[patientId] = updated;
    saveStore(store);
    return updated;
  },

  categories(flow_type?: FlowType, department?: ClinicalDepartment): Category[] {
    return categories
      .filter((c) => (!flow_type || c.flow_type === flow_type) && (!department || c.department === department))
      .sort((a, b) => a.display_order - b.display_order);
  },

  conditions(categoryId: string): Condition[] {
    return conditions
      .filter((c) => c.category_id === categoryId)
      .sort((a, b) => a.display_order - b.display_order);
  },

  startSession(patientId: string, conditionId: string): SessionState {
    const store = loadStore();
    const condition = conditions.find((c) => c.id === conditionId);
    if (!condition) throw new Error('Condition not found');
    const entry = entryQuestion(conditionId);
    if (!entry) throw new Error('No questions for this condition');
    const patient = store.patients[patientId];
    const session: LocalSession = {
      session_id: uid(),
      patient_id: patientId,
      condition_id: conditionId,
      category_id: condition.category_id,
      status: 'in_progress',
      is_complete: false,
      current_question_id: entry.id,
      answers: [],
      facts: {
        age: patient?.age ?? 0,
      },
      created_at: new Date().toISOString(),
    };
    store.sessions[session.session_id] = session;
    saveStore(store);
    return sessionState(session);
  },

  getSession(sessionId: string): SessionState {
    const store = loadStore();
    const session = store.sessions[sessionId];
    if (!session) throw new Error('Session not found');
    return sessionState(session);
  },

  answer(sessionId: string, questionId: string, optionId: string): SessionState {
    const store = loadStore();
    const session = store.sessions[sessionId];
    if (!session) throw new Error('Session not found');
    const question = questions.find((q) => q.id === questionId);
    const option = options.find((o) => o.id === optionId);
    if (!question || !option) throw new Error('Invalid question or option');

    session.answers = session.answers.filter((a) => a.question_id !== questionId);
    session.answers.push({
      question_id: question.id,
      question_key: question.key,
      question_text: question.text,
      answer_value: option.value,
      answer_label: option.label,
      answered_at: new Date().toISOString(),
    });
    session.facts[question.key] = option.value;

    if (option.is_terminal || !option.next_question_id) {
      session.is_complete = true;
      session.status = 'completed';
      session.current_question_id = null;
      session.completed_at = new Date().toISOString();
    } else {
      session.current_question_id = option.next_question_id;
    }

    store.sessions[sessionId] = session;
    saveStore(store);
    return sessionState(session);
  },

  summary(sessionId: string): SessionSummary {
    const store = loadStore();
    const session = store.sessions[sessionId];
    if (!session) throw new Error('Session not found');
    const patient = store.patients[session.patient_id];
    if (!patient) throw new Error('Patient not found');
    return {
      session_id: session.session_id,
      patient,
      category: categories.find((c) => c.id === session.category_id) ?? null,
      condition: conditions.find((c) => c.id === session.condition_id) ?? null,
      status: session.status,
      answers: session.answers,
      created_at: session.created_at,
      completed_at: session.completed_at ?? null,
    };
  },

  evaluate(sessionId: string): Recommendation {
    const store = loadStore();
    const session = store.sessions[sessionId];
    if (!session) throw new Error('Session not found');

    const applicable = rules
      .filter((r) => !r.condition_id || r.condition_id === session.condition_id)
      .filter((r) => !r.category_id || r.category_id === session.category_id)
      .sort((a, b) => b.priority - a.priority);

    const matched: SnapRule[] = [];
    for (const rule of applicable) {
      if (rule.is_baseline || evaluatePredicate(rule.rule_definition, session.facts)) {
        matched.push(rule);
      }
    }

    const seen = new Set<string>();
    const tests = [];
    for (const rule of matched) {
      const ruleTests = recommendedTests
        .filter((t) => t.rule_id === rule.id)
        .sort((a, b) => a.display_order - b.display_order);
      for (const test of ruleTests) {
        if (seen.has(test.test_code)) continue;
        seen.add(test.test_code);
        const meta = catalogByCode(test.test_code);
        tests.push({
          test_code: test.test_code,
          test_name: test.test_name,
          reason_text: test.reason_text,
          rule_name: rule.name,
          description: meta?.description ?? null,
          preparation: meta?.preparation ?? null,
          duration_minutes: meta?.duration_minutes ?? null,
        });
      }
    }

    const recommendation: Recommendation = {
      session_id: sessionId,
      plan_id: uid(),
      recommended_tests: tests,
      general_recommendations: [
        'Please discuss these screening suggestions with a clinician at NIEPMD.',
        'This tool does not provide a diagnosis.',
      ],
      matched_rule_ids: matched.map((r) => r.id),
      generated_at: new Date().toISOString(),
      disclaimer:
        'These recommendations are generated from clinic screening rules for guidance only and are not a medical diagnosis.',
    };
    store.plans[sessionId] = recommendation;
    saveStore(store);
    return recommendation;
  },

  getRecommendation(sessionId: string): Recommendation {
    const store = loadStore();
    const existing = store.plans[sessionId];
    if (existing) return existing;
    return this.evaluate(sessionId);
  },

  generateReport(sessionId: string): Report {
    const store = loadStore();
    const summary = this.summary(sessionId);
    const recommendation = this.getRecommendation(sessionId);
    const report: Report = {
      id: uid(),
      patient_id: summary.patient.id,
      session_id: sessionId,
      generated_at: new Date().toISOString(),
      download_url: '',
      report_json: {
        patient: summary.patient,
        category: summary.category,
        condition: summary.condition,
        answers: summary.answers,
        recommendations: recommendation,
        mode: 'embedded-clinical',
      },
    };
    store.reports[report.id] = report;
    saveStore(store);
    return report;
  },
};
