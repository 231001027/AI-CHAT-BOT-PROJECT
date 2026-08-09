import { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import {
  api,
  ApiError,
  type Option,
  type Question,
  type SessionState,
  type SessionSummary,
} from '../../lib/api';
import { useSessionStore } from '../../store/session';
import { ProgressStepper } from '../../components/shared/ProgressStepper';
import { QuestionCard } from '../../components/shared/QuestionCard';
import { Button } from '../../components/ui/Button';

export function QuestionnairePage() {
  const navigate = useNavigate();
  const { patient, condition, sessionId, setSessionId, setAnswers } = useSessionStore();
  const [state, setState] = useState<SessionState | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patient || !condition) {
      navigate('/register/relationship');
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        let next: SessionState;
        if (sessionId) {
          next = await api.get<SessionState>(`/api/sessions/${sessionId}`, false);
        } else {
          next = await api.post<SessionState>(
            '/api/sessions',
            { patient_id: patient.id, condition_id: condition.id },
            false,
          );
          if (!cancelled) setSessionId(next.session_id);
        }
        if (!cancelled) setState(next);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : 'Could not start the questionnaire.');
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [patient, condition, sessionId, setSessionId, navigate]);

  async function answer(question: Question, option: Option) {
    if (!state || submitting) return;
    setSubmitting(true);
    setError(null);
    try {
      const next = await api.post<SessionState>(
        `/api/sessions/${state.session_id}/answers`,
        { question_id: question.id, option_id: option.id },
        false,
      );
      setState(next);
      if (next.is_complete) {
        const summary = await api.get<SessionSummary>(
          `/api/sessions/${state.session_id}/summary`,
          false,
        );
        setAnswers(summary.answers || []);
        navigate('/chat/summary');
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not save that answer.');
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center text-slate-600">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading questions…
      </div>
    );
  }

  if (error && !state) {
    return (
      <div className="mx-auto max-w-lg px-4 py-16 text-center">
        <p className="text-red-700">{error}</p>
        <Button asChild className="mt-4" variant="outline">
          <Link to="/chat/category">Back to categories</Link>
        </Button>
      </div>
    );
  }

  const question = state?.question;
  const progress = state?.progress;

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <ProgressStepper current="questions" />
      <p className="mt-2 text-sm text-slate-500">
        {condition?.name}
        {progress ? ` · ${progress.answered} of ~${progress.total}` : null}
      </p>
      {progress ? (
        <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-500 transition-all"
            style={{
              width: `${Math.min(100, (progress.answered / Math.max(progress.total, 1)) * 100)}%`,
            }}
          />
        </div>
      ) : null}

      {error ? <p className="mt-4 text-sm text-red-700">{error}</p> : null}

      {question ? (
        <div className="mt-8">
          <QuestionCard
            question={question}
            disabled={submitting}
            onSelect={(option) => answer(question, option)}
          />
        </div>
      ) : (
        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 text-center">
          <p className="text-slate-700">All questions answered.</p>
          <Button className="mt-4" onClick={() => navigate('/chat/summary')}>
            Review answers
          </Button>
        </div>
      )}
    </div>
  );
}
