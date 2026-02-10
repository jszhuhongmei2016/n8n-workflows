import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import ProjectsPage from './pages/ProjectsPage'
import ProjectDetailPage from './pages/ProjectDetailPage'
import Stage1Page from './pages/Stage1Page'
import Stage2Page from './pages/Stage2Page'
import GenerationPage from './pages/GenerationPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/projects" element={<ProjectsPage />} />
        <Route path="/projects/:id" element={<ProjectDetailPage />} />
        <Route path="/projects/:id/stage1" element={<Stage1Page />} />
        <Route path="/projects/:id/stage2" element={<Stage2Page />} />
        <Route path="/projects/:id/generation" element={<GenerationPage />} />
      </Routes>
    </Layout>
  )
}

export default App
