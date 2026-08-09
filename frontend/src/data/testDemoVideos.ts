/**
 * Demo media for recommended tests.
 *
 * Upload files into:  frontend/public/demo-videos/
 * Name them by test code, e.g. PTA.mp4, TYMP.mp4, OAE.mp3
 *
 * Then set `file` below to match. The app serves them as /demo-videos/<file>.
 */
export type TestDemoVideo = {
  /** Filename inside public/demo-videos/ (e.g. "PTA.mp4" or "PTA.mp3") */
  file?: string;
  /** Optional caption under the player */
  caption?: string;
};

export const TEST_DEMO_VIDEOS: Record<string, TestDemoVideo> = {
  PTA: { file: 'PTA.mp4', caption: 'How Pure Tone Audiometry is done' },
  TYMP: { file: 'TYMP.mp3', caption: 'How Tympanometry is done' },
  SPEECH: { file: 'SPEECH.mp3', caption: 'How Speech Audiometry is done' },
  OAE: { file: 'OAE.mp3', caption: 'How Otoacoustic Emissions testing is done' },
  ABR: { file: 'ABR.mp3', caption: 'How ABR testing is done' },
  VNG: { file: 'VNG.mp3', caption: 'How balance / VNG testing is done' },
  OTOSCOPY: { file: 'OTOSCOPY.mp3', caption: 'How an ear examination is done' },
  TINN_ASSESS: { file: 'TINN_ASSESS.mp3', caption: 'How tinnitus assessment is done' },
  SLP_EVAL: { file: 'SLP_EVAL.mp3', caption: 'How a speech-language evaluation is done' },
  VOICE_EVAL: { file: 'VOICE_EVAL.mp3', caption: 'How a voice assessment is done' },
  FLUENCY_EVAL: { file: 'FLUENCY_EVAL.mp3', caption: 'How a fluency assessment is done' },
  ARTIC_EVAL: { file: 'ARTIC_EVAL.mp3', caption: 'How a speech clarity assessment is done' },
  SWALLOW_ASSESS: { file: 'SWALLOW_ASSESS.mp3', caption: 'How a swallowing assessment is done' },
};

const DEMO_BASE = '/demo-videos';

export function demoPublicUrl(file: string): string {
  return `${DEMO_BASE}/${file.replace(/^\/+/, '')}`;
}

export function isAudioFile(fileOrUrl: string): boolean {
  return /\.(mp3|wav|m4a|aac)(\?|$)/i.test(fileOrUrl);
}

export function isVideoFile(fileOrUrl: string): boolean {
  return /\.(mp4|webm|ogg|mov)(\?|$)/i.test(fileOrUrl);
}

export function getTestDemoVideo(testCode: string): TestDemoVideo & { url?: string } {
  const entry = TEST_DEMO_VIDEOS[testCode] ?? { caption: `Demo for ${testCode}` };
  return {
    ...entry,
    url: entry.file ? demoPublicUrl(entry.file) : undefined,
  };
}
