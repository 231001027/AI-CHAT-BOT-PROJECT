import type { Option, Question } from '@/lib/api';
import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';

export function OptionButton({
  option,
  selected,
  onSelect,
  disabled,
}: {
  option: Option;
  selected?: boolean;
  onSelect: (option: Option) => void;
  disabled?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => onSelect(option)}
      className={cn(
        'w-full rounded-xl border px-4 py-3 text-left text-sm font-medium transition-all',
        selected
          ? 'border-brand-500 bg-brand-50 text-brand-800 shadow-soft'
          : 'border-slate-200 bg-white text-slate-700 hover:border-brand-300 hover:bg-brand-50/40',
        disabled && 'opacity-60 pointer-events-none',
      )}
    >
      {option.label}
    </button>
  );
}

export function QuestionCard({
  question,
  onSelect,
  disabled,
  selectedOptionId,
}: {
  question: Question;
  onSelect: (option: Option) => void;
  disabled?: boolean;
  selectedOptionId?: string;
}) {
  return (
    <Card className="overflow-hidden">
      <CardHeader className="bg-gradient-to-r from-brand-50 to-white">
        <CardTitle className="text-base leading-snug sm:text-lg">{question.text}</CardTitle>
        {question.help_text && (
          <p className="text-sm text-slate-500">{question.help_text}</p>
        )}
      </CardHeader>
      <CardContent className="space-y-2 pt-4">
        {question.options
          .slice()
          .sort((a, b) => a.display_order - b.display_order)
          .map((opt) => (
            <OptionButton
              key={opt.id}
              option={opt}
              selected={selectedOptionId === opt.id}
              onSelect={onSelect}
              disabled={disabled}
            />
          ))}
      </CardContent>
    </Card>
  );
}
