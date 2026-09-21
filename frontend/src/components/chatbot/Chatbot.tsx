import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';

const ASSISTANT_PHOTO = '/assistant.png';
const AI_PAGE = '/ai-assistant';

export function Chatbot() {
  const navigate = useNavigate();
  const location = useLocation();

  if (location.pathname === AI_PAGE) return null;

  function goToAssistant() {
    navigate(AI_PAGE);
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-2">
      <motion.button
        type="button"
        onClick={goToAssistant}
        initial={{ opacity: 0, y: 8, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ type: 'spring', stiffness: 320, damping: 22 }}
        className="relative mb-1 mr-0.5 rounded-2xl bg-white px-5 py-3 text-left shadow-lg ring-1 ring-brand-200"
        aria-label="May I help you — Talk to AI"
      >
        <motion.p
          className="whitespace-nowrap text-sm font-bold uppercase tracking-widest text-brand-700"
          animate={{ y: [0, -2, 0] }}
          transition={{ duration: 2.2, repeat: Infinity, ease: 'easeInOut' }}
        >
          May I help you
        </motion.p>
        <span
          className="absolute -bottom-2 right-7 h-0 w-0 border-x-[8px] border-t-[10px] border-x-transparent border-t-white drop-shadow-sm"
          aria-hidden="true"
        />
      </motion.button>

      <motion.button
        type="button"
        onClick={goToAssistant}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.94 }}
        className="relative flex h-32 w-32 items-end justify-center bg-transparent p-0"
        aria-label="Talk to AI"
      >
        <img
          src={ASSISTANT_PHOTO}
          alt="NIEPMD AI assistant"
          className="relative h-32 w-auto max-w-[8rem] object-contain object-bottom drop-shadow-md"
        />
      </motion.button>
    </div>
  );
}
