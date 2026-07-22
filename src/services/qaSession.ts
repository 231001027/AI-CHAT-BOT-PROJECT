/**
 * qaSession.ts
 *
 * Maps each adultSection id → its ordered list of Q&A questions.
 * Used by AIAssistantPage to start a guided interview when the user
 * arrives via /ai-assistant?topic=<id>.
 */

export interface QASession {
  topicId: string;
  topicTitle: string;
  questions: string[];
  tests: string[];
  whatItHelps: string;
}

const SESSIONS: Record<string, QASession> = {
  'hearing-difficulty': {
    topicId: 'hearing-difficulty',
    topicTitle: 'Hearing Difficulty',
    questions: [
      'When did it start?',
      'Both ears or one ear?',
      'Sudden or gradual?',
      'Any noise exposure?',
      'Previous ear problem?',
    ],
    tests: ['Hearing Test (PTA)', 'Speech Audiometry', 'Tympanometry', 'OAE', 'SPIN (Speech In Noise)'],
    whatItHelps: 'Checks how well you hear and the type of hearing loss.',
  },
  'tinnitus': {
    topicId: 'tinnitus',
    topicTitle: 'Ringing in Ears (Tinnitus)',
    questions: [
      'In which ear?',
      'Constant or comes and goes?',
      'Difficulty sleeping?',
      'Exposure to loud noise?',
      'Stress / Anxiety?',
    ],
    tests: ['Hearing Test (PTA)', 'Tinnitus Assessment', 'Tympanometry', 'OAE', 'SPIN (Speech In Noise)'],
    whatItHelps: 'Finds the possible cause of ringing in your ears.',
  },
  'hyperacusis': {
    topicId: 'hyperacusis',
    topicTitle: 'Hyperacusis (Sound Sensitivity)',
    questions: [
      'Sensitivity to everyday sounds?',
      'Discomfort with normal sound levels?',
      'Pain or irritation with loud sounds?',
      'Avoids noisy places?',
    ],
    tests: ['Loudness Discomfort Level (LDL)', 'Audiometry (PTA)', 'Tympanometry', 'SPIN (Speech In Noise)'],
    whatItHelps: 'Identifies sound sensitivity and helps in management.',
  },
  'balance-problems': {
    topicId: 'balance-problems',
    topicTitle: 'Dizziness / Balance Problem',
    questions: [
      'When does it happen?',
      'Spinning feeling or light headed?',
      'Any hearing loss or ringing in ears?',
      'Nausea / Vomiting?',
      'Unsteady while walking?',
    ],
    tests: ['VEMP', 'VNG', 'Hearing Test (PTA)', 'SPIN (Speech In Noise) (if needed)', 'Posturography (if needed)'],
    whatItHelps: 'Checks balance system and inner ear function.',
  },
  'ear-pain': {
    topicId: 'ear-pain',
    topicTitle: 'Ear Pain / Discharge',
    questions: [
      'In which ear?',
      'Pain, discharge or both?',
      'Fever or cold?',
      'Recent ear infection?',
      'Itching in ear?',
    ],
    tests: ['Ear Evaluation (ENT)', 'Tympanometry', 'Hearing Test (PTA)', 'Immittance Test', 'OAE'],
    whatItHelps: 'Finds infection, fluid or other ear problems.',
  },
  'other-hearing-problems': {
    topicId: 'other-hearing-problems',
    topicTitle: 'Other Hearing Related Issues',
    questions: [
      'Ear fullness / Blockage?',
      'Earwax / Itching?',
      'Difficulty understanding speech?',
      'Changes in hearing?',
      'Previous ear surgery?',
      'Family history of hearing loss?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'Speech Audiometry', 'SPIN (Speech In Noise)', 'OAE'],
    whatItHelps: 'Identifies other ear related conditions and concerns.',
  },
  // ── Child age-group sessions ───────────────────────────────────────────────
  'newborn': {
    topicId: 'newborn',
    topicTitle: 'Newborn (0 – 6 Months)',
    questions: [
      'Was newborn hearing screening done?',
      'Any NICU stay?',
      'Not responding to sounds?',
      'Family history of hearing loss?',
    ],
    tests: ['OAE', 'ABR', 'BOA', 'Tympanometry'],
    whatItHelps: 'Detects hearing loss early so intervention can begin before speech development.',
  },
  'infant': {
    topicId: 'infant',
    topicTitle: 'Infant / Toddler (6 Months – 2.5 Years)',
    questions: [
      'Does the child respond to sounds?',
      'Delayed speech?',
      'Frequent ear infections?',
      'Difficulty in feeding / attention?',
    ],
    tests: ['VRA', 'OAE', 'Tympanometry', 'ABR'],
    whatItHelps: 'Identifies hearing issues that may delay speech and language milestones.',
  },
  'preschool': {
    topicId: 'preschool',
    topicTitle: 'Preschool Child (2.5 – 5 Years)',
    questions: [
      'Speech delay?',
      'Difficulty following instructions?',
      "Doesn't respond consistently?",
      'Learning concerns?',
    ],
    tests: ['Play Audiometry', 'OAE', 'Speech Detection', 'Tympanometry'],
    whatItHelps: 'Checks hearing ability through play-based tests suited for young children.',
  },
  'school-age': {
    topicId: 'school-age',
    topicTitle: 'School-Age Child (5 Years and Above)',
    questions: [
      'Difficulty hearing in class?',
      'Frequently asking for repetition?',
      'Academic concerns?',
    ],
    tests: ['PTA', 'Speech Audiometry', 'OAE', 'Special Tests'],
    whatItHelps: 'Identifies hearing difficulties that affect learning and classroom performance.',
  },
};

export function getQASession(topicId: string): QASession | null {
  return SESSIONS[topicId] ?? null;
}
