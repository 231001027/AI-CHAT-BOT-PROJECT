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
  /** Default quick-reply chips for every question (e.g. Yes / No / Not sure). */
  answerOptions?: string[];
  /** Per-question overrides keyed by 0-based index. */
  answerOptionsByIndex?: Record<number, string[]>;
}

const YES_NO_NOT_SURE = ['Yes', 'No', 'Not sure'];
const EAR_SIDE = ['Right', 'Left', 'Both', 'Not sure'];
const EAR_COMPARE = ['Right', 'Left', 'Both same', 'Not sure'];
const STUTTER_ONSET = ['Since childhood', 'Recently', 'Not sure'];
const CLARITY_ONSET = ['Suddenly', 'Gradually', 'Not sure'];

/** Quick-reply options for the current question, if any. */
export function getQAAnswerOptions(session: QASession, questionIndex: number): string[] | null {
  const byIndex = session.answerOptionsByIndex?.[questionIndex];
  if (byIndex?.length) return byIndex;
  if (session.answerOptions?.length) return session.answerOptions;
  return null;
}

const SESSIONS: Record<string, QASession> = {
  // ── Adult Part 2 — Section A Speech ───────────────────────────────────────
  'adult-speech-language': {
    topicId: 'adult-speech-language',
    topicTitle: 'Speech and Language Issues',
    questions: [
      'Do you struggle to find the right word?',
      'Is it hard to understand what others say?',
      'Any difficulty reading, writing or with numbers?',
      'Did this start after a stroke or head injury?',
      'Does it affect your work or daily life?',
    ],
    tests: ['Speech-Language Evaluation', 'Pure Tone Audiometry'],
    whatItHelps: 'Reviews how you understand and use language, and checks hearing.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'adult-stuttering': {
    topicId: 'adult-stuttering',
    topicTitle: 'Stuttering (Fluency)',
    questions: [
      'Do you repeat sounds or words while speaking?',
      'Do you get stuck on a word?',
      'Do you avoid calls or speaking situations?',
      'Any tension in face or jaw while speaking?',
      'When did it start?',
    ],
    tests: ['Fluency Assessment', 'Pure Tone Audiometry'],
    whatItHelps: 'Looks at how smoothly you speak and what support may help.',
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 4: STUTTER_ONSET },
  },
  'adult-speech-clarity': {
    topicId: 'adult-speech-clarity',
    topicTitle: 'Speech Clarity',
    questions: [
      'Do people often ask you to repeat?',
      'Does your speech sound slurred or slow?',
      'Does it get worse when you are tired?',
      'Any weakness in face, lips or tongue?',
      'How did it start?',
    ],
    tests: ['Speech Sound / Clarity Assessment', 'Pure Tone Audiometry'],
    whatItHelps: 'Checks which speech sounds are clear and which need support.',
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 4: CLARITY_ONSET },
  },
  'adult-voice-problems': {
    topicId: 'adult-voice-problems',
    topicTitle: 'Voice Problems',
    questions: [
      'Is your voice hoarse, rough or weak?',
      'Does your voice tire out after talking?',
      'Any throat pain or tightness while speaking?',
      'Does your job need heavy voice use?',
      'Has your voice been different for over 2 weeks?',
    ],
    tests: ['Voice Assessment', 'Pure Tone Audiometry'],
    whatItHelps: 'Reviews voice quality, strain, and day-to-day voice use.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'adult-feeding-swallowing': {
    topicId: 'adult-feeding-swallowing',
    topicTitle: 'Feeding and Swallowing',
    questions: [
      'Do you cough or choke while eating or drinking?',
      'Does food feel stuck in your throat or chest?',
      'Do meals take much longer than before?',
      'Have you changed your diet because of this?',
      'Any weight loss or repeated chest infections?',
    ],
    tests: ['Clinical Swallowing Assessment', 'Speech-Language Evaluation'],
    whatItHelps: 'Checks safety and comfort when you eat and drink.',
    answerOptions: YES_NO_NOT_SURE,
  },
  // ── Adult Part 2 — Section B Audiology ────────────────────────────────────
  'hearing-difficulty': {
    topicId: 'hearing-difficulty',
    topicTitle: 'Hearing Difficulty',
    questions: [
      'Is it hard to follow conversation in noisy places?',
      'Do you often ask people to repeat?',
      'Do others say your TV volume is too loud?',
      'Is one ear worse than the other?',
      'Any long-term loud noise exposure at work?',
    ],
    tests: ['Hearing Test (PTA)', 'Speech Audiometry', 'Tympanometry'],
    whatItHelps: 'Checks how well you hear and the type of hearing loss.',
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 3: EAR_COMPARE },
  },
  'ringing-in-ears': {
    topicId: 'ringing-in-ears',
    topicTitle: 'Ringing in the Ears',
    questions: [
      'Do you hear ringing or buzzing others cannot?',
      'Is it present even in a quiet room?',
      'Does it disturb your sleep or focus?',
      'Did it start after loud noise, infection or new medicine?',
      'Which ear?',
    ],
    tests: ['Hearing Test (PTA)', 'Tinnitus Assessment', 'Tympanometry'],
    whatItHelps: 'Assesses ringing concerns together with hearing levels.',
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 4: EAR_SIDE },
  },
  'dizziness-balance': {
    topicId: 'dizziness-balance',
    topicTitle: 'Dizziness / Balance',
    questions: [
      'Do you feel dizzy, spinning or unsteady?',
      'Does it start when you turn your head or stand up?',
      'Any vomiting, hearing loss or ear fullness with it?',
      'Have you fallen or nearly fallen because of it?',
      'Is walking harder in the dark?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'VNG / balance screening'],
    whatItHelps: 'Looks at balance concerns that can share pathways with the ear.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'other-hearing-related': {
    topicId: 'other-hearing-related',
    topicTitle: 'Other Hearing Issues',
    questions: [
      'Do you feel the ear is blocked or under pressure?',
      'Are normal sounds uncomfortably loud?',
      'Is it hard to tell where a sound comes from?',
      'Are you on any long-term medication?',
      'Do you already use a hearing aid?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'Speech Audiometry'],
    whatItHelps: 'Screens other ear-related concerns that affect hearing comfort.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'ear-pain-discharge': {
    topicId: 'ear-pain-discharge',
    topicTitle: 'Ear Pain / Discharge',
    questions: [
      'Do you have pain or discomfort in the ear?',
      'Any fluid, pus or blood from the ear?',
      'Any fever along with it?',
      'Any recent cold, cough or blocked nose?',
      'Has this happened before in the past year?',
    ],
    tests: ['Ear Examination', 'Tympanometry', 'Hearing Test (PTA)'],
    whatItHelps: 'Checks for infection, fluid, or middle-ear problems causing pain or discharge.',
    answerOptions: YES_NO_NOT_SURE,
  },
  // Legacy topic aliases (old Adult Care deep links)
  tinnitus: {
    topicId: 'ringing-in-ears',
    topicTitle: 'Ringing in the Ears',
    questions: [
      'Do you hear ringing or buzzing others cannot?',
      'Is it present even in a quiet room?',
      'Does it disturb your sleep or focus?',
      'Did it start after loud noise, infection or new medicine?',
      'Which ear?',
    ],
    tests: ['Hearing Test (PTA)', 'Tinnitus Assessment', 'Tympanometry'],
    whatItHelps: 'Assesses ringing concerns together with hearing levels.',
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 4: EAR_SIDE },
  },
  'balance-problems': {
    topicId: 'dizziness-balance',
    topicTitle: 'Dizziness / Balance',
    questions: [
      'Do you feel dizzy, spinning or unsteady?',
      'Does it start when you turn your head or stand up?',
      'Any vomiting, hearing loss or ear fullness with it?',
      'Have you fallen or nearly fallen because of it?',
      'Is walking harder in the dark?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'VNG / balance screening'],
    whatItHelps: 'Looks at balance concerns that can share pathways with the ear.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'ear-pain': {
    topicId: 'ear-pain-discharge',
    topicTitle: 'Ear Pain / Discharge',
    questions: [
      'Do you have pain or discomfort in the ear?',
      'Any fluid, pus or blood from the ear?',
      'Any fever along with it?',
      'Any recent cold, cough or blocked nose?',
      'Has this happened before in the past year?',
    ],
    tests: ['Ear Examination', 'Tympanometry', 'Hearing Test (PTA)'],
    whatItHelps: 'Checks for infection, fluid, or middle-ear problems causing pain or discharge.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'other-hearing-problems': {
    topicId: 'other-hearing-related',
    topicTitle: 'Other Hearing Issues',
    questions: [
      'Do you feel the ear is blocked or under pressure?',
      'Are normal sounds uncomfortably loud?',
      'Is it hard to tell where a sound comes from?',
      'Are you on any long-term medication?',
      'Do you already use a hearing aid?',
    ],
    tests: ['Hearing Test (PTA)', 'Tympanometry', 'Speech Audiometry'],
    whatItHelps: 'Screens other ear-related concerns that affect hearing comfort.',
    answerOptions: YES_NO_NOT_SURE,
  },
  // ── Child Part 1 — Section A Speech ───────────────────────────────────────
  'child-speech-language': {
    topicId: 'child-speech-language',
    topicTitle: 'Speech and Language Issues',
    questions: [
      'Does your child speak less than other children of the same age?',
      'Does your child follow simple instructions?',
      'Does your child point or gesture instead of talking?',
      'Has your child stopped using words they knew before?',
      'Is it hard for your child to hold a conversation?',
    ],
    tests: ['Speech-Language Evaluation', 'OAE'],
    whatItHelps: 'Reviews how your child understands and uses language, and checks hearing.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-stuttering': {
    topicId: 'child-stuttering',
    topicTitle: 'Stuttering (Fluency)',
    questions: [
      'Does your child repeat sounds or words while speaking?',
      'Does your child get stuck on a word?',
      'Does your child stretch out sounds?',
      'Any eye blinking or head movements while speaking?',
      'Does your child avoid speaking because of this?',
    ],
    tests: ['Fluency Assessment', 'OAE'],
    whatItHelps: 'Looks at how smoothly your child speaks and what support may help.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-speech-clarity': {
    topicId: 'child-speech-clarity',
    topicTitle: 'Speech Clarity',
    questions: [
      'Do outsiders find it hard to understand your child?',
      'Does your child miss or mix up sounds in words?',
      'Do you have to repeat what your child said?',
      'Is your child’s speech too fast, slow or mumbled?',
      'Did your child start speaking late?',
    ],
    tests: ['Speech Sound / Clarity Assessment', 'OAE'],
    whatItHelps: 'Checks which speech sounds are clear and which need support.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-voice-problems': {
    topicId: 'child-voice-problems',
    topicTitle: 'Voice Problems',
    questions: [
      'Is your child’s voice hoarse or rough?',
      'Does the voice get weak after talking a while?',
      'Does your child complain of throat pain while speaking?',
      'Does your child shout or scream often?',
      'Has the voice been different for over 2 weeks?',
    ],
    tests: ['Voice Assessment', 'OAE'],
    whatItHelps: 'Reviews voice quality, strain, and day-to-day voice use.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-feeding-swallowing': {
    topicId: 'child-feeding-swallowing',
    topicTitle: 'Feeding and Swallowing',
    questions: [
      'Does your child cough or choke while eating or drinking?',
      'Does food or liquid come out of the nose or mouth?',
      'Does a meal take more than 30 minutes?',
      'Does your child refuse solids or liquids?',
      'Poor weight gain or repeated chest infections?',
    ],
    tests: ['Feeding and Swallowing Assessment', 'Speech-Language Evaluation'],
    whatItHelps: 'Checks safety and comfort when your child eats and drinks.',
    answerOptions: YES_NO_NOT_SURE,
  },
  // ── Child Part 1 — Section B Audiology ────────────────────────────────────
  'child-hearing-difficulty': {
    topicId: 'child-hearing-difficulty',
    topicTitle: 'Hearing Difficulty',
    questions: [
      'Does your child not respond when called from behind?',
      'Does your child ask you to repeat often?',
      'Does your child keep the TV volume very high?',
      'Is hearing harder in noisy places?',
      'Any hearing loss in the family?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'OAE'],
    whatItHelps: 'Measures how soft a sound your child can hear and checks the middle ear.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-ringing-in-ears': {
    topicId: 'child-ringing-in-ears',
    topicTitle: 'Ringing in the Ears',
    questions: [
      'Does your child hear ringing or buzzing in the ear?',
      'Is it present even in a quiet room?',
      'Does it disturb sleep or concentration?',
      'Did it start after loud noise, infection or injury?',
      'Which ear?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'OAE'],
    whatItHelps: 'Assesses ringing concerns together with hearing levels.',
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 4: EAR_SIDE },
  },
  'child-dizziness-balance': {
    topicId: 'child-dizziness-balance',
    topicTitle: 'Dizziness / Balance',
    questions: [
      'Does your child feel dizzy or unsteady?',
      'Does your child fall or bump into things often?',
      'Does dizziness start with sudden head movement?',
      'Any vomiting or hearing loss with it?',
      'Is walking harder in the dark?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'Balance screening'],
    whatItHelps: 'Looks at balance concerns that can share pathways with the ear.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-other-hearing': {
    topicId: 'child-other-hearing',
    topicTitle: 'Other Hearing Issues',
    questions: [
      'Does your child feel the ear is blocked or full?',
      'Is your child upset by loud everyday sounds?',
      'Is it hard to tell where a sound comes from?',
      'Frequent colds, allergy or blocked nose?',
      'Loud earphone use or noise exposure?',
    ],
    tests: ['PTA / age-appropriate hearing test', 'Tympanometry', 'OAE'],
    whatItHelps: 'Screens other ear-related concerns that affect hearing comfort.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-ear-pain-discharge': {
    topicId: 'child-ear-pain-discharge',
    topicTitle: 'Ear Pain / Discharge',
    questions: [
      'Does your child have ear pain or pull at the ear?',
      'Any fluid, pus or blood from the ear?',
      'Any fever along with it?',
      'Any recent cold or blocked nose?',
      'Has this happened before in the past year?',
    ],
    tests: ['Tympanometry', 'Ear Examination', 'PTA / age-appropriate hearing test'],
    whatItHelps: 'Checks for infection, fluid, or middle-ear problems causing pain or discharge.',
    answerOptions: YES_NO_NOT_SURE,
  },
};

export function getQASession(topicId: string): QASession | null {
  return SESSIONS[topicId] ?? null;
}
