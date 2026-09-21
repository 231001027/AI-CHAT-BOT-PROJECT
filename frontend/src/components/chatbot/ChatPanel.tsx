// @refresh reset
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import { Send, User, Sparkles, RotateCcw, WifiOff, Ear, BellRing, CircleDashed, Activity, Baby, CheckCircle2, ClipboardList, FlaskConical, ShieldCheck, Volume2, EarOff, Headphones, Gauge, Stethoscope } from 'lucide-react';

const ASSISTANT_PHOTO = '/assistant.png';
import { sendChatMessage } from '../../services/api';
import { getQASession, getQAAnswerOptions, getQARecommendedTests } from '../../services/qaSession';
import { specialTests, generalRecommendations, adultSpeechSections } from '../../data/hearingData';
import { childSpeechCategories } from '../../data/childData';
import { createChatSession, saveChatMessage as dbSaveMessage } from '../../services/db';

const SPEECH_TOPIC_IDS = new Set([
  ...adultSpeechSections.map((s) => s.id),
  ...childSpeechCategories.map((s) => s.id),
]);

function isSpeechTopic(topicId: string | undefined): boolean {
  return Boolean(topicId && SPEECH_TOPIC_IDS.has(topicId));
}

const TAKE_TEST_PATH = '/register/relationship';

/** Follow-ups that should open the Take Test flow instead of sending a chat message. */
function isTakeTestFollowup(label: string): boolean {
  const t = label.toLowerCase();
  if (t.includes('take test')) return true;
  if (/\bbook\b/.test(t) && (/\btest\b/.test(t) || /\bassessment\b/.test(t) || /\bscreening\b/.test(t))) {
    return true;
  }
  if (t.includes('schedule screening') || t.includes('schedule assessment')) return true;
  return false;
}

export interface ChatMessage {
  id: number;
  role: 'bot' | 'user';
  text: string;
  followups?: string[];
  showTopicCards?: boolean;
  /** Present on Q&A question messages — tracks which question this is */
  qaSession?: { topicId: string; questionIndex: number };
  /** Present on the final summary message */
  qaSummary?: { topicId: string };
}

// ─── Topic cards (shown on default greeting) ────────────────────────────────

interface TopicCard {
  icon: React.ElementType;
  title: string;
  symptoms: string[];
  message: string;
  color: string;
  iconBg: string;
}

const TOPIC_CARDS: TopicCard[] = [
  {
    icon: Ear,
    title: 'Hearing Difficulty',
    symptoms: ['Not hearing well', 'Muffled sounds', 'Need to ask people to repeat'],
    message: "I have hearing difficulty — I can't hear well and sounds seem muffled",
    color: 'border-blue-200 hover:border-blue-400 dark:border-blue-800 dark:hover:border-blue-500',
    iconBg: 'bg-blue-50 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300',
  },
  {
    icon: BellRing,
    title: 'Ringing in Ears (Tinnitus)',
    symptoms: ['Ringing or noise in ears', 'Buzzing / Hissing sound', 'Comes and goes'],
    message: 'I hear ringing, buzzing or hissing sounds in my ears (tinnitus)',
    color: 'border-purple-200 hover:border-purple-400 dark:border-purple-800 dark:hover:border-purple-500',
    iconBg: 'bg-purple-50 text-purple-600 dark:bg-purple-900/40 dark:text-purple-300',
  },
  {
    icon: CircleDashed,
    title: 'Dizziness / Balance Problem',
    symptoms: ['Feeling dizzy', 'Room spinning', 'Unsteady walking'],
    message: 'I feel dizzy, the room is spinning and I have balance problems',
    color: 'border-pink-200 hover:border-pink-400 dark:border-pink-800 dark:hover:border-pink-500',
    iconBg: 'bg-pink-50 text-pink-600 dark:bg-pink-900/40 dark:text-pink-300',
  },
  {
    icon: Activity,
    title: 'Ear Pain / Discharge',
    symptoms: ['Ear pain', 'Discharge', 'Fullness in ear', 'Ear infection'],
    message: 'I have ear pain, discharge and a feeling of fullness in my ear',
    color: 'border-orange-200 hover:border-orange-400 dark:border-orange-800 dark:hover:border-orange-500',
    iconBg: 'bg-orange-50 text-orange-600 dark:bg-orange-900/40 dark:text-orange-300',
  },
  {
    icon: Baby,
    title: 'Child Concerns',
    symptoms: ['Not responding to sounds', 'Delayed speech', 'Frequent ear infections'],
    message: 'My child is not responding to sounds and has delayed speech',
    color: 'border-green-200 hover:border-green-400 dark:border-green-800 dark:hover:border-green-500',
    iconBg: 'bg-green-50 text-green-600 dark:bg-green-900/40 dark:text-green-300',
  },
];

