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
} from 'lucide-react';

export type HearingProblemId =
  | 'hearing-difficulty'
  | 'tinnitus'
  | 'dizziness'
  | 'ear-pain'
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
    symptoms: ['Cannot hear properly', 'Muffled sounds', 'Asking people to repeat'],
    route: '/adult-care#hearing-difficulty',
  },
  {
    id: 'tinnitus',
    title: 'Ringing in Ears (Tinnitus)',
    icon: BellRing,
    accent: 'purple',
    symptoms: ['Ringing', 'Buzzing', 'Hissing'],
    route: '/adult-care#tinnitus',
  },
  {
    id: 'dizziness',
    title: 'Dizziness / Balance',
    icon: CircleDashed,
    accent: 'green',
    symptoms: ['Feeling dizzy', 'Room spinning', 'Difficulty walking'],
    route: '/adult-care#balance-problems',
  },
  {
    id: 'ear-pain',
    title: 'Ear Pain / Discharge',
    icon: Activity,
    accent: 'blue',
    symptoms: ['Ear pain', 'Fluid', 'Infection'],
    route: '/adult-care#ear-pain',
  },
  {
    id: 'child-concerns',
    title: 'Child Hearing Concerns',
    icon: Baby,
    accent: 'purple',
    symptoms: ['Delayed speech', "Doesn't respond to sounds", 'Frequent ear infections'],
    route: '/child-care',
  },
];

export interface AdultSection {
  id: string;
  title: string;
  number: number;
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green';
  commonSigns: string[];
  tests: string[];
  whatItHelps: string;
}

export const adultSections: AdultSection[] = [
  {
    id: 'hearing-difficulty',
    number: 1,
    title: 'Hearing Difficulty',
    icon: Ear,
    accent: 'blue',
    commonSigns: [
      'When did it start?',
      'Both ears or one ear?',
      'Sudden or gradual?',
      'Any noise exposure?',
      'Previous ear problem?',
    ],
    tests: ['Hearing Test (PTA)', 'Speech Audiometry', 'Tympanometry', 'OAE', 'SPIN (Speech In Noise)'],
    whatItHelps: 'Checks how well you hear and the type of hearing loss.',
  },
  {
    id: 'tinnitus',
    number: 2,
    title: 'Ringing in Ears (Tinnitus)',
    icon: BellRing,
    accent: 'purple',
    commonSigns: [
      'In which ear?',
      'Constant or comes and goes?',
      'Difficulty sleeping?',
      'Exposure to loud noise?',
      'Stress / Anxiety?',
    ],
    tests: ['Hearing Test (PTA)', 'Tinnitus Assessment', 'Tympanometry', 'OAE', 'SPIN (Speech In Noise)'],
    whatItHelps: 'Finds the possible cause of ringing in your ears.',
  },
  {
    id: 'hyperacusis',
    number: 3,
    title: 'Hyperacusis (Sound Sensitivity)',
    icon: Volume2,
    accent: 'green',
    commonSigns: [
      'Sensitivity to everyday sounds?',
      'Discomfort with normal sound levels?',
      'Pain or irritation with loud sounds?',
      'Avoids noisy places?',
    ],
    tests: ['Loudness Discomfort Level (LDL)', 'Audiometry (PTA)', 'Tympanometry', 'SPIN (Speech In Noise)'],
    whatItHelps: 'Identifies sound sensitivity and helps in management.',
  },
  {
    id: 'balance-problems',
    number: 4,
    title: 'Dizziness / Balance Problem',
    icon: CircleDashed,
    accent: 'blue',
    commonSigns: [
      'When does it happen?',
      'Spinning feeling or light headed?',
      'Any hearing loss or ringing in ears?',
      'Nausea / Vomiting?',
      'Unsteady while walking?',
    ],
    tests: ['VEMP', 'VNG', 'Hearing Test (PTA)', 'SPIN (Speech In Noise) (if needed)', 'Posturography (if needed)'],
    whatItHelps: 'Checks balance system and inner ear function.',
  },
  {
    id: 'ear-pain',
    number: 5,
    title: 'Ear Pain / Discharge',
    icon: Activity,
    accent: 'purple',
    commonSigns: [
      'In which ear?',
      'Pain, discharge or both?',
      'Fever or cold?',
      'Recent ear infection?',
      'Itching in ear?',
    ],
    tests: ['Ear Evaluation (ENT)', 'Tympanometry', 'Hearing Test (PTA)', 'Immittance Test', 'OAE'],
    whatItHelps: 'Finds infection, fluid or other ear problems.',
  },
  {
    id: 'other-hearing-problems',
    number: 6,
    title: 'Other Hearing Related Issues',
    icon: EarOff,
    accent: 'green',
    commonSigns: [
      'Ear fullness / Blockage',
      'Earwax / Itching',
      'Difficulty understanding speech',
      'Changes in hearing',
      'Previous ear surgery',
      'Family history of hearing loss',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'Speech Audiometry', 'SPIN (Speech In Noise)', 'OAE'],
    whatItHelps: 'Identifies other ear related conditions and concerns.',
  },
];

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
