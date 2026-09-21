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
      'Compared with other children of the same age, does your child use fewer words or much shorter sentences?',
      'Does your child have trouble following simple spoken directions unless you also use gestures?',
      "Does your child often point, cry, or pull someone's hand instead of using words to communicate?",
      'Has your child lost words or communication skills that they used regularly before?',
      'Does your child have difficulty answering questions or keeping a short conversation going?',
      "Does your child leave out small grammar words such as 'is' or 'the', or often use sentence grammar incorrectly?",
      "Does your child have trouble naming familiar objects and often say things like 'that thing' instead?",
    ],
    tests: [
      'ALD (Assessment of Language Development)',
      'REELS (Receptive-Expressive Emergent Language Scale)',
      'COMDEALL Developmental Checklist',
      'LPT (Linguistic Profile Test)',
    ],
    whatItHelps: 'Reviews how your child understands and uses language against age-expected milestones.',
  },
  {
    id: 'child-stuttering',
    number: 2,
    title: 'Stuttering (Fluency)',
    section: 'speech',
    icon: Repeat,
    accent: 'purple',
    commonSigns: [
      "Does your child repeat a sound or syllable several times, such as 'b-b-b-ball'?",
      "Does your child hold a sound for a long time, such as 'ssss-snake'?",
      'Does your child sometimes get stuck while trying to speak, with no sound coming out?',
      'Do you notice eye blinking, facial tension, or other movements when your child is having difficulty speaking?',
      'Does your child become frustrated, cover their mouth, or avoid talking when speech is difficult?',
      "Does your child's speech sometimes sound very fast, uneven, or as though words run together?",
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
      "Do people who aren't used to your child's speech have trouble understanding what they say?",
      "Does your child leave out or replace sounds in familiar words, such as saying 'tat' instead of 'cat'?",
      'Do you or other family members often need to repeat what your child says or explain it to others?',
      "Does your child leave out syllables in longer words, such as saying 'nana' for 'banana'?",
      'When repeating a word, does your child appear to search for the right mouth position or make unusual mouth movements?',
      'Did your child begin babbling or using first words later than expected for their age?',
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
      "Does your child's voice regularly sound hoarse, rough, or breathy?",
      "Does your child's voice become weak, strained, or disappear after talking or crying for a while?",
      'Does your child complain that their throat feels sore, tight, or uncomfortable after speaking?',
      'Does your child frequently shout, scream, or make harsh sounds while playing?',
      'Has the unusual voice quality continued for more than two weeks?',
      "When your child isn't sick, do they still sound unusually nasal or as though their nose is blocked?",
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
      'Does your child cough, choke, or gag while eating or drinking, especially with liquids?',
      "Does food or liquid spill from your child's lips or come through the nose while swallowing?",
      "Do your child's usual meals often take more than 30 to 40 minutes to finish?",
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
