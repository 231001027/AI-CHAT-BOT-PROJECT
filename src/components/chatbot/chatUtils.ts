import type { ChatMessage } from './ChatPanel';

const initialBot: ChatMessage = {
  id: 0,
  role: 'bot',
  text: "Hello 👋 I can help identify hearing-related concerns. Please select a topic below or describe your problem in your own words.",
  showTopicCards: true,
};

export function createInitialMessages(): ChatMessage[] {
  return [{ ...initialBot }];
}
