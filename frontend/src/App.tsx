import { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/Layout';
import { AdminGuard } from './components/admin/AdminGuard';
import { AdminLayout } from './components/admin/AdminLayout';
import { HomePage } from './pages/HomePage';
import { AssessmentPage } from './pages/AssessmentPage';
import { AdultCarePage } from './pages/AdultCarePage';
import { ChildCarePage } from './pages/ChildCarePage';
import { AIAssistantPage } from './pages/AIAssistantPage';
import { AboutPage } from './pages/AboutPage';
import { ContactPage } from './pages/ContactPage';
import { RelationshipPage } from './pages/patient/RelationshipPage';
import { RegisterPage } from './pages/patient/RegisterPage';
import { PatientLoginPage } from './pages/patient/PatientLoginPage';
import { PatientSignupPage } from './pages/patient/PatientSignupPage';
import { CategoryPage } from './pages/patient/CategoryPage';
import { QuestionnairePage } from './pages/patient/QuestionnairePage';
import { SummaryPage } from './pages/patient/SummaryPage';
import { RecommendationsPage } from './pages/results/RecommendationsPage';
import { ReportPage } from './pages/results/ReportPage';
import { AdminLoginPage } from './pages/admin/AdminLoginPage';
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { AdminQuestionsPage } from './pages/admin/AdminQuestionsPage';
import { AdminRulesPage } from './pages/admin/AdminRulesPage';
import { AdminDocumentsPage } from './pages/admin/AdminDocumentsPage';
import { AdminAiLogsPage } from './pages/admin/AdminAiLogsPage';
import { AdminDoctorsPage } from './pages/admin/AdminDoctorsPage';
import { AdminReportsPage } from './pages/admin/AdminReportsPage';
import { useSessionStore } from './store/session';
import { setStoredToken } from './lib/api';

if (typeof document !== 'undefined') {
  document.documentElement.classList.remove('dark');
  try {
    window.localStorage.removeItem('hc-theme');
  } catch {
    /* ignore */
  }
}

function AuthHydration() {
  const token = useSessionStore((s) => s.authToken);
  useEffect(() => {
    setStoredToken(token);
  }, [token]);
  return null;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthHydration />
      <Toaster position="top-center" richColors closeButton />
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<HomePage />} />
          <Route path="/take-test" element={<Navigate to="/register/relationship" replace />} />
          <Route path="/login" element={<PatientLoginPage />} />
          <Route path="/signup" element={<PatientSignupPage />} />
          <Route path="/register/signin" element={<PatientLoginPage />} />
          <Route path="/register/signup" element={<PatientSignupPage />} />
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
        </Route>

        <Route path="/admin/login" element={<AdminLoginPage />} />
        <Route element={<AdminGuard />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<Navigate to="dashboard" replace />} />
            <Route path="dashboard" element={<AdminDashboardPage />} />
            <Route path="questions" element={<AdminQuestionsPage />} />
            <Route path="rules" element={<AdminRulesPage />} />
            <Route path="documents" element={<AdminDocumentsPage />} />
            <Route path="ai-logs" element={<AdminAiLogsPage />} />
            <Route path="doctors" element={<AdminDoctorsPage />} />
            <Route path="reports" element={<AdminReportsPage />} />
          </Route>
        </Route>

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
