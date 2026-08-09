import { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { MessageCircle, X, Bot } from 'lucide-react';
import { ChatPanel, type ChatMessage } from './ChatPanel';
import { createInitialMessages } from './chatUtils';

export function Chatbot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>(createInitialMessages);

  return (
    <>
      <motion.button
        type="button"
        onClick={() => setOpen((v) => !v)}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.94 }}
        className="fixed bottom-5 right-5 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-purple-500 text-white shadow-card-hover"
        aria-label={open ? 'Close AI chat assistant' : 'Open AI chat assistant'}
        aria-expanded={open}
      >
        <span className="absolute inset-0 rounded-full bg-brand-500 animate-pulse-ring opacity-30" aria-hidden="true" />
        <AnimatePresence mode="wait" initial={false}>
          <motion.span
            key={open ? 'x' : 'chat'}
            initial={{ rotate: -90, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 90, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="relative"
          >
            {open ? <X size={24} /> : <MessageCircle size={24} />}
          </motion.span>
        </AnimatePresence>
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.92 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.92 }}
            transition={{ type: 'spring', stiffness: 320, damping: 26 }}
            className="fixed bottom-24 right-5 z-50 w-[calc(100vw-2.5rem)] max-w-sm h-[32rem] max-h-[75vh] flex flex-col rounded-3xl bg-white dark:bg-slate-900 shadow-card-hover border border-slate-200 dark:border-slate-800 overflow-hidden"
            role="dialog"
            aria-label="AI chat assistant"
          >
            <div className="flex items-center gap-3 bg-gradient-to-r from-brand-600 to-purple-600 px-4 py-3 text-white">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-white/20">
                <Bot size={18} />
              </span>
              <div className="flex-1">
                <p className="text-sm font-semibold leading-none">NIEPMD Audiology and Speech</p>
                <p className="mt-1 text-xs text-white/80 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-green-400" />
                  Online · AI assistant
                </p>
              </div>
            </div>
            <ChatPanel messages={messages} setMessages={setMessages} className="flex-1" compact />
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
