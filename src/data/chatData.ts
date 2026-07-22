export interface ChatResponse {
  keywords: string[];
  response: string;
  followups?: string[];
}

export const chatResponses: ChatResponse[] = [
  {
    keywords: ['child', 'kid', 'baby', 'son', 'daughter', 'infant'],
    response:
      'This could indicate hearing loss in your child. We recommend scheduling a hearing assessment with a paediatric audiologist. Early detection greatly improves speech and language development outcomes.',
    followups: ['Book a child assessment', 'Learn about OAE test', 'Speech delay concerns'],
  },
  {
    keywords: ['not responding', 'respond', 'no response', "doesn't respond", 'ignore'],
    response:
      'Not responding to sounds is an important early sign. If this happens repeatedly, a hearing screening (OAE / ABR) is strongly recommended to rule out hearing loss.',
    followups: ['What is OAE?', 'What is ABR?', 'Schedule screening'],
  },
  {
    keywords: ['ringing', 'buzzing', 'hissing', 'tinnitus'],
    response:
      'Ringing or buzzing in the ears is called tinnitus. It is often linked to noise exposure, stress, or inner-ear changes. An audiologist can assess severity and suggest management strategies.',
    followups: ['Tinnitus management tips', 'Book tinnitus assessment'],
  },
  {
    keywords: ['dizzy', 'dizziness', 'vertigo', 'spinning', 'balance', 'walking'],
    response:
      'Dizziness and balance issues may relate to the inner ear. Tests such as VNG and VEMP help evaluate vestibular function. Please consult an ENT specialist if symptoms are severe or sudden.',
    followups: ['What is VNG?', 'Balance assessment'],
  },
  {
    keywords: ['pain', 'ear pain', 'ache', 'discharge', 'fluid', 'infection'],
    response:
      'Ear pain with discharge often signals an ear infection. Keep the ear dry and see an ENT specialist promptly. Tympanometry can confirm whether fluid is present behind the eardrum.',
    followups: ['Find ENT specialist', 'What is tympanometry?'],
  },
  {
    keywords: ['muffled', "can't hear", 'cannot hear', 'hearing loss', 'asking repeat', 'repeat'],
    response:
      'Difficulty hearing or asking others to repeat may indicate hearing loss. A Pure Tone Audiometry (PTA) test is the first step to measure your hearing thresholds accurately.',
    followups: ['What is PTA?', 'Book hearing test'],
  },
  {
    keywords: ['hearing aid', 'aid', 'device', 'amplification'],
    response:
      'Hearing aids can significantly improve quality of life. An audiologist will recommend the right type based on your hearing loss severity, lifestyle, and budget.',
    followups: ['Types of hearing aids', 'Hearing aid maintenance'],
  },
  {
    keywords: ['cochlear', 'implant'],
    response:
      'Cochlear implants are an option for severe to profound hearing loss where hearing aids provide limited benefit. A thorough evaluation by a cochlear implant team is required.',
    followups: ['Cochlear implant evaluation', 'Candidacy criteria'],
  },
  {
    keywords: ['speech', 'delay', 'talking', 'talk', 'language'],
    response:
      'Delayed speech can be related to hearing difficulties. We recommend a combined hearing and speech-language assessment to identify the cause and start early intervention.',
    followups: ['Speech therapy options', 'Book speech assessment'],
  },
  {
    keywords: ['noise', 'loud', 'concert', 'workplace', 'earmuffs', 'earplugs'],
    response:
      'Noise exposure is a leading cause of preventable hearing loss. Always use ear protection in loud environments and limit listening volumes to safe levels (below 80 dB).',
    followups: ['Hearing protection tips', 'Safe listening levels'],
  },
  {
    keywords: ['newborn', '0-6', 'nicu', 'screening'],
    response:
      'Newborn hearing screening is recommended within the first month. OAE and ABR are painless tests done while the baby sleeps. Early screening enables timely intervention.',
    followups: ['Newborn screening details', 'What is ABR?'],
  },
  {
    keywords: ['school', 'academic', 'class', 'teacher', 'grades'],
    response:
      'Hearing issues can affect academic performance. A school-age hearing test (PTA + Speech Audiometry) can identify whether hearing is contributing to learning difficulties.',
    followups: ['School-age assessment', 'Classroom strategies'],
  },
  {
    keywords: ['sleep', 'insomnia', 'tinnitus sleep'],
    response:
      'Tinnitus can disturb sleep. Sound therapy, relaxation techniques, and a quiet background noise at bedtime often help. Please discuss persistent sleep issues with your audiologist.',
    followups: ['Tinnitus management', 'Sound therapy'],
  },
  {
    keywords: ['stress', 'anxiety', 'worried', 'depressed'],
    response:
      'Stress can worsen tinnitus and perceived hearing difficulties. Counselling, mindfulness, and hearing therapy together can provide meaningful relief.',
    followups: ['Counselling services', 'Stress reduction tips'],
  },
  {
    keywords: ['blockage', 'blocked', 'wax', 'earwax', 'plugged'],
    response:
      'A blocked sensation is often caused by earwax build-up. Avoid inserting cotton buds — an ENT or audiologist can safely remove wax and check the eardrum.',
    followups: ['Safe ear care', 'Book ear cleaning'],
  },
  {
    keywords: ['surgery', 'operation', 'mastoid', 'tube', 'grommet'],
    response:
      'If you have had previous ear surgery, share the details with your audiologist. It affects which tests are suitable and the interpretation of your results.',
    followups: ['Pre-surgery hearing test', 'Post-surgery follow-up'],
  },
  {
    keywords: ['fever', 'temperature', 'sick'],
    response:
      'Fever alongside ear symptoms may indicate an active infection. Please consult a doctor promptly, especially in young children, to prevent complications.',
    followups: ['Find ENT specialist', 'When to seek urgent care'],
  },
  {
    keywords: ['family', 'history', 'genetic', 'hereditary'],
    response:
      'A family history of hearing loss increases risk. A baseline hearing test is recommended, and periodic monitoring helps detect changes early.',
    followups: ['Book baseline test', 'Genetic counselling'],
  },
  {
    keywords: ['hyperacusis', 'sensitive', 'too loud', 'painful sound'],
    response:
      'Hyperacusis is increased sensitivity to everyday sounds. Sound therapy and gradual exposure under an audiologist can help desensitise and improve comfort.',
    followups: ['What is LDL test?', 'Hyperacusis management'],
  },
  {
    keywords: ['hello', 'hi', 'hey', 'start', 'help', 'default'],
    response:
      "Hello! I'm HearConnect AI. I can help you understand hearing-related concerns and suggest next steps. Could you describe the problem you or your child are experiencing?",
    followups: ['Hearing difficulty', 'Ringing in ears', 'Child hearing concern'],
  },
];

export const defaultResponse: ChatResponse = {
  keywords: [],
  response:
    "Thanks for sharing that. Based on what you've described, I recommend booking a professional hearing assessment. Could you tell me a bit more about when the symptoms started and which ear is affected?",
  followups: ['Book an assessment', 'Talk to an audiologist'],
};

export function findResponse(input: string): ChatResponse {
  const text = input.toLowerCase();
  for (const item of chatResponses) {
    if (item.keywords.some((k) => text.includes(k))) return item;
  }
  return defaultResponse;
}
