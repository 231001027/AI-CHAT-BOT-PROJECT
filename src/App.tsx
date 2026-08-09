import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { AssessmentPage } from './pages/AssessmentPage';
import { AdultCarePage } from './pages/AdultCarePage';
import { ChildCarePage } from './pages/ChildCarePage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { AboutPage } from './pages/AboutPage';
import { ContactPage } from './pages/ContactPage';

// Force light theme — clear any previously saved dark preference
if (typeof document !== 'undefined') {
  document.documentElement.classList.remove('dark');
  try {
    window.localStorage.removeItem('hc-theme');
  } catch {
    /* ignore */
  }
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/take-test" element={<AssessmentPage />} />
          <Route path="/adult-care" element={<AdultCarePage />} />
          <Route path="/child-care" element={<ChildCarePage />} />
          <Route path="/ai-assistant" element={<AIAssistantPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
