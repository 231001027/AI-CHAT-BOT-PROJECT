import type { LucideIcon } from 'lucide-react';
import {
  MessageSquare,
  Repeat,
  Mic,
  Volume2,
  Utensils,
  Ear,
  Waves,
  CircleDot,
  HelpCircle,
  Thermometer,
  Stethoscope,
  CalendarCheck,
  Brain,
  HeartPulse,
  Smile,
  MessageSquareHeart,
} from 'lucide-react';

export interface ChildCategory {
  id: string;
  number: number;
  title: string;
  section: 'speech' | 'hearing';
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green' | 'pink';
  commonSigns: string[];
  tests: string[];
  whatItHelps: string;
}

/** Part 1 — Children: Section A (Speech) + Section B (Audiology). */
export const childCategories: ChildCategory[] = [
  // Section A — Speech and Language
  {
    id: 'child-speech-language',
    number: 1,
    title: 'Speech and Language Issues',
    section: 'speech',
    icon: MessageSquare,
    accent: 'purple',
    commonSigns: [
      'Does your child speak less than other children of the same age?',
      'Does your child follow simple instructions?',
      'Does your child point or gesture instead of talking?',
      'Has your child stopped using words they knew before?',
      'Is it hard for your child to hold a conversation?',
    ],
    tests: ['Speech-Language Evaluation', 'OAE'],
    whatItHelps: 'Reviews how your child understands and uses language, and checks hearing.',
  },
  {
    id: 'child-stuttering',
    number: 2,
    title: 'Stuttering (Fluency)',
    section: 'speech',
    icon: Repeat,
    accent: 'purple',
    commonSigns: [
      'Does your child repeat sounds or words while speaking?',
      'Does your child get stuck on a word?',
      'Does your child stretch out sounds?',
      'Any eye blinking or head movements while speaking?',
      'Does your child avoid speaking because of this?',
    ],
    tests: ['Fluency Assessment', 'OAE'],
    whatItHelps: 'Looks at how smoothly your child speaks and what support may help.',
  },
  {
    id: 'child-speech-clarity',
    number: 3,
    title: 'Speech Clarity',
    section: 'speech',
    icon: Mic,
    accent: 'pink',
    commonSigns: [
      'Do outsiders find it hard to understand your child?',
      'Does your child miss or mix up sounds in words?',
      'Do you have to repeat what your child said?',
      'Is your child’s speech too fast, slow or mumbled?',
      'Did your child start speaking late?',
    ],
    tests: ['Speech Sound / Clarity Assessment', 'OAE'],
    whatItHelps: 'Checks which speech sounds are clear and which need support.',
  },
  {
    id: 'child-voice-problems',
    number: 4,
    title: 'Voice Problems',
    section: 'speech',
    icon: Volume2,
    accent: 'purple',
    commonSigns: [
      'Is your child’s voice hoarse or rough?',
      'Does the voice get weak after talking a while?',
      'Does your child complain of throat pain while speaking?',
      'Does your child shout or scream often?',
      'Has the voice been different for over 2 weeks?',
    ],
    tests: ['Voice Assessment', 'OAE'],
    whatItHelps: 'Reviews voice quality, strain, and day-to-day voice use.',
  },
  {
    id: 'child-feeding-swallowing',
    number: 5,
    title: 'Feeding and Swallowing',
    section: 'speech',
    icon: Utensils,
    accent: 'green',
    commonSigns: [
      'Does your child cough or choke while eating or drinking?',
      'Does food or liquid come out of the nose or mouth?',
      'Does a meal take more than 30 minutes?',
      'Does your child refuse solids or liquids?',
      'Poor weight gain or repeated chest infections?',
    ],
    tests: ['Feeding and Swallowing Assessment', 'Speech-Language Evaluation'],
    whatItHelps: 'Checks safety and comfort when your child eats and drinks.',
  },
  // Section B — Audiology (Hearing)
  {
    id: 'child-hearing-difficulty',
    number: 1,
    title: 'Hearing Difficulty',
    section: 'hearing',
    icon: Ear,
    accent: 'blue',
    commonSigns: [
      'Does your child not respond when called from behind?',
      'Does your child ask you to repeat often?',
      'Does your child keep the TV volume very high?',
      'Is hearing harder in noisy places?',
      'Any hearing loss in the family?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'OAE'],
    whatItHelps: 'Measures how soft a sound your child can hear and checks the middle ear.',
  },
  {
    id: 'child-ringing-in-ears',
    number: 2,
    title: 'Ringing in the Ears',
    section: 'hearing',
    icon: Waves,
    accent: 'blue',
    commonSigns: [
      'Does your child hear ringing or buzzing in the ear?',
      'Is it present even in a quiet room?',
      'Does it disturb sleep or concentration?',
      'Did it start after loud noise, infection or injury?',
      'Which ear?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'OAE'],
    whatItHelps: 'Assesses ringing concerns together with hearing levels.',
  },
  {
    id: 'child-dizziness-balance',
    number: 3,
    title: 'Dizziness / Balance',
    section: 'hearing',
    icon: CircleDot,
    accent: 'blue',
    commonSigns: [
      'Does your child feel dizzy or unsteady?',
      'Does your child fall or bump into things often?',
      'Does dizziness start with sudden head movement?',
      'Any vomiting or hearing loss with it?',
      'Is walking harder in the dark?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'Balance screening'],
    whatItHelps: 'Looks at balance concerns that can share pathways with the ear.',
  },
  {
    id: 'child-other-hearing',
    number: 4,
    title: 'Other Hearing Issues',
    section: 'hearing',
    icon: HelpCircle,
    accent: 'blue',
    commonSigns: [
      'Does your child feel the ear is blocked or full?',
      'Is your child upset by loud everyday sounds?',
      'Is it hard to tell where a sound comes from?',
      'Frequent colds, allergy or blocked nose?',
      'Loud earphone use or noise exposure?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'OAE'],
    whatItHelps: 'Screens other ear-related concerns that affect hearing comfort.',
  },
  {
    id: 'child-ear-pain-discharge',
    number: 5,
    title: 'Ear Pain / Discharge',
    section: 'hearing',
    icon: Thermometer,
    accent: 'green',
    commonSigns: [
      'Does your child have ear pain or pull at the ear?',
      'Any fluid, pus or blood from the ear?',
      'Any fever along with it?',
      'Any recent cold or blocked nose?',
      'Has this happened before in the past year?',
    ],
    tests: ['Tympanometry', 'Ear Examination', 'PTA / age-appropriate hearing test'],
    whatItHelps: 'Checks for infection, fluid, or middle-ear problems causing pain or discharge.',
  },
];

export const childSpeechCategories = childCategories.filter((c) => c.section === 'speech');
export const childHearingCategories = childCategories.filter((c) => c.section === 'hearing');

export interface ChildRecommendation {
  title: string;
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green';
}

export const childRecommendations: ChildRecommendation[] = [
  { title: 'Hearing Aid', icon: Ear, accent: 'blue' },
  { title: 'ENT Referral', icon: Stethoscope, accent: 'purple' },
  { title: 'Speech Therapy', icon: Mic, accent: 'purple' },
  { title: 'Auditory Training', icon: Volume2, accent: 'blue' },
  { title: 'Parent Counselling', icon: MessageSquareHeart, accent: 'green' },
  { title: 'Regular Follow-up', icon: CalendarCheck, accent: 'blue' },
];

export interface ChildTestInfo {
  code: string;
  name: string;
  icon: LucideIcon;
}

export const childTests: ChildTestInfo[] = [
  { code: 'OAE', name: 'Otoacoustic Emissions', icon: Ear },
  { code: 'ABR', name: 'Auditory Brainstem Response', icon: Brain },
  { code: 'VRA', name: 'Visual Reinforcement Audiometry', icon: HeartPulse },
  { code: 'Tympanometry', name: 'Middle Ear Analysis', icon: Stethoscope },
  { code: 'Play Audiometry', name: 'Play-Based Hearing Test', icon: Smile },
  { code: 'PTA', name: 'Pure Tone Audiometry', icon: Volume2 },
  { code: 'SLP', name: 'Speech-Language Evaluation', icon: Mic },
];
