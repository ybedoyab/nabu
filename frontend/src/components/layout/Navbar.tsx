import { motion } from 'motion/react';
import { useState, useEffect } from 'react';
import ThemeToggle from './ThemeToggle';
import logoClaro from '../../assets/logo_claro.png';
import logoOscuro from '../../assets/logo_oscuro.png';

const Navbar = () => {
  const [currentTheme, setCurrentTheme] = useState('default');

  useEffect(() => {
    const updateTheme = () => {
      const theme = document.documentElement.getAttribute('data-theme') || 'default';
      setCurrentTheme(theme);
    };

    // Initial theme check
    updateTheme();

    // Listen for theme changes
    const observer = new MutationObserver(updateTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ['data-theme']
    });

    return () => observer.disconnect();
  }, []);

  const logoSrc = currentTheme === 'dark' ? logoClaro : logoOscuro;

  return (
    <motion.header 
      className="navbar px-4 lg:px-8 py-4 relative"
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div className="absolute inset-0 bg-gradient-to-b from-base-100/60 via-base-100/30 to-transparent backdrop-blur-sm" />
      
      <div className="navbar-start relative z-10">
        <motion.div 
          className="flex items-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          <img 
            src={logoSrc} 
            alt="Nabu Logo" 
            className="h-8 lg:h-10 w-auto"
          />
        </motion.div>
      </div>

      <div className="navbar-end relative z-10">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.4, duration: 0.4 }}
        >
          <ThemeToggle />
        </motion.div>
      </div>
    </motion.header>
  );
};

export default Navbar;
