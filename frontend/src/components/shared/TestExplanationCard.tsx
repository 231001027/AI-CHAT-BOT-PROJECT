import { useState } from 'react';
import { ChevronDown, Loader2, PlayCircle, Sparkles, Video } from 'lucide-react';
import type { Explanation, RecommendedTest } from '@/lib/api';
import { aiApi } from '@/lib/api';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import {
  getTestDemoVideo,
  isAudioFile,
  isVideoFile,
} from '@/data/testDemoVideos';

export function TestExplanationCard({
  test,
  sessionId,
}: {
  test: RecommendedTest;
  sessionId: string;
}) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [explanation, setExplanation] = useState<Explanation | null>(null);
  const [error, setError] = useState<string | null>(null);
  const demo = getTestDemoVideo(test.test_code);

  async function loadExplanation() {
    if (explanation) {
      setOpen((v) => !v);
      return;
    }
    setOpen(true);
    setLoading(true);
    setError(null);
    try {
      const res = await aiApi.explainTest({
        session_id: sessionId,
        test_code: test.test_code,
        test_name: test.test_name,
      });
      setExplanation(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load explanation');
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card className="h-full">
      <CardHeader className="pb-3">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-base">{test.test_name}</CardTitle>
            <p className="mt-1 text-xs text-slate-500">
              Code: {test.test_code}
              {test.duration_minutes ? ` · ~${test.duration_minutes} min` : ''}
            </p>
          </div>
          <Badge variant="secondary">{test.rule_name || 'Recommended'}</Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-slate-600">{test.reason_text}</p>
        {test.description && (
          <p className="text-sm text-slate-500">{test.description}</p>
        )}
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={loadExplanation}
          className="w-full sm:w-auto"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Sparkles className="h-4 w-4" />
          )}
          {explanation ? (open ? 'Hide AI explanation' : 'Show AI explanation') : 'Explain this test'}
          <ChevronDown className={cn('h-4 w-4 transition', open && 'rotate-180')} />
        </Button>
        {open && (
          <div className="space-y-3 rounded-xl border border-slate-100 bg-slate-50 p-4">
            {loading && <p className="text-sm text-slate-500">Generating explanation…</p>}
            {error && <p className="text-sm text-red-600">{error}</p>}
            {explanation && (
              <>
                <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                  {explanation.explanation}
                </p>
                <p className="text-xs text-slate-400">Source: {explanation.source}</p>
              </>
            )}
          </div>
        )}

        <TestDemoVideoSlot
          testCode={test.test_code}
          testName={test.test_name}
          url={demo.url}
          fileName={demo.file}
          caption={demo.caption}
        />
      </CardContent>
    </Card>
  );
}

function TestDemoVideoSlot({
  testCode,
  testName,
  url,
  fileName,
  caption,
}: {
  testCode: string;
  testName: string;
  url?: string;
  fileName?: string;
  caption?: string;
}) {
  const [missing, setMissing] = useState(false);
  const media = url?.trim();
  const showPlayer = Boolean(media) && !missing;
  const audio = media ? isAudioFile(media) : false;
  const video = media ? isVideoFile(media) : false;

  return (
    <div className="space-y-2 border-t border-slate-100 pt-4">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
        <Video className="h-4 w-4 text-brand-600" aria-hidden="true" />
        Demo video
      </div>
      <p className="text-xs text-slate-500">
        {caption || `Watch how ${testName} is performed.`}
      </p>

      {showPlayer && video && (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-slate-900 aspect-video">
          <video
            className="h-full w-full"
            controls
            preload="metadata"
            title={`${testName} demo`}
            src={media}
            onError={() => setMissing(true)}
          >
            Your browser does not support video playback.
          </video>
        </div>
      )}

      {showPlayer && audio && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-5">
          <audio
            className="w-full"
            controls
            preload="metadata"
            title={`${testName} demo`}
            src={media}
            onError={() => setMissing(true)}
          >
            Your browser does not support audio playback.
          </audio>
        </div>
      )}

      {(!showPlayer || (!video && !audio)) && (
        <div
          className="flex aspect-video flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 px-4 text-center"
          role="img"
          aria-label={`Demo video placeholder for ${testCode}`}
        >
          <PlayCircle className="h-10 w-10 text-slate-300" aria-hidden="true" />
          <p className="text-sm font-medium text-slate-500">Upload demo file</p>
          <p className="max-w-sm text-xs text-slate-400">
            Place{' '}
            <span className="font-semibold text-slate-500">
              {fileName || `${testCode}.mp4`}
            </span>{' '}
            in <span className="font-semibold text-slate-500">public/demo-videos/</span>
          </p>
        </div>
      )}
    </div>
  );
}
