import { motion } from 'motion/react';

const Footer = () => {
  return (
    <motion.footer 
      className="footer footer-center py-6 lg:py-8"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 1, duration: 0.5 }}
    >
      <div>
        <p className="text-sm lg:text-base text-white font-geist">
          Impulsado por literatura científica y flujos de investigación asistida
        </p>
      </div>
    </motion.footer>
  );
};

export default Footer;
