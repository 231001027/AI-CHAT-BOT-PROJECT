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
      'Do you often have trouble finding the word you want or accidentally say a different word?',
      'Do you have trouble following fast conversations or complicated spoken instructions?',
      'Have you recently developed problems with reading, writing, or everyday calculations?',
      'Did these communication problems begin after a stroke, head injury, or other brain illness?',
      'Do you speak in short, effortful phrases and sometimes leave out small grammar words?',
      'Do your speech difficulties make phone calls, work tasks, or everyday activities harder?',
      'Do you have difficulty remembering conversations or staying focused during communication?',
    ],
    tests: [],
    whatItHelps: 'Reviews how you understand and use language.',
  },
  {
    id: 'adult-stuttering',
    number: 2,
    section: 'speech',
    title: 'Stuttering (Fluency)',
    icon: Repeat,
    accent: 'purple',
    commonSigns: [
      "Do you repeat sounds or syllables when speaking, such as 't-t-today' or 'I-I-I'?",
      "Do you stretch sounds out, such as 'ssss-seven', or sometimes experience silent blocks?",
      'When speech becomes difficult, do you feel tension in your jaw, neck, or face, or use movements such as tapping your feet?',
      'Do you sometimes change words or talk around what you mean to avoid a difficult sound or word?',
      'Do you avoid situations such as phone calls, introductions, or ordering because speaking feels difficult?',
      'Does your speech sometimes sound rushed, uneven, or as though several words run together?',
      'Did the difficulty with fluency begin during childhood, or did it start suddenly as an adult?',
      'Does your speech difficulty cause stress or make social, work, or career situations harder?',
    ],
    tests: ['Fluency Assessment'],
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
      'Does your speech sound slurred or unclear enough that other people have trouble understanding you?',
      "Do you have difficulty saying a sequence of syllables quickly, such as 'puh-tuh-kuh'?",
      'Does your speech become less clear when you are tired?',
      'Have you noticed facial drooping, stiff lips, or slower tongue movements?',
      'Does your voice sometimes sound unusually flat, monotone, or robotic?',
      'When saying certain words, do you find yourself searching for the correct mouth position?',
    ],
    tests: ['Speech Sound / Clarity Assessment'],
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
      'Is your voice regularly hoarse, rough, weak, or breathy?',
      'Does your voice become tired or do you run out of air after talking for a moderate amount of time?',
      'Do you feel aching or tightness in your throat, or a constant lump-like feeling?',
      'Does your work require you to use your voice heavily, such as teaching, taking calls, or sales?',
      'Has a change in your voice or hoarseness lasted longer than two to three weeks?',
      'Does your voice unexpectedly break in pitch or develop involuntary shaking or tremor?',
    ],
    tests: ['Voice Assessment'],
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
      'Do you cough, clear your throat, or choke when eating or drinking liquids?',
      'Do solid food, tablets, or liquids ever feel as though they are stuck in your throat or chest?',
      "Have you changed your diet to softer foods or purees because you're worried about choking?",
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
