import type { LucideIcon } from 'lucide-react';
import {
  Baby,
  BabyIcon,
  Smile,
  GraduationCap,
  Ear,
  Volume2,
  HeartPulse,
  Stethoscope,
  MessageSquareHeart,
  CalendarCheck,
  Brain,
  Mic,
} from 'lucide-react';

export interface ChildCategory {
  id: string;
  number: number;
  title: string;
  ageRange: string;
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green' | 'pink';
  commonSigns: string[];
  tests: string[];
  whatItHelps: string;
}

export const childCategories: ChildCategory[] = [
  {
    id: 'newborn',
    number: 1,
    title: 'Newborn',
    ageRange: '0 – 6 Months',
    icon: Baby,
    accent: 'blue',
    commonSigns: [
      'Was newborn hearing screening done?',
      'Any NICU stay?',
      'Not responding to sounds?',
      'Family history of hearing loss?',
    ],
    tests: ['OAE', 'ABR', 'BOA', 'Tympanometry'],
    whatItHelps: 'Detects hearing loss early so intervention can begin before speech development.',
  },
  {
    id: 'infant',
    number: 2,
    title: 'Infant / Toddler',
    ageRange: '6 Months – 2.5 Years',
    icon: BabyIcon,
    accent: 'blue',
    commonSigns: [
      'Does the child respond to sounds?',
      'Delayed speech?',
      'Frequent ear infections?',
      'Difficulty in feeding / attention?',
    ],
    tests: ['VRA', 'OAE', 'Tympanometry', 'ABR'],
    whatItHelps: 'Identifies hearing issues that may delay speech and language milestones.',
  },
  {
    id: 'preschool',
    number: 3,
    title: 'Preschool Child',
    ageRange: '2.5 – 5 Years',
    icon: Smile,
    accent: 'pink' as 'green',   // mapped to pink styling below
    commonSigns: [
      'Speech delay?',
      'Difficulty following instructions?',
      'Doesn\'t respond consistently?',
      'Learning concerns?',
    ],
    tests: ['Play Audiometry', 'OAE', 'Speech Detection', 'Tympanometry'],
    whatItHelps: 'Checks hearing ability through play-based tests suited for young children.',
  },
  {
    id: 'school-age',
    number: 4,
    title: 'School-Age Child',
    ageRange: '5 Years and Above',
    icon: GraduationCap,
    accent: 'green',
    commonSigns: [
      'Difficulty hearing in class?',
      'Frequently asking for repetition?',
      'Academic concerns?',
    ],
    tests: ['PTA', 'Speech Audiometry', 'OAE', 'Special Tests'],
    whatItHelps: 'Identifies hearing difficulties that affect learning and classroom performance.',
  },
];

export interface ChildRecommendation {
  title: string;
  icon: LucideIcon;
  accent: 'blue' | 'purple' | 'green';
}

export const childRecommendations: ChildRecommendation[] = [
  { title: 'Hearing Aid', icon: Ear, accent: 'blue' },
  { title: 'ENT Referral', icon: Stethoscope, accent: 'purple' },
  { title: 'Cochlear Implant Evaluation', icon: Ear, accent: 'green' },
  { title: 'Auditory Training', icon: Volume2, accent: 'blue' },
  { title: 'Speech Therapy', icon: Mic, accent: 'purple' },
  { title: 'Parent Counselling', icon: MessageSquareHeart, accent: 'green' },
  { title: 'Regular Follow-up', icon: CalendarCheck, accent: 'blue' },
];

export interface ChildTestInfo {
  code: string;
  name: string;
  icon: LucideIcon;
}

export const childTests: ChildTestInfo[] = [
  { code: 'OAE',            name: 'Otoacoustic Emissions',          icon: Ear },
  { code: 'ABR',            name: 'Auditory Brainstem Response',     icon: Brain },
  { code: 'BOA',            name: 'Behavioural Observation Audiometry', icon: Smile },
  { code: 'VRA',            name: 'Visual Reinforcement Audiometry', icon: HeartPulse },
  { code: 'Tympanometry',   name: 'Middle Ear Analysis',             icon: Stethoscope },
  { code: 'Play Audiometry',name: 'Play-Based Hearing Test',         icon: Smile },
  { code: 'Speech Detection',name: 'Speech Awareness Threshold',     icon: Mic },
  { code: 'PTA',            name: 'Pure Tone Audiometry',            icon: Volume2 },
];
