import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AnimatePresence, motion } from 'framer-motion';
import {
  User,
  Baby,
  Users,
  ChevronDown,
  Search,
  ArrowRight,
  ArrowLeft,
  Check,
  Sparkles,
  Bot,
  User as UserIcon,
  Stethoscope,
  CalendarCheck,
  RotateCcw,
  Ear,
  BellRing,
  CircleDashed,
  Activity,
} from 'lucide-react';
import { PageHero } from '../components/ui/PageHero';
import { AccentIcon } from '../components/ui/AccentIcon';
import { Button, LinkButton } from '../components/ui/Button';
import { sendChatMessage } from '../services/api';
import { hearingProblems } from '../data/hearingData';
import { ALL_DISTRICTS } from '../data/indianDistricts';

type Audience = 'myself' | 'child' | 'someone';
type StepId = 1 | 2 | 3 | 4;

interface FormData {
  fullName: string;
  district: string;
  age: string;
  gender: string;
  phone: string;
}

const audienceCards: { id: Audience; label: string; icon: typeof User; desc: string; accent: 'blue' | 'purple' | 'green' }[] = [
  { id: 'myself', label: 'Myself', icon: User, desc: 'I am experiencing hearing concerns', accent: 'blue' },
  { id: 'child', label: 'My Child', icon: Baby, desc: 'My child may have a hearing issue', accent: 'purple' },
  { id: 'someone', label: 'Someone Else', icon: Users, desc: 'I am caring for another person', accent: 'green' },
];

const stepsMeta: { id: StepId; label: string }[] = [
  { id: 1, label: 'Who needs help' },
  { id: 2, label: 'Your details' },
  { id: 3, label: 'Chat with AI' },
  { id: 4, label: 'Your pathway' },
];

const emptyForm: FormData = { fullName: '', district: '', age: '', gender: '', phone: '' };

interface ChatMsg {
  id: number;
  role: 'bot' | 'user';
  text: string;
  followups?: string[];
  showTopicCards?: boolean;
}

interface TopicCard {
  icon: React.ElementType;
  title: string;
  symptoms: string[];
  message: string;
  route?: string;        // if set → navigate there instead of sending a chat message
  color: string;
  iconBg: string;
}

const TOPIC_CARDS: TopicCard[] = [
  {
    icon: Ear,
    title: 'Hearing Difficulty',
    symptoms: ['Not hearing well', 'Muffled sounds', 'Need to ask people to repeat'],
    message: "I have hearing difficulty — I can't hear well and sounds seem muffled",
    route: '/adult-care#hearing-difficulty',
    color: 'border-blue-200 hover:border-blue-400 dark:border-blue-800 dark:hover:border-blue-500',
    iconBg: 'bg-blue-50 text-blue-600 dark:bg-blue-900/40 dark:text-blue-300',
  },
  {
    icon: BellRing,
    title: 'Ringing in Ears (Tinnitus)',
    symptoms: ['Ringing or noise in ears', 'Buzzing / Hissing sound', 'Comes and goes'],
    message: 'I hear ringing, buzzing or hissing sounds in my ears (tinnitus)',
    route: '/adult-care#tinnitus',
    color: 'border-purple-200 hover:border-purple-400 dark:border-purple-800 dark:hover:border-purple-500',
    iconBg: 'bg-purple-50 text-purple-600 dark:bg-purple-900/40 dark:text-purple-300',
  },
  {
    icon: CircleDashed,
    title: 'Dizziness / Balance Problem',
    symptoms: ['Feeling dizzy', 'Room spinning', 'Unsteady walking'],
    message: 'I feel dizzy, the room is spinning and I have balance problems',
    route: '/adult-care#balance-problems',
    color: 'border-pink-200 hover:border-pink-400 dark:border-pink-800 dark:hover:border-pink-500',
    iconBg: 'bg-pink-50 text-pink-600 dark:bg-pink-900/40 dark:text-pink-300',
  },
  {
    icon: Activity,
    title: 'Ear Pain / Discharge',
    symptoms: ['Ear pain', 'Discharge', 'Fullness in ear', 'Ear infection'],
    message: 'I have ear pain, discharge and a feeling of fullness in my ear',
    route: '/adult-care#ear-pain',
    color: 'border-orange-200 hover:border-orange-400 dark:border-orange-800 dark:hover:border-orange-500',
    iconBg: 'bg-orange-50 text-orange-600 dark:bg-orange-900/40 dark:text-orange-300',
  },
  {
    icon: Baby,
    title: 'Child Concerns',
    symptoms: ['Not responding to sounds', 'Delayed speech', 'Frequent ear infections'],
    message: "My child is not responding to sounds and has delayed speech",
    // no route — stays in chat
    color: 'border-green-200 hover:border-green-400 dark:border-green-800 dark:hover:border-green-500',
    iconBg: 'bg-green-50 text-green-600 dark:bg-green-900/40 dark:text-green-300',
  },
];

