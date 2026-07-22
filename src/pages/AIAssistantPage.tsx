import { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Bot, Sparkles, ShieldCheck, RefreshCw, MessageSquareHeart } from 'lucide-react';
import { useSearchParams } from 'react-router-dom';
import { PageHero } from '../components/ui/PageHero';
import { Reveal } from '../components/ui/Reveal';
import { ChatPanel, type ChatMessage } from '../components/chatbot/ChatPanel';
import { createInitialMessages } from '../components/chatbot/chatUtils';
import { getQASession } from '../services/qaSession';

const suggestions = [
  'My child is not responding to sounds',
  'I hear ringing in my ears constantly',
  'I feel dizzy and the room spins',
  'My child has delayed speech',
  'I have ear pain and fluid coming out',
  "I can't hear clearly in noisy places",
];

const guarantees = [
  { icon: ShieldCheck,        title: 'Secure connection',  desc: 'All conversations are transmitted over encrypted HTTPS.' },
  { icon: RefreshCw,          title: 'Reset anytime',      desc: 'Start a fresh conversation whenever you like.' },
  { icon: MessageSquareHeart, title: 'Judgement-free',     desc: 'Ask anything, in your own words. There are no silly questions.' },
];

/** Build the initial message list for a guided Q&A session.
 *  If `signText` is provided it is pre-injected as the first user answer
 *  so the bot immediately moves to question 2.
 */
function createQAMessages(topicId: string, signText?: string): ChatMessage[] {
  const session = getQASession(topicId);
  if (!session) return createInitialMessages();

  const intro: ChatMessage = {
    id: 0,
    role: 'bot',
    text: `Hello 👋 I'll ask you a few questions about your **${session.topicTitle}** concern to help guide you.\n\nLet's start with the first question:`,
  };

  const firstQuestion: ChatMessage = {
    id: 1,
    role: 'bot',
    text: session.questions[0],
    qaSession: { topicId, questionIndex: 0 },
  };

  if (!signText) return [intro, firstQuestion];

  // Pre-answer the first question with the clicked sign text
  const userAnswer: ChatMessage = { id: 2, role: 'user', text: signText };

  if (session.questions.length > 1) {
    // Move immediately to question 2
    return [
      intro,
      firstQuestion,
      userAnswer,
      { id: 3, role: 'bot', text: session.questions[1], qaSession: { topicId, questionIndex: 1 } },
    ];
  }

  // Only one question — show summary directly
  return [
    intro,
    firstQuestion,
    userAnswer,
    {
      id: 3,
      role: 'bot',
      text: `Thank you! Based on your response about **${session.topicTitle}**, here are the recommended next steps:`,
      qaSummary: { topicId },
    },
  ];
}

export function AIAssistantPage() {
  const [searchParams] = useSearchParams();
  const topicId = searchParams.get('topic') ?? '';
  const signText = searchParams.get('sign') ?? '';

  // Build initial messages based on whether a topic was passed
  const initialMessages = useMemo<ChatMessage[]>(() => {
    if (topicId) return createQAMessages(topicId, signText || undefined);
    return createInitialMessages();
  }, [topicId]);

  const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);

  // When topicId changes (user navigates to a different topic without remounting),
  // reset the conversation
  const [lastTopicId, setLastTopicId] = useState(topicId);
  if (topicId !== lastTopicId) {
    setLastTopicId(topicId);
    setMessages(topicId ? createQAMessages(topicId, signText || undefined) : createInitialMessages());
  }

  const session = topicId ? getQASession(topicId) : null;

  return (
    <>
      <PageHero
        eyebrow={session ? `${session.topicTitle} assessment` : 'AI assistant'}
        title={session ? `${session.topicTitle} — Q&A` : 'Talk to HearConnect AI'}
        description={
          session
            ? `Answer a few guided questions about your ${session.topicTitle.toLowerCase()} concern and get personalised next steps.`
            : 'Describe a hearing concern in plain words and get caring, instant guidance. This assistant does not replace a professional medical diagnosis.'
        }
        crumbs={[
          { label: 'Home', to: '/' },
          ...(session ? [{ label: 'Adult Care', to: '/adult-care' }] : []),
          { label: session ? session.topicTitle : 'AI Assistant' },
        ]}
        accent="purple"
        icon={<Bot size={13} />}
      />

      <section className="container-page py-12 sm:py-16">
        <div className="grid gap-8 lg:grid-cols-3">
          {/* ── Chat panel ── */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="card overflow-hidden flex flex-col"
              style={{ height: 'calc(100vh - 220px)', minHeight: '520px' }}
            >
              <div className="flex items-center gap-3 bg-gradient-to-r from-brand-600 to-purple-600 px-5 py-3.5 text-white">
                <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20">
                  <Bot size={18} />
                </span>
                <div className="flex-1">
                  <p className="text-sm font-semibold leading-none">HearConnect AI</p>
                  <p className="mt-1 text-xs text-white/80 flex items-center gap-1.5">
                    <span className="h-1.5 w-1.5 rounded-full bg-green-400 animate-pulse" />
                    {session ? `Guided Q&A · ${session.topicTitle}` : 'Online · AI assistant'}
                  </p>
                </div>
              </div>
              <ChatPanel
                messages={messages}
                setMessages={setMessages}
                className="flex-1"
                qaTopicId={topicId || undefined}
              />
            </motion.div>
          </div>

          {/* ── Sidebar ── */}
          <div className="space-y-6">
            {/* If a topic session → show tests panel */}
            {session ? (
              <>
                <Reveal delay={0.1}>
                  <div className="card p-5">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">How this works</h3>
                    <ul className="mt-3 space-y-3">
                      {[
                        'The AI asks you one question at a time',
                        'Answer in your own words — no right or wrong',
                        'After all questions, you\'ll see your recommended next steps',
                      ].map((s) => (
                        <li key={s} className="flex gap-2.5 text-sm text-slate-600 dark:text-slate-300">
                          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-400" />
                          {s}
                        </li>
                      ))}
                    </ul>
                  </div>
                </Reveal>
              </>
            ) : (
              <>
                {/* Default sidebar */}
                <Reveal>
                  <div className="card p-5">
                    <h3 className="flex items-center gap-2 text-sm font-semibold text-slate-900 dark:text-white">
                      <Sparkles size={16} className="text-brand-500" /> Try asking about
                    </h3>
                    <ul className="mt-3 space-y-2">
                      {suggestions.map((s) => (
                        <li key={s}>
                          <button
                            type="button"
                            onClick={() => {
                              window.dispatchEvent(new CustomEvent('hc-suggestion', { detail: s }));
                            }}
                            className="w-full text-left text-sm text-slate-600 dark:text-slate-300 rounded-lg border border-slate-200 dark:border-slate-700 px-3 py-2 hover:border-brand-300 hover:text-brand-700 dark:hover:text-brand-300 transition-colors"
                          >
                            {s}
                          </button>
                        </li>
                      ))}
                    </ul>
                  </div>
                </Reveal>

                <Reveal delay={0.1}>
                  <div className="card p-5">
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">What to expect</h3>
                    <ul className="mt-3 space-y-3">
                      {guarantees.map((g) => (
                        <li key={g.title} className="flex gap-3">
                          <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-200">
                            <g.icon size={15} />
                          </span>
                          <div>
                            <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{g.title}</p>
                            <p className="text-xs text-slate-500 dark:text-slate-400">{g.desc}</p>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </div>
                </Reveal>
              </>
            )}
          </div>
        </div>
      </section>
    </>
  );
}
