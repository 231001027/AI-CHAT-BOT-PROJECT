import type { LucideIcon } from 'lucide-react';
import {
  Ear,
  BellRing,
  CircleDashed,
  Activity,
  Baby,
  AudioLines,
  Brain,
  Waves,
  Stethoscope,
  Mic,
  Gauge,
  Volume2,
  ScanLine,
  Headphones,
  EarOff,
  MessageSquare,
  Repeat,
  Utensils,
  HelpCircle,
} from 'lucide-react';

export type HearingProblemId =
  | 'hearing-difficulty'
  | 'ringing-in-ears'
  | 'dizziness-balance'
  | 'ear-pain-discharge'
  | 'child-concerns';

export interface HearingProblem {
  id: HearingProblemId;
  title: string;
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green';
  symptoms: string[];
  route: string;
}

export const hearingProblems: HearingProblem[] = [
  {
    id: 'hearing-difficulty',
    title: 'Hearing Difficulty',
    icon: Ear,
    accent: 'blue',
    symptoms: ['Hard in noisy places', 'Asking people to repeat', 'TV too loud'],
    route: '/adult-care#hearing-difficulty',
  },
  {
    id: 'ringing-in-ears',
    title: 'Ringing in Ears',
    icon: BellRing,
    accent: 'purple',
    symptoms: ['Ringing', 'Buzzing', 'Disturbs sleep'],
    route: '/adult-care#ringing-in-ears',
  },
  {
    id: 'dizziness-balance',
    title: 'Dizziness / Balance',
    icon: CircleDashed,
    accent: 'green',
    symptoms: ['Feeling dizzy', 'Room spinning', 'Unsteady walking'],
    route: '/adult-care#dizziness-balance',
  },
  {
    id: 'ear-pain-discharge',
    title: 'Ear Pain / Discharge',
    icon: Activity,
    accent: 'blue',
    symptoms: ['Ear pain', 'Fluid', 'Fever'],
    route: '/adult-care#ear-pain-discharge',
  },
  {
    id: 'child-concerns',
    title: 'Child Hearing Concerns',
    icon: Baby,
    accent: 'purple',
    symptoms: ['Speech concerns', 'Hearing difficulty', 'Ear pain'],
    route: '/child-care',
  },
];

export interface AdultSection {
  id: string;
  title: string;
  number: number;
  section: 'speech' | 'hearing';
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green' | 'pink';
  commonSigns: string[];
  tests: string[];
  whatItHelps: string;
}

