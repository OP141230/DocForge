import { BrowserRouter, Routes, Route } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import DocumentPage from './pages/DocumentPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/document/:id" element={<DocumentPage />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
