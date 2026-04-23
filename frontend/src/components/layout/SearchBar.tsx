import { Search, X, Sparkles } from 'lucide-react';
import { motion } from 'motion/react';
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useResearch } from '../../context/ResearchContext';

interface SearchBarProps {
  onSearch?: (query: string) => void;
  defaultValue?: string;
  value?: string;
  isAIEnabled?: boolean;
}


const SearchBar = ({ onSearch, defaultValue = '', value, isAIEnabled = true }: SearchBarProps) => {
  const [query, setQuery] = useState(value ?? defaultValue);

  useEffect(() => {
    if (value !== undefined) setQuery(value);
  }, [value]);
  const [isSearching, setIsSearching] = useState(false);
  const navigate = useNavigate();
  const { getRecommendations, isLoading } = useResearch();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsSearching(true);
    
    try {
      if (isAIEnabled) {
        // Use AI search functionality
        await getRecommendations(query.trim());
        // Navigate to search page to show results
        navigate(`/search?q=${encodeURIComponent(query.trim())}`);
      } else if (onSearch) {
        // Use traditional search
        onSearch(query);
      }
    } catch (err) {
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleClear = () => {
    setQuery('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch(e);
    }
  };

  return (
    <>
      <form onSubmit={handleSearch} className="w-full max-w-2xl">
        <motion.div 
          className="relative flex items-center w-full bg-base-200/92 rounded-full border border-base-300 shadow-sm hover:shadow-md transition-shadow duration-300 backdrop-blur-sm"
          whileFocus={{ scale: 1.005 }}
          transition={{ duration: 0.3 }}
        >
          <motion.input
            type="text"
            placeholder={isAIEnabled ? "Pregunta sobre un tema, artículo, método o tendencia de investigación..." : "Busca artículos y temas de investigación..."}
            className="flex-1 px-6 py-4 text-base lg:text-lg bg-transparent border-0 outline-none placeholder:text-base-content/60"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isSearching || isLoading}
          />
          
          {query && !isSearching && (
            <motion.button
              type="button"
              onClick={handleClear}
              className="p-2 hover:bg-base-300 rounded-full transition-colors duration-300 mr-2"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              transition={{ duration: 0.3 }}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              aria-label="Limpiar búsqueda"
            >
              <X className="w-5 h-5 text-base-content/60 hover:text-base-content transition-colors duration-300" />
            </motion.button>
          )}
          
        <motion.button 
          type="submit"
          className="p-3 hover:bg-base-300 rounded-full transition-colors duration-300 mr-1"
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          transition={{ duration: 0.3 }}
          aria-label={isAIEnabled ? "Preguntar a la IA" : "Buscar"}
          disabled={isSearching || isLoading}
        >
          {isAIEnabled ? (
            <Sparkles className={`w-5 h-5 transition-colors duration-300 ${
              isSearching || isLoading ? 'text-primary animate-pulse' : 'text-base-content/60 hover:text-primary'
            }`} />
          ) : (
            <Search className={`w-5 h-5 transition-colors duration-300 ${
              isSearching || isLoading ? 'text-primary animate-pulse' : 'text-base-content/60 hover:text-primary'
            }`} />
          )}
        </motion.button>
        </motion.div>

        {(isSearching || isLoading) && (
          <motion.div
            className="mt-3 flex items-center justify-center gap-2 text-sm text-base-content/70"
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <span className="loading loading-dots loading-sm text-primary" />
            <span>Cargando artículos...</span>
          </motion.div>
        )}
      </form>
    </>
  );
};

export default SearchBar;