/** Part 2 — Adults: Section A (Speech) + Section B (Audiology). */
export const adultSections: AdultSection[] = [
  // Section A — Speech and Language
  {
    id: 'adult-speech-language',
    number: 1,
    section: 'speech',
    title: 'Speech and Language Issues',
    icon: MessageSquare,
    accent: 'purple',
    commonSigns: [
      'Do you struggle to find the right word?',
      'Is it hard to understand what others say?',
      'Any difficulty reading, writing or with numbers?',
      'Did this start after a stroke or head injury?',
      'Does it affect your work or daily life?',
    ],
    tests: ['Speech-Language Evaluation', 'Pure Tone Audiometry'],
    whatItHelps: 'Reviews how you understand and use language, and checks hearing.',
  },
  {
    id: 'adult-stuttering',
    number: 2,
    section: 'speech',
    title: 'Stuttering (Fluency)',
    icon: Repeat,
    accent: 'purple',
    commonSigns: [
      'Do you repeat sounds or words while speaking?',
      'Do you get stuck on a word?',
      'Do you avoid calls or speaking situations?',
      'Any tension in face or jaw while speaking?',
      'When did it start?',
    ],
    tests: ['Fluency Assessment', 'Pure Tone Audiometry'],
    whatItHelps: 'Looks at how smoothly you speak and what support may help.',
  },
  {
    id: 'adult-speech-clarity',
    number: 3,
    section: 'speech',
    title: 'Speech Clarity',
    icon: Mic,
    accent: 'pink',
    commonSigns: [
      'Do people often ask you to repeat?',
      'Does your speech sound slurred or slow?',
      'Does it get worse when you are tired?',
      'Any weakness in face, lips or tongue?',
      'How did it start?',
    ],
    tests: ['Speech Sound / Clarity Assessment', 'Pure Tone Audiometry'],
    whatItHelps: 'Checks which speech sounds are clear and which need support.',
  },
  {
    id: 'adult-voice-problems',
    number: 4,
    section: 'speech',
    title: 'Voice Problems',
    icon: Volume2,
    accent: 'purple',
    commonSigns: [
      'Is your voice hoarse, rough or weak?',
      'Does your voice tire out after talking?',
      'Any throat pain or tightness while speaking?',
      'Does your job need heavy voice use?',
      'Has your voice been different for over 2 weeks?',
    ],
    tests: ['Voice Assessment', 'Pure Tone Audiometry'],
    whatItHelps: 'Reviews voice quality, strain, and day-to-day voice use.',
  },
  {
    id: 'adult-feeding-swallowing',
    number: 5,
    section: 'speech',
    title: 'Feeding and Swallowing',
    icon: Utensils,
    accent: 'green',
    commonSigns: [
      'Do you cough or choke while eating or drinking?',
      'Does food feel stuck in your throat or chest?',
      'Do meals take much longer than before?',
      'Have you changed your diet because of this?',
      'Any weight loss or repeated chest infections?',
    ],
    tests: ['Clinical Swallowing Assessment', 'Speech-Language Evaluation'],
    whatItHelps: 'Checks safety and comfort when you eat and drink.',
  },
  // Section B — Audiology
  {
    id: 'hearing-difficulty',
    number: 1,
    section: 'hearing',
    title: 'Hearing Difficulty',
    icon: Ear,
    accent: 'blue',
    commonSigns: [
      'Is it hard to follow conversation in noisy places?',
      'Do you often ask people to repeat?',
      'Do others say your TV volume is too loud?',
      'Is one ear worse than the other?',
      'Any long-term loud noise exposure at work?',
    ],
    tests: ['Hearing Test (PTA)', 'Speech Audiometry', 'Tympanometry'],
    whatItHelps: 'Checks how well you hear and the type of hearing loss.',
  },
  {
    id: 'ringing-in-ears',
    number: 2,
    section: 'hearing',
    title: 'Ringing in the Ears',
    icon: BellRing,
    accent: 'blue',
    commonSigns: [
      'Do you hear ringing or buzzing others cannot?',
      'Is it present even in a quiet room?',
      'Does it disturb your sleep or focus?',
      'Did it start after loud noise, infection or new medicine?',
      'Which ear?',
    ],
    tests: ['Hearing Test (PTA)', 'Tinnitus Assessment', 'Tympanometry'],
    whatItHelps: 'Assesses ringing concerns together with hearing levels.',
  },
  {
    id: 'dizziness-balance',
    number: 3,
    section: 'hearing',
    title: 'Dizziness / Balance',
    icon: CircleDashed,
    accent: 'blue',
    commonSigns: [
      'Do you feel dizzy, spinning or unsteady?',
      'Does it start when you turn your head or stand up?',
      'Any vomiting, hearing loss or ear fullness with it?',
      'Have you fallen or nearly fallen because of it?',
      'Is walking harder in the dark?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'VNG / balance screening'],
    whatItHelps: 'Looks at balance concerns that can share pathways with the ear.',
  },
  {
    id: 'other-hearing-related',
    number: 4,
    section: 'hearing',
    title: 'Other Hearing Issues',
    icon: HelpCircle,
    accent: 'blue',
    commonSigns: [
      'Do you feel the ear is blocked or under pressure?',
      'Are normal sounds uncomfortably loud?',
      'Is it hard to tell where a sound comes from?',
      'Are you on any long-term medication?',
      'Do you already use a hearing aid?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'Speech Audiometry'],
    whatItHelps: 'Screens other ear-related concerns that affect hearing comfort.',
  },
  {
    id: 'ear-pain-discharge',
    number: 5,
    section: 'hearing',
    title: 'Ear Pain / Discharge',
    icon: Activity,
    accent: 'green',
    commonSigns: [
      'Do you have pain or discomfort in the ear?',
      'Any fluid, pus or blood from the ear?',
      'Any fever along with it?',
      'Any recent cold, cough or blocked nose?',
      'Has this happened before in the past year?',
    ],
    tests: ['Ear Examination', 'Tympanometry', 'Hearing Test (PTA)'],
    whatItHelps: 'Checks for infection, fluid, or middle-ear problems causing pain or discharge.',
  },
];

export const adultSpeechSections = adultSections.filter((s) => s.section === 'speech');
export const adultHearingSections = adultSections.filter((s) => s.section === 'hearing');

export interface SpecialTest {
  code: string;
  name: string;
  icon: LucideIcon;
  description: string;
}

export const specialTests: SpecialTest[] = [
  { code: 'ABR', name: 'Auditory Brainstem Response', icon: Brain, description: 'Measures hearing nerve and brain pathway responses.' },
  { code: 'MLR', name: 'Middle Latency Response', icon: AudioLines, description: 'Evaluates middle-latency auditory evoked potentials.' },
  { code: 'LLR', name: 'Late Latency Response', icon: AudioLines, description: 'Assesses cortical auditory processing.' },
  { code: 'P300', name: 'Cognitive Evoked Potential', icon: Brain, description: 'Detects attention and cognitive hearing processing.' },
  { code: 'P500', name: 'P500 Response', icon: Waves, description: 'Evaluates higher-level auditory discrimination.' },
  { code: 'SRT', name: 'Speech Reception Threshold', icon: Mic, description: 'Lowest level at which speech is understood.' },
  { code: 'WRS', name: 'Word Recognition Score', icon: Mic, description: 'Tests clarity of word recognition at conversational levels.' },
  { code: 'PB Test', name: 'Phonetically Balanced Test', icon: ScanLine, description: 'Measures speech discrimination with balanced words.' },
  { code: 'SPIN', name: 'Speech in Noise Test', icon: Headphones, description: 'Assesses understanding of speech in background noise.' },
];

export interface Recommendation {
  title: string;
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green';
}

export const generalRecommendations: Recommendation[] = [
  { title: 'Avoid loud noise exposure', icon: Volume2, accent: 'blue' },
  { title: 'Protect ears in noisy places', icon: EarOff, accent: 'purple' },
  { title: 'Get enough rest and sleep', icon: Headphones, accent: 'green' },
  { title: 'Manage stress and anxiety', icon: Activity, accent: 'blue' },
  { title: 'Stay hydrated and healthy', icon: Gauge, accent: 'purple' },
  { title: 'Regular hearing check-ups', icon: Stethoscope, accent: 'green' },
];
