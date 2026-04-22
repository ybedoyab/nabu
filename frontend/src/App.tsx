import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ResearchProvider } from './context/ResearchContext';
import Home from './pages/Home';
import SearchPage from './pages/SearchPage';

function App() {
  return (
    <ResearchProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-base-100">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/search" element={<SearchPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ResearchProvider>
  );
}

export default App;