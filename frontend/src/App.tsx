import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { HomePage } from './pages/HomePage';
import { AssessmentPage } from './pages/AssessmentPage';
import { AdultCarePage } from './pages/AdultCarePage';
import { ChildCarePage } from './pages/ChildCarePage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { AboutPage } from './pages/AboutPage';
import { ContactPage } from './pages/ContactPage';
import { RelationshipPage } from './pages/patient/RelationshipPage';
import { RegisterPage } from './pages/patient/RegisterPage';
import { CategoryPage } from './pages/patient/CategoryPage';
import { QuestionnairePage } from './pages/patient/QuestionnairePage';
import { SummaryPage } from './pages/patient/SummaryPage';
import { RecommendationsPage } from './pages/results/RecommendationsPage';
import { ReportPage } from './pages/results/ReportPage';
import { LoginPage } from './pages/LoginPage';
import { GenerateFormPage } from './pages/GenerateFormPage';

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
      <Toaster position="top-center" richColors closeButton />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/take-test" element={<Navigate to="/register/relationship" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/generate-form" element={<GenerateFormPage />} />
          <Route path="/signup" element={<Navigate to="/" replace />} />
          <Route path="/register/signin" element={<Navigate to="/register/relationship" replace />} />
          <Route path="/register/signup" element={<Navigate to="/register/relationship" replace />} />
          <Route path="/register/relationship" element={<RelationshipPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/chat/category" element={<CategoryPage />} />
          <Route path="/chat/questionnaire" element={<QuestionnairePage />} />
          <Route path="/chat/summary" element={<SummaryPage />} />
          <Route path="/results/recommendations" element={<RecommendationsPage />} />
          <Route path="/results/report" element={<ReportPage />} />
          <Route path="/adult-care" element={<AdultCarePage />} />
          <Route path="/child-care" element={<ChildCarePage />} />
          <Route path="/ai-assistant" element={<AIAssistantPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/assessment" element={<AssessmentPage />} />
          <Route path="/admin/*" element={<Navigate to="/" replace />} />
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
