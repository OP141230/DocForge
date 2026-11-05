import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import DocumentPage from './pages/DocumentPage'
import ConversationPage from './pages/ConversationPage'
import DocumentBriefManager from './components/DocumentBriefManager'
import KnowledgeBasePage from './pages/KnowledgeBasePage'

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          <Route element={<ProtectedRoute />}>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/document/:id" element={<DocumentPage />} />
            <Route path="/conversation/:id" element={<ConversationPage />} />
            <Route path="/briefs" element={<DocumentBriefManager />} />
            <Route path="/knowledge" element={<KnowledgeBasePage />} />
          </Route>
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App
