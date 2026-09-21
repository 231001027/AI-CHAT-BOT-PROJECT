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
const STUTTER_ONSET = ['Childhood', 'Adult', 'Not sure'];

/** Quick-reply options for the current question, if any. */
export function getQAAnswerOptions(session: QASession, questionIndex: number): string[] | null {
  const byIndex = session.answerOptionsByIndex?.[questionIndex];
  if (byIndex?.length) return byIndex;
  if (session.answerOptions?.length) return session.answerOptions;
  return null;
}

function isYes(answer: string | undefined): boolean {
  return answer?.trim().toLowerCase() === 'yes';
}

/** Recommended tests after Q&A — WAB/LPT only when answers match. */
export function getQARecommendedTests(session: QASession, answers: string[]): string[] {
  if (session.topicId !== 'adult-speech-language') {
    return session.tests;
  }
  const tests: string[] = [];
  if (isYes(answers[3])) {
    tests.push('WAB (Western Aphasia Battery)');
  }
  if (isYes(answers[0]) || isYes(answers[1]) || isYes(answers[2])) {
    tests.push('LPT (Linguistic Profile Test)');
  }
  return tests;
}

const SESSIONS: Record<string, QASession> = {
  // ── Adult Part 2 — Section A Speech ───────────────────────────────────────
  'adult-speech-language': {
    topicId: 'adult-speech-language',
    topicTitle: 'Speech and Language Issues',
    questions: [
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
    answerOptions: YES_NO_NOT_SURE,
  },
  'adult-stuttering': {
    topicId: 'adult-stuttering',
    topicTitle: 'Stuttering (Fluency)',
    questions: [
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
    answerOptions: YES_NO_NOT_SURE,
    answerOptionsByIndex: { 6: STUTTER_ONSET },
  },
  'adult-speech-clarity': {
    topicId: 'adult-speech-clarity',
    topicTitle: 'Speech Clarity',
    questions: [
      'Does your speech sound slurred or unclear enough that other people have trouble understanding you?',
      "Do you have difficulty saying a sequence of syllables quickly, such as 'puh-tuh-kuh'?",
      'Does your speech become less clear when you are tired?',
      'Have you noticed facial drooping, stiff lips, or slower tongue movements?',
      'Does your voice sometimes sound unusually flat, monotone, or robotic?',
      'When saying certain words, do you find yourself searching for the correct mouth position?',
    ],
    tests: ['Speech Sound / Clarity Assessment'],
    whatItHelps: 'Checks which speech sounds are clear and which need support.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'adult-voice-problems': {
    topicId: 'adult-voice-problems',
    topicTitle: 'Voice Problems',
    questions: [
      'Is your voice regularly hoarse, rough, weak, or breathy?',
      'Does your voice become tired or do you run out of air after talking for a moderate amount of time?',
      'Do you feel aching or tightness in your throat, or a constant lump-like feeling?',
      'Does your work require you to use your voice heavily, such as teaching, taking calls, or sales?',
      'Has a change in your voice or hoarseness lasted longer than two to three weeks?',
      'Does your voice unexpectedly break in pitch or develop involuntary shaking or tremor?',
    ],
    tests: ['Voice Assessment'],
    whatItHelps: 'Reviews voice quality, strain, and day-to-day voice use.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'adult-feeding-swallowing': {
    topicId: 'adult-feeding-swallowing',
    topicTitle: 'Feeding and Swallowing',
    questions: [
      'Do you cough, clear your throat, or choke when eating or drinking liquids?',
      'Do solid food, tablets, or liquids ever feel as though they are stuck in your throat or chest?',
      "Have you changed your diet to softer foods or purees because you're worried about choking?",
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
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-stuttering': {
    topicId: 'child-stuttering',
    topicTitle: 'Stuttering (Fluency)',
    questions: [
      "Does your child repeat a sound or syllable several times, such as 'b-b-b-ball'?",
      "Does your child hold a sound for a long time, such as 'ssss-snake'?",
      'Does your child sometimes get stuck while trying to speak, with no sound coming out?',
      'Do you notice eye blinking, facial tension, or other movements when your child is having difficulty speaking?',
      'Does your child become frustrated, cover their mouth, or avoid talking when speech is difficult?',
      "Does your child's speech sometimes sound very fast, uneven, or as though words run together?",
    ],
    tests: ['Fluency Assessment', 'OAE'],
    whatItHelps: 'Looks at how smoothly your child speaks and what support may help.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-speech-clarity': {
    topicId: 'child-speech-clarity',
    topicTitle: 'Speech Clarity',
    questions: [
      "Do people who aren't used to your child's speech have trouble understanding what they say?",
      "Does your child leave out or replace sounds in familiar words, such as saying 'tat' instead of 'cat'?",
      'Do you or other family members often need to repeat what your child says or explain it to others?',
      "Does your child leave out syllables in longer words, such as saying 'nana' for 'banana'?",
      'When repeating a word, does your child appear to search for the right mouth position or make unusual mouth movements?',
      'Did your child begin babbling or using first words later than expected for their age?',
    ],
    tests: ['Speech Sound / Clarity Assessment', 'OAE'],
    whatItHelps: 'Checks which speech sounds are clear and which need support.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-voice-problems': {
    topicId: 'child-voice-problems',
    topicTitle: 'Voice Problems',
    questions: [
      "Does your child's voice regularly sound hoarse, rough, or breathy?",
      "Does your child's voice become weak, strained, or disappear after talking or crying for a while?",
      'Does your child complain that their throat feels sore, tight, or uncomfortable after speaking?',
      'Does your child frequently shout, scream, or make harsh sounds while playing?',
      'Has the unusual voice quality continued for more than two weeks?',
      "When your child isn't sick, do they still sound unusually nasal or as though their nose is blocked?",
    ],
    tests: ['Voice Assessment', 'OAE'],
    whatItHelps: 'Reviews voice quality, strain, and day-to-day voice use.',
    answerOptions: YES_NO_NOT_SURE,
  },
  'child-feeding-swallowing': {
    topicId: 'child-feeding-swallowing',
    topicTitle: 'Feeding and Swallowing',
    questions: [
      'Does your child cough, choke, or gag while eating or drinking, especially with liquids?',
      "Does food or liquid spill from your child's lips or come through the nose while swallowing?",
      "Do your child's usual meals often take more than 30 to 40 minutes to finish?",
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
