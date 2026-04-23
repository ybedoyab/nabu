import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';
import SearchBar from './SearchBar';
import CategoryTags from './CategoryTags';

const HeroSection = () => {
  const navigate = useNavigate();

  const handleSearch = (query: string) => {
    navigate(`/search?q=${encodeURIComponent(query)}`);
  };

  return (
    <main className="flex-1 flex flex-col items-center justify-center px-4 lg:px-8 py-8 lg:py-16">
      <motion.h1
        className="text-3xl lg:text-5xl font-bold text-primary font-geist text-center mb-4 lg:mb-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        Nabu
      </motion.h1>

      <motion.p
        className="text-base lg:text-xl text-base-content/70 font-geist text-center mb-8 lg:mb-12 max-w-3xl px-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        Explora artículos científicos, compara enfoques y encuentra evidencia útil para estudiar, investigar o tomar decisiones.
      </motion.p>

      <motion.div
        className="w-full flex justify-center mb-8 lg:mb-12 px-4"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
      >
        <SearchBar onSearch={handleSearch} />
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.8 }}
      >
        <CategoryTags />
      </motion.div>
    </main>
  );
};

export default HeroSection;