// ─── Props ───────────────────────────────────────────────────────────────────

interface ChatPanelProps {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  className?: string;
  compact?: boolean;
  /** If set, the panel runs in guided Q&A mode for this topic id */
  qaTopicId?: string;
}

import { createInitialMessages } from './chatUtils';

export function ChatPanel({ messages, setMessages, className, compact = false, qaTopicId }: ChatPanelProps) {
  const navigate = useNavigate();
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const idRef = useRef(1);
  // API session id for the current Q&A — created lazily on first user answer
  const dbSessionIdRef = useRef<string | null>(null);

  // Keep id counter in sync when messages are replaced externally (e.g. topic switch)
  useEffect(() => {
    const maxId = messages.reduce((m, msg) => Math.max(m, msg.id), 0);

    idRef.current = maxId + 1;
  }, [messages]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, typing]);

  // Listen for suggestion events (from sidebar buttons on AI Assistant page)
  useEffect(() => {
    const onSuggestion = (e: Event) => {
      const detail = (e as CustomEvent<string>).detail;
      if (typeof detail === 'string') sendFreeText(detail);
    };
    window.addEventListener('hc-suggestion', onSuggestion as EventListener);
    return () => window.removeEventListener('hc-suggestion', onSuggestion as EventListener);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [typing]);

  // ── Q&A helpers ────────────────────────────────────────────────────────────

  /**
   * After the user answers a Q&A question, find the next question and post it,
   * or post the final summary if all questions have been answered.
   */
  const advanceQA = (topicId: string, answeredIndex: number) => {
    const session = getQASession(topicId);
    if (!session) return;

    const nextIndex = answeredIndex + 1;

    if (nextIndex < session.questions.length) {
      window.setTimeout(() => {
        const nextQ = session.questions[nextIndex];
        setMessages((prev) => [
          ...prev,
          { id: idRef.current++, role: 'bot', text: nextQ, qaSession: { topicId, questionIndex: nextIndex } },
        ]);
        setTyping(false);
      }, 700);
    } else {
      // All questions answered → post summary
      window.setTimeout(() => {
        const summaryText = `Thank you for answering all the questions! 🎉\n\nBased on your responses about **${session.topicTitle}**, here are the recommended next steps:`;
        setMessages((prev) => [
          ...prev,
          { id: idRef.current++, role: 'bot', text: summaryText, qaSummary: { topicId } },
        ]);
        // Save summary message to Supabase
        if (dbSessionIdRef.current) {
          dbSaveMessage({ session_id: dbSessionIdRef.current, role: 'bot', message: summaryText });
        }
        setTyping(false);
      }, 700);
    }
  };

  // ── Send: Q&A mode ─────────────────────────────────────────────────────────

  const sendQAAnswer = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || typing) return;

    // Find the last bot message that has a qaSession tag — that's the current question
    const lastQAMsg = [...messages].reverse().find((m) => m.role === 'bot' && m.qaSession);

    setApiError(null);
    setMessages((prev) => [...prev, { id: idRef.current++, role: 'user', text: trimmed }]);
    setInput('');
    setTyping(true);

    // ── Supabase: create session on first answer, then save bot question + user answer ──
    if (qaTopicId) {
      const qaSession = getQASession(qaTopicId);

      // Create the DB session row the first time a user answers
      if (!dbSessionIdRef.current && qaSession) {
        const sid = await createChatSession({
          topic_id:    qaTopicId,
          topic_title: qaSession.topicTitle,
        });
        dbSessionIdRef.current = sid;
      }

      if (dbSessionIdRef.current && lastQAMsg?.qaSession) {
        const sid = dbSessionIdRef.current;
        const qi  = lastQAMsg.qaSession.questionIndex;
        // Save the bot question
        dbSaveMessage({ session_id: sid, role: 'bot', message: lastQAMsg.text, question_index: qi });
        // Save the user answer
        dbSaveMessage({ session_id: sid, role: 'user', message: trimmed, question_index: qi });
      }
    }

    if (lastQAMsg?.qaSession) {
      advanceQA(lastQAMsg.qaSession.topicId, lastQAMsg.qaSession.questionIndex);
    } else {
      setTyping(false);
    }
  };

  // ── Send: free-text AI mode ────────────────────────────────────────────────

  const sendFreeText = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || typing) return;

    setApiError(null);
    setMessages((prev) => [...prev, { id: idRef.current++, role: 'user', text: trimmed }]);
    setInput('');
    setTyping(true);

    try {
      const data = await sendChatMessage(trimmed);
      setMessages((prev) => [
        ...prev,
        { id: idRef.current++, role: 'bot', text: data.response, followups: data.followups },
      ]);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setApiError(message);
      setMessages((prev) => [
        ...prev,
        { id: idRef.current++, role: 'bot', text: "Sorry, I couldn't reach the server. Please check your connection and try again." },
      ]);
    } finally {
      setTyping(false);
    }
  };

  // ── Unified send dispatcher ────────────────────────────────────────────────

  const send = (text: string) => {
    if (qaTopicId) {
      // Check if we're still in the question phase (summary not yet shown)
      const summaryShown = messages.some((m) => m.qaSummary);
      if (!summaryShown) {
        sendQAAnswer(text);
        return;
      }
    }
    sendFreeText(text);
  };

  const reset = () => {
    idRef.current = 1;
    dbSessionIdRef.current = null;
    setMessages(createInitialMessages());
    setInput('');
    setTyping(false);
    setApiError(null);
  };

  // ── Check if Q&A is complete (summary shown) ──────────────────────────────
  const qaSummaryMsg = messages.find((m) => m.qaSummary);
  const qaSession = qaTopicId ? getQASession(qaTopicId) : null;

  // Count answered questions
  const answeredCount = messages.filter((m) => m.role === 'user').length;
  const totalQuestions = qaSession?.questions.length ?? 0;

  const lastQAMsg = [...messages].reverse().find((m) => m.role === 'bot' && m.qaSession);
  const currentAnswerOptions =
    qaSession && lastQAMsg?.qaSession && !qaSummaryMsg && !typing
      ? getQAAnswerOptions(qaSession, lastQAMsg.qaSession.questionIndex)
      : null;
  const speechSummary = isSpeechTopic(qaTopicId);
  const qaAnswers = messages.filter((m) => m.role === 'user').map((m) => m.text);
  const recommendedTests = qaSession ? getQARecommendedTests(qaSession, qaAnswers) : [];

  return (
    <div className={`flex flex-col min-h-0 ${className ?? ''}`}>

      {/* Q&A progress bar */}
      {qaTopicId && qaSession && !qaSummaryMsg && (
        <div className="border-b border-slate-200 dark:border-slate-700 px-4 py-2 bg-slate-50 dark:bg-slate-900/60">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400 mb-1">
            <span>{qaSession.topicTitle}</span>
            <span>{Math.min(answeredCount, totalQuestions)} / {totalQuestions} answered</span>
          </div>
          <div className="h-1.5 rounded-full bg-slate-200 dark:bg-slate-700 overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-brand-500 to-purple-500"
              animate={{ width: `${(Math.min(answeredCount, totalQuestions) / totalQuestions) * 100}%` }}
              transition={{ duration: 0.4 }}
            />
          </div>
        </div>
      )}

      {/* Messages */}
      <div
        ref={scrollRef}
        className={`flex-1 overflow-y-auto scrollbar-thin space-y-4 ${compact ? 'p-3' : 'p-5'}`}
        role="log"
        aria-live="polite"
        aria-label="Chat conversation"
      >
        <AnimatePresence initial={false}>
          {messages.map((m) => (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 12, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              transition={{ duration: 0.25 }}
              className={`flex gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
            >
              {m.role === 'bot' ? (
                <img
                  src={ASSISTANT_PHOTO}
                  alt=""
                  className="h-8 w-8 shrink-0 rounded-full bg-white object-contain object-center ring-1 ring-brand-200"
                />
              ) : (
                <span
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-200"
                  aria-hidden="true"
                >
                  <User size={16} />
                </span>
              )}

              <div className={m.role === 'user' ? 'max-w-[80%] items-end' : 'flex-1 min-w-0'}>
                {/* Message bubble */}
                <div
                  className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed whitespace-pre-line ${
                    m.role === 'bot'
                      ? m.qaSession
                        ? 'bg-brand-50 border-2 border-brand-200 text-slate-800 dark:bg-brand-900/20 dark:border-brand-700 dark:text-slate-100 rounded-tl-sm font-medium'
                        : 'bg-white border border-slate-200 text-slate-700 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 rounded-tl-sm'
                      : 'bg-brand-600 text-white rounded-tr-sm'
                  }`}
                >
                  {m.text}
                </div>

                {/* Q&A summary card */}
                {m.qaSummary && qaSession && (
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 }}
                    className="mt-3 rounded-2xl border-2 border-brand-200 dark:border-brand-700 bg-white dark:bg-slate-800 overflow-hidden"
                  >
                    {/* ── Recommended Tests ── */}
                    <div className="bg-gradient-to-r from-brand-600 to-purple-600 px-4 py-2.5">
                      <p className="text-xs font-bold text-white uppercase tracking-wide flex items-center gap-1.5">
                        <ClipboardList size={13} /> Recommended Tests
                      </p>
                    </div>
                    <ul className="px-4 py-3 space-y-1.5">
                      {recommendedTests.map((t) => (
                        <li key={t} className="flex items-start gap-2 text-sm text-slate-700 dark:text-slate-200">
                          <CheckCircle2 size={14} className="mt-0.5 shrink-0 text-green-500" />
                          {t}
                        </li>
                      ))}
                    </ul>
                    <div className="border-t border-slate-100 dark:border-slate-700 px-4 py-3">
                      <p className="text-xs text-slate-500 dark:text-slate-400 italic">{qaSession.whatItHelps}</p>
                    </div>

                    {!speechSummary && (
                      <>
                        {/* ── Special Tests (Non-Speech) ── */}
                        <div className="border-t border-slate-100 dark:border-slate-700">
                          <div className="bg-brand-600 px-4 py-2">
                            <p className="text-xs font-bold text-white uppercase tracking-wide flex items-center gap-1.5">
                              <FlaskConical size={12} /> Special Tests (Non-Speech)
                            </p>
                          </div>
                          <div className="grid grid-cols-2 gap-2 p-3 sm:grid-cols-3">
                            {specialTests.filter(t => ['ABR','MLR','LLR','P300','P500'].includes(t.code)).map((t) => (
                              <div key={t.code} className="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2.5">
                                <p className="text-xs font-bold text-slate-800 dark:text-slate-100">{t.code}</p>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">{t.name}</p>
                                <p className="text-[10px] text-slate-600 dark:text-slate-300 mt-1 leading-tight">{t.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* ── Special Speech Audiometry Tests ── */}
                        <div className="border-t border-slate-100 dark:border-slate-700">
                          <div className="bg-purple-600 px-4 py-2">
                            <p className="text-xs font-bold text-white uppercase tracking-wide flex items-center gap-1.5">
                              <FlaskConical size={12} /> Special Speech Audiometry Tests
                            </p>
                          </div>
                          <div className="grid grid-cols-2 gap-2 p-3 sm:grid-cols-4">
                            {specialTests.filter(t => ['SRT','WRS','PB Test','SPIN'].includes(t.code)).map((t) => (
                              <div key={t.code} className="rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2.5">
                                <p className="text-xs font-bold text-slate-800 dark:text-slate-100">{t.code}</p>
                                <p className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5 leading-tight">{t.name}</p>
                                <p className="text-[10px] text-slate-600 dark:text-slate-300 mt-1 leading-tight">{t.description}</p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* ── General Recommendations ── */}
                        <div className="border-t border-slate-100 dark:border-slate-700">
                          <div className="bg-gradient-to-r from-slate-700 to-slate-800 px-4 py-2">
                            <p className="text-xs font-bold text-white uppercase tracking-wide flex items-center gap-1.5">
                              <ShieldCheck size={12} /> General Recommendations
                            </p>
                          </div>
                          <div className="grid grid-cols-2 gap-2 p-3 sm:grid-cols-3">
                            {generalRecommendations.map((r) => (
                              <div key={r.title} className="flex items-center gap-2 rounded-lg bg-slate-50 dark:bg-slate-700/50 p-2.5">
                                <r.icon size={14} className="shrink-0 text-brand-500" />
                                <p className="text-[11px] font-medium text-slate-700 dark:text-slate-200 leading-tight">{r.title}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </>
                    )}

                    {/* ── Next step ── */}
                    <div className="border-t border-slate-100 dark:border-slate-700 bg-brand-50 dark:bg-brand-900/20 px-4 py-3 flex items-center gap-2">
                      <CheckCircle2 size={15} className="text-brand-600 dark:text-brand-300 shrink-0" />
                      <p className="text-xs font-semibold text-brand-700 dark:text-brand-300">
                        {speechSummary
                          ? qaTopicId?.includes('voice') || qaTopicId?.includes('swallow')
                            ? 'Please consult a Speech-Language Pathologist / ENT for proper evaluation and advice.'
                            : 'Please consult a Speech-Language Pathologist for proper evaluation and advice.'
                          : 'Please consult an Audiologist / ENT for proper evaluation and advice.'}
                      </p>
                    </div>
                  </motion.div>
                )}

                {/* Topic cards on default greeting */}
                {m.showTopicCards && (
                  <div className={`mt-3 grid gap-2 ${compact ? 'grid-cols-1' : 'grid-cols-2 sm:grid-cols-3'}`}>
                    {TOPIC_CARDS.map((card) => (
                      <button
                        key={card.title}
                        type="button"
                        onClick={() => send(card.message)}
                        disabled={typing}
                        className={`group flex flex-col gap-2 rounded-xl border-2 bg-white dark:bg-slate-800 p-3 text-left transition-all duration-150 hover:shadow-md disabled:opacity-50 disabled:pointer-events-none ${card.color}`}
                      >
                        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${card.iconBg}`}>
                          <card.icon size={15} />
                        </span>
                        <span className="text-xs font-semibold text-slate-800 dark:text-slate-100 leading-tight">
                          {card.title}
                        </span>
                        <ul className="space-y-0.5">
                          {card.symptoms.map((s) => (
                            <li key={s} className="flex items-start gap-1 text-[11px] text-slate-500 dark:text-slate-400">
                              <span className="mt-0.5 text-brand-400">✓</span>
                              {s}
                            </li>
                          ))}
                        </ul>
                      </button>
                    ))}
                  </div>
                )}

                {/* Follow-up chips */}
                {m.followups && m.followups.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {m.followups.map((f) => (
                      <button
                        key={f}
                        type="button"
                        onClick={() => {
                          if (isTakeTestFollowup(f)) {
                            navigate(TAKE_TEST_PATH);
                            return;
                          }
                          send(f);
                        }}
                        className="chip bg-brand-50 text-brand-700 hover:bg-brand-100 dark:bg-brand-900/40 dark:text-brand-200 dark:hover:bg-brand-900/60 transition-colors"
                      >
                        <Sparkles size={11} />
                        {f}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {/* Typing indicator */}
        {typing && (
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="flex gap-2.5">
            <img
              src={ASSISTANT_PHOTO}
              alt=""
              className="h-8 w-8 rounded-full bg-white object-contain object-center ring-1 ring-brand-200"
            />
            <div className="rounded-2xl rounded-tl-sm bg-white border border-slate-200 dark:bg-slate-800 dark:border-slate-700 px-4 py-3">
              <div className="flex items-center gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="h-1.5 w-1.5 rounded-full bg-brand-400"
                    animate={{ y: [0, -4, 0] }}
                    transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* API error */}
      {apiError && (
        <div className="flex items-center gap-2 bg-red-50 dark:bg-red-900/30 border-t border-red-200 dark:border-red-800 px-4 py-2 text-xs text-red-600 dark:text-red-300">
          <WifiOff size={13} className="shrink-0" aria-hidden="true" />
          <span>API error: {apiError}</span>
        </div>
      )}

      {/* Input */}
      <div className={`border-t border-slate-200 dark:border-slate-700 ${compact ? 'p-3' : 'p-4'}`}>
        {currentAnswerOptions && currentAnswerOptions.length > 0 && (
          <div className="mb-3 flex flex-wrap gap-2" role="group" aria-label="Quick answers">
            {currentAnswerOptions.map((opt) => (
              <button
                key={opt}
                type="button"
                disabled={typing}
                onClick={() => send(opt)}
                className="rounded-xl border-2 border-brand-200 bg-brand-50 px-4 py-2 text-sm font-semibold text-brand-800 hover:bg-brand-100 hover:border-brand-400 disabled:opacity-50 dark:border-brand-700 dark:bg-brand-900/30 dark:text-brand-100 dark:hover:bg-brand-900/50 transition-colors"
              >
                {opt}
              </button>
            ))}
          </div>
        )}
        <form
          onSubmit={(e) => { e.preventDefault(); send(input); }}
          className="flex items-center gap-2"
        >
          <button
            type="button"
            onClick={reset}
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg text-slate-400 hover:text-brand-600 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Reset conversation"
            title="Reset conversation"
          >
            <RotateCcw size={16} />
          </button>
          <label htmlFor="chat-input" className="sr-only">Type your message</label>
          <input
            id="chat-input"
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              qaTopicId && !qaSummaryMsg
                ? 'Type your answer...'
                : 'Describe your hearing concern...'
            }
            className="flex-1 rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900"
          />
          <button
            type="submit"
            disabled={!input.trim() || typing}
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-600 text-white hover:bg-brand-700 disabled:opacity-50 disabled:pointer-events-none transition-colors"
            aria-label="Send message"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}
