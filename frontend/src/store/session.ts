import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type {
  AnswerOut,
  Category,
  Condition,
  Doctor,
  Patient,
  Recommendation,
  Report,
  UserType,
} from '../lib/api';
import { setStoredToken } from '../lib/api';

export type AnswerTrailItem = AnswerOut & { option_id?: string };

type SessionStore = {
  relationship: UserType | null;
  patient: Patient | null;
  sessionId: string | null;
  category: Category | null;
  condition: Condition | null;
  answers: AnswerTrailItem[];
  recommendations: Recommendation | null;
  report: Report | null;
  authToken: string | null;
  doctor: Doctor | null;

  setRelationship: (r: UserType) => void;
  setPatient: (p: Patient | null) => void;
  setSessionId: (id: string | null) => void;
  setCategory: (c: Category | null) => void;
  setCondition: (c: Condition | null) => void;
  pushAnswer: (a: AnswerTrailItem) => void;
  setAnswers: (a: AnswerTrailItem[]) => void;
  setRecommendations: (r: Recommendation | null) => void;
  setReport: (r: Report | null) => void;
  setAuth: (token: string | null, doctor?: Doctor | null) => void;
  resetClinical: () => void;
  logout: () => void;
};

export const useSessionStore = create<SessionStore>()(
  persist(
    (set) => ({
      relationship: null,
      patient: null,
      sessionId: null,
      category: null,
      condition: null,
      answers: [],
      recommendations: null,
      report: null,
      authToken: null,
      doctor: null,

      setRelationship: (relationship) => set({ relationship }),
      setPatient: (patient) => set({ patient }),
      setSessionId: (sessionId) => set({ sessionId }),
      setCategory: (category) => set({ category }),
      setCondition: (condition) => set({ condition }),
      pushAnswer: (a) => set((s) => ({ answers: [...s.answers, a] })),
      setAnswers: (answers) => set({ answers }),
      setRecommendations: (recommendations) => set({ recommendations }),
      setReport: (report) => set({ report }),
      setAuth: (token, doctor = null) => {
        setStoredToken(token);
        set({ authToken: token, doctor });
      },
      resetClinical: () =>
        set({
          relationship: null,
          patient: null,
          sessionId: null,
          category: null,
          condition: null,
          answers: [],
          recommendations: null,
          report: null,
        }),
      logout: () => {
        setStoredToken(null);
        set({ authToken: null, doctor: null });
      },
    }),
    {
      name: 'niepmd-session-v2',
      // Only keep admin login across reloads. Patient registration and Take Test
      // progress must not survive a refresh (privacy + empty form on revisit).
      partialize: (s) => ({
        authToken: s.authToken,
        doctor: s.doctor,
      }),
    },
  ),
);