export function AssessmentPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState<StepId>(1);
  const [audience, setAudience] = useState<Audience | null>(null);
  const [form, setForm] = useState<FormData>(emptyForm);

  const canContinueStep2 =
    form.fullName.trim() && form.district.trim() && form.age.trim() && form.gender.trim();

  // Called when Step 2 "Continue" is clicked — route by age
  const handleStep2Next = () => {
    const age = parseInt(form.age, 10);
    if (!isNaN(age) && age < 18) {
      navigate('/child-care');
    } else {
      navigate('/adult-care');
    }
  };

  return (
    <>
      <PageHero
        eyebrow="Guided assessment"
        title="Let's find the right care pathway"
        description="Answer three short steps and our AI assistant will suggest the most relevant hearing tests and next steps."
        crumbs={[{ label: 'Home', to: '/' }, { label: 'Assessment' }]}
        icon={<Sparkles size={13} />}
      />

      <section className="container-page py-12 sm:py-16">
        <ProgressBar current={step} />

        <div className="mt-10">
          <AnimatePresence mode="wait">
            {step === 1 && (
              <StepWrapper key="s1">
                <Step1
                  value={audience}
                  onSelect={(a) => {
                    setAudience(a);
                    setStep(2);
                  }}
                />
              </StepWrapper>
            )}
            {step === 2 && (
              <StepWrapper key="s2">
                <Step2
                  form={form}
                  setForm={setForm}
                  onBack={() => setStep(1)}
                  onNext={handleStep2Next}
                  canContinue={!!canContinueStep2}
                />
              </StepWrapper>
            )}
            {step === 3 && (
              <StepWrapper key="s3">
                <Step3 onBack={() => setStep(2)} onNext={() => setStep(4)} />
              </StepWrapper>
            )}
            {step === 4 && (
              <StepWrapper key="s4">
                <Step4 audience={audience} form={form} onRestart={() => {
                  setStep(1);
                  setAudience(null);
                  setForm(emptyForm);
                }} />
              </StepWrapper>
            )}
          </AnimatePresence>
        </div>
      </section>
    </>
  );
}

function ProgressBar({ current }: { current: StepId }) {
  const pct = ((current - 1) / (stepsMeta.length - 1)) * 100;
  return (
    <div className="mx-auto max-w-2xl">
      <div className="flex items-center justify-between">
        {stepsMeta.map((s, i) => {
          const done = s.id < current;
          const active = s.id === current;
          return (
            <div key={s.id} className="flex flex-1 items-center last:flex-none">
              <div className="flex flex-col items-center">
                <span
                  className={`flex h-9 w-9 items-center justify-center rounded-full text-sm font-semibold transition-all ${
                    done
                      ? 'bg-green-500 text-white'
                      : active
                      ? 'bg-brand-600 text-white ring-4 ring-brand-100 dark:ring-brand-900'
                      : 'bg-slate-100 text-slate-400 dark:bg-slate-800'
                  }`}
                >
                  {done ? <Check size={16} /> : i + 1}
                </span>
                <span className={`mt-2 hidden text-xs sm:block ${active ? 'text-brand-700 dark:text-brand-300 font-semibold' : 'text-slate-500'}`}>
                  {s.label}
                </span>
              </div>
              {i < stepsMeta.length - 1 && (
                <div className="mx-2 h-1 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                  <motion.div
                    className="h-full bg-gradient-to-r from-brand-500 to-purple-500"
                    initial={false}
                    animate={{ width: s.id < current ? '100%' : '0%' }}
                    transition={{ duration: 0.4 }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
      <motion.div
        className="mt-4 h-1 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden sm:hidden"
        aria-hidden="true"
      >
        <motion.div className="h-full bg-gradient-to-r from-brand-500 to-purple-500" animate={{ width: `${pct}%` }} transition={{ duration: 0.4 }} />
      </motion.div>
    </div>
  );
}

function StepWrapper({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 40 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -40 }}
      transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function Step1({ value, onSelect }: { value: Audience | null; onSelect: (a: Audience) => void }) {
  return (
    <div className="mx-auto max-w-4xl">
      <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white text-center">
        Who are you seeking help for?
      </h2>
      <p className="mt-3 text-center text-slate-600 dark:text-slate-400">
        Choose the option that best describes your situation.
      </p>
      <div className="mt-10 grid gap-5 sm:grid-cols-3">
        {audienceCards.map((c, i) => {
          const selected = value === c.id;
          return (
            <motion.button
              key={c.id}
              type="button"
              onClick={() => onSelect(c.id)}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              whileHover={{ y: -6 }}
              className={`group relative flex flex-col items-center gap-4 rounded-2xl border-2 p-8 text-center transition-all ${
                selected
                  ? 'border-brand-500 bg-brand-50/50 dark:bg-brand-900/20'
                  : 'border-slate-200 bg-white hover:border-brand-300 dark:border-slate-700 dark:bg-slate-900'
              }`}
              aria-pressed={selected}
              aria-label={c.label}
            >
              <AccentIcon icon={c.icon} accent={c.accent} size="lg" className="group-hover:scale-110 transition-transform" />
              <div>
                <p className="text-lg font-semibold text-slate-900 dark:text-white">{c.label}</p>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{c.desc}</p>
              </div>
              <span className="mt-1 inline-flex items-center gap-1 text-sm font-medium text-brand-600 dark:text-brand-300 opacity-0 group-hover:opacity-100 transition-opacity">
                Continue <ArrowRight size={14} />
              </span>
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}

function Step2({
  form,
  setForm,
  onBack,
  onNext,
  canContinue,
}: {
  form: FormData;
  setForm: React.Dispatch<React.SetStateAction<FormData>>;
  onBack: () => void;
  onNext: () => void;
  canContinue: boolean;
}) {
  const field = (key: keyof FormData, label: string, opts?: { type?: string; placeholder?: string; required?: boolean; optional?: boolean; children?: React.ReactNode }) => (
    <label className="block">
      <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
        {label}
        {opts?.optional && <span className="text-xs text-slate-400">(optional)</span>}
        {opts?.required && <span className="text-brand-500">*</span>}
      </span>
      {opts?.children ?? (
        <input
          type={opts?.type ?? 'text'}
          value={form[key]}
          onChange={(e) => setForm((f) => ({ ...f, [key]: e.target.value }))}
          placeholder={opts?.placeholder}
          required={opts?.required}
          className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 transition-all"
        />
      )}
    </label>
  );

  return (
    <div className="mx-auto max-w-2xl">
      <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">Tell us a bit about yourself</h2>
      <p className="mt-3 text-slate-600 dark:text-slate-400">
        These details help us tailor recommendations. Nothing is stored or sent anywhere.
      </p>
      <form
        className="mt-8 grid gap-5 sm:grid-cols-2"
        onSubmit={(e) => {
          e.preventDefault();
          if (canContinue) onNext();
        }}
      >
        <div className="sm:col-span-2">{field('fullName', 'Full Name', { placeholder: 'e.g. Aarav Sharma', required: true })}</div>
        <DistrictSelect value={form.district} onChange={(v) => setForm((f) => ({ ...f, district: v }))} />
        <label className="block">
          <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
            Age <span className="text-brand-500">*</span>
          </span>
          <input
            type="number"
            value={form.age}
            onChange={(e) => setForm((f) => ({ ...f, age: e.target.value }))}
            placeholder="e.g. 32"
            required
            min={0}
            max={120}
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 placeholder:text-slate-400 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:ring-brand-900 transition-all"
          />
          {form.age && !isNaN(parseInt(form.age, 10)) && (
            <p className={`mt-1.5 flex items-center gap-1.5 text-xs font-medium ${
              parseInt(form.age, 10) < 18
                ? 'text-purple-600 dark:text-purple-300'
                : 'text-blue-600 dark:text-blue-300'
            }`}>
              {parseInt(form.age, 10) < 18 ? (
                <>
                  <Baby size={12} /> Under 18 — you'll be directed to the Child Care page
                </>
              ) : (
                <>
                  <User size={12} /> 18 or above — you'll be directed to the Adult Care page
                </>
              )}
            </p>
          )}
        </label>
        {field('gender', 'Gender', { required: true, children: (
          <select
            value={form.gender}
            onChange={(e) => setForm((f) => ({ ...f, gender: e.target.value }))}
            required
            className="w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 dark:focus:ring-brand-900 transition-all"
          >
            <option value="">Select gender</option>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other</option>
            <option value="prefer-not">Prefer not to say</option>
          </select>
        ) })}
        {field('phone', 'Phone Number', { type: 'tel', placeholder: '+91 ...', optional: true })}
        <div className="sm:col-span-2 mt-2 flex items-center justify-between gap-3">
          <Button type="button" variant="ghost" onClick={onBack}>
            <ArrowLeft size={16} /> Back
          </Button>
          <Button type="submit" disabled={!canContinue}>
            Continue <ArrowRight size={16} />
          </Button>
        </div>
      </form>
    </div>
  );
}

function Step3({ onBack, onNext }: { onBack: () => void; onNext: () => void }) {
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      id: 0,
      role: 'bot',
      text: `Hello 👋 I can help identify hearing-related concerns. Select a topic below or describe your problem in your own words.`,
      showTopicCards: true,
    },
  ]);
  const [typing, setTyping] = useState(false);
  const idRef = useState({ n: 1 })[0];

  const send = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || typing) return;
    setMessages((m) => [...m, { id: idRef.n++, role: 'user', text: trimmed }]);
    setTyping(true);
    try {
      const data = await sendChatMessage(trimmed);
      setMessages((m) => [...m, { id: idRef.n++, role: 'bot', text: data.response, followups: data.followups }]);
    } catch {
      setMessages((m) => [...m, { id: idRef.n++, role: 'bot', text: "Sorry, I couldn't reach the server. Please try again." }]);
    } finally {
      setTyping(false);
    }
  };

  const handleCardClick = (card: TopicCard) => {
    if (card.route) {
      // Adult topics → navigate directly to the Adult Care page section
      navigate(card.route);
    } else {
      // Child Concerns → send as a chat message
      send(card.message);
    }
  };

  return (
    <div className="mx-auto max-w-3xl">
      <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">Chat with the AI assistant</h2>
      <p className="mt-3 text-slate-600 dark:text-slate-400">
        Select a concern from the cards below or type in your own words. When you're ready, continue to see your tailored care pathway.
      </p>

      <div className="mt-8 card overflow-hidden">
        {/* Header */}
        <div className="flex items-center gap-3 bg-gradient-to-r from-brand-600 to-purple-600 px-5 py-3 text-white">
          <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20">
            <Bot size={18} />
          </span>
          <div className="flex-1">
            <p className="text-sm font-semibold leading-none">HearConnect AI</p>
            <p className="mt-1 text-xs text-white/80 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-green-400" /> Listening
            </p>
          </div>
        </div>

        {/* Messages */}
        <div className="h-[28rem] space-y-4 overflow-y-auto scrollbar-thin p-5" role="log" aria-live="polite">
          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className={`flex gap-2.5 ${m.role === 'user' ? 'flex-row-reverse' : ''}`}
              >
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${m.role === 'bot' ? 'bg-gradient-to-br from-brand-500 to-purple-500 text-white' : 'bg-slate-200 text-slate-600 dark:bg-slate-700 dark:text-slate-200'}`} aria-hidden="true">
                  {m.role === 'bot' ? <Bot size={16} /> : <UserIcon size={16} />}
                </span>
                <div className={m.role === 'user' ? 'max-w-[80%]' : 'flex-1 min-w-0'}>
                  <div className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.role === 'bot' ? 'bg-slate-50 text-slate-700 dark:bg-slate-800 dark:text-slate-100 rounded-tl-sm border border-slate-100 dark:border-slate-700' : 'bg-brand-600 text-white rounded-tr-sm'}`}>
                    {m.text}
                  </div>

                  {/* Topic cards on first greeting */}
                  {m.showTopicCards && (
                    <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
                      {TOPIC_CARDS.map((card) => (
                        <button
                          key={card.title}
                          type="button"
                          onClick={() => handleCardClick(card)}
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
                          {/* Badge: shows "View page →" for adult cards, "Chat" for child */}
                          <span className={`mt-auto inline-flex items-center gap-1 text-[10px] font-semibold ${card.route ? 'text-brand-600 dark:text-brand-300' : 'text-green-600 dark:text-green-400'}`}>
                            {card.route ? (
                              <><ArrowRight size={10} /> View details</>
                            ) : (
                              <><Sparkles size={10} /> Chat with AI</>
                            )}
                          </span>
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Follow-up chips */}
                  {m.followups && (
                    <div className="mt-2 flex flex-wrap gap-1.5">
                      {m.followups.map((f) => (
                        <button key={f} type="button" onClick={() => send(f)} className="chip bg-brand-50 text-brand-700 hover:bg-brand-100 dark:bg-brand-900/40 dark:text-brand-200 dark:hover:bg-brand-900/60 transition-colors">
                          <Sparkles size={11} /> {f}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {typing && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-500 to-purple-500 text-white">
                <Bot size={16} />
              </span>
              <div className="rounded-2xl rounded-tl-sm bg-slate-50 dark:bg-slate-800 border border-slate-100 dark:border-slate-700 px-4 py-3">
                <div className="flex items-center gap-1">
                  {[0, 1, 2].map((i) => (
                    <motion.span key={i} className="h-1.5 w-1.5 rounded-full bg-brand-400" animate={{ y: [0, -4, 0] }} transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.15 }} />
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </div>

      </div>

      <div className="mt-6 flex items-center justify-between">
        <Button variant="ghost" onClick={onBack}>
          <ArrowLeft size={16} /> Back
        </Button>
        <Button onClick={onNext}>
          See my pathway <ArrowRight size={16} />
        </Button>
      </div>
    </div>
  );
}

function Step4({ audience, form, onRestart }: { audience: Audience | null; form: FormData; onRestart: () => void }) {
  const isChild = audience === 'child';
  const route = isChild ? '/child-care' : '/adult-care';
  return (
    <div className="mx-auto max-w-3xl text-center">
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: 'spring', stiffness: 200, damping: 16 }}
        className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-green-500 text-white shadow-card"
      >
        <Check size={32} />
      </motion.div>
      <h2 className="mt-6 text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white">
        Your care pathway is ready
      </h2>
      <p className="mt-3 text-slate-600 dark:text-slate-400">
        {form.fullName ? `Thanks, ${form.fullName.split(' ')[0]}.` : 'Thanks.'} Based on what you
        shared, here's the recommended next step.
      </p>

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        <div className="card p-6 text-left">
          <AccentIcon icon={Stethoscope} accent="blue" size="lg" />
          <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">
            {isChild ? 'Explore Child Care pathways' : 'Explore Adult Care pathways'}
          </h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            {isChild
              ? 'Age-specific questions and tests from newborn to school age.'
              : 'Six adult hearing concerns with recommended diagnostic tests.'}
          </p>
          <LinkButton to={route} variant="secondary" size="sm" className="mt-4">
            Open {isChild ? 'Child' : 'Adult'} Care <ArrowRight size={14} />
          </LinkButton>
        </div>
        <div className="card p-6 text-left">
          <AccentIcon icon={CalendarCheck} accent="green" size="lg" />
          <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">Talk to a specialist</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
            Share your pathway summary with an audiologist or ENT to book the right tests.
          </p>
          <LinkButton to="/contact" variant="secondary" size="sm" className="mt-4">
            Contact us <ArrowRight size={14} />
          </LinkButton>
        </div>
      </div>

      <div className="mt-8 rounded-2xl bg-slate-50 dark:bg-slate-900 p-5 text-left">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Quick summary</p>
        <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
          <SummaryRow label="Seeking help for" value={audienceLabel(audience)} />
          {form.fullName && <SummaryRow label="Name" value={form.fullName} />}
          {form.district && <SummaryRow label="District" value={form.district} />}
          {form.age && <SummaryRow label="Age" value={form.age} />}
          {form.gender && <SummaryRow label="Gender" value={form.gender} />}
        </div>
        <p className="mt-4 text-xs text-slate-400">
          Note: HearConnect AI provides guidance only and is not a medical diagnosis.
        </p>
      </div>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Button variant="ghost" onClick={onRestart}>
          <RotateCcw size={16} /> Start over
        </Button>
        <LinkButton to={route}>
          View recommended care <ArrowRight size={16} />
        </LinkButton>
      </div>

      <div className="mt-10 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {hearingProblems.slice(0, 3).map((p) => (
          <Link key={p.id} to={p.route} className="group card p-4 text-left hover:shadow-card-hover transition-shadow">
            <div className="flex items-center gap-3">
              <AccentIcon icon={p.icon} accent={p.accent} size="sm" />
              <span className="text-sm font-medium text-slate-800 dark:text-slate-100">{p.title}</span>
              <ArrowRight size={14} className="ml-auto text-slate-300 group-hover:text-brand-600 group-hover:translate-x-1 transition-all" />
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}

function SummaryRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between rounded-lg bg-white dark:bg-slate-800 px-3 py-2">
      <span className="text-slate-500 dark:text-slate-400">{label}</span>
      <span className="font-medium text-slate-800 dark:text-slate-100">{value}</span>
    </div>
  );
}

function audienceLabel(a: Audience | null) {
  return a === 'myself' ? 'Myself' : a === 'child' ? 'My Child' : a === 'someone' ? 'Someone Else' : '—';
}

// ── Searchable District Dropdown ────────────────────────────────────────────

function DistrictSelect({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);

  const filtered = query.trim().length < 1
    ? ALL_DISTRICTS.slice(0, 60)          // show first 60 when no query
    : ALL_DISTRICTS.filter(
        (d) =>
          d.district.toLowerCase().includes(query.toLowerCase()) ||
          d.state.toLowerCase().includes(query.toLowerCase())
      ).slice(0, 80);

  const handleSelect = (district: string) => {
    onChange(district);
    setQuery('');
    setOpen(false);
  };

  return (
    <div className="relative block">
      <span className="mb-1.5 flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
        District <span className="text-brand-500">*</span>
      </span>

      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-800 focus:border-brand-400 focus:ring-2 focus:ring-brand-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-100 transition-all"
      >
        <span className={value ? 'text-slate-800 dark:text-slate-100' : 'text-slate-400'}>
          {value || 'Select district…'}
        </span>
        <ChevronDown size={16} className={`text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {/* Dropdown panel */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.15 }}
            className="absolute z-50 mt-1 w-full rounded-xl border border-slate-200 bg-white dark:bg-slate-800 dark:border-slate-700 shadow-card-hover overflow-hidden"
          >
            {/* Search box */}
            <div className="flex items-center gap-2 border-b border-slate-100 dark:border-slate-700 px-3 py-2.5">
              <Search size={14} className="shrink-0 text-slate-400" />
              <input
                autoFocus
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search district or state…"
                className="flex-1 bg-transparent text-sm text-slate-800 dark:text-slate-100 placeholder:text-slate-400 outline-none"
              />
            </div>

            {/* Results list */}
            <ul className="max-h-56 overflow-y-auto scrollbar-thin">
              {filtered.length === 0 ? (
                <li className="px-4 py-3 text-sm text-slate-400">No districts found</li>
              ) : (
                filtered.map(({ district, state }) => (
                  <li key={`${state}-${district}`}>
                    <button
                      type="button"
                      onClick={() => handleSelect(district)}
                      className={`w-full flex items-center justify-between px-4 py-2.5 text-left text-sm hover:bg-brand-50 dark:hover:bg-brand-900/30 transition-colors ${
                        value === district ? 'bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300 font-medium' : 'text-slate-700 dark:text-slate-200'
                      }`}
                    >
                      <span>{district}</span>
                      <span className="text-xs text-slate-400 dark:text-slate-500 ml-2 shrink-0">{state}</span>
                    </button>
                  </li>
                ))
              )}
              {!query && ALL_DISTRICTS.length > 60 && (
                <li className="px-4 py-2 text-xs text-slate-400 border-t border-slate-100 dark:border-slate-700">
                  Type to search all {ALL_DISTRICTS.length} districts…
                </li>
              )}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
