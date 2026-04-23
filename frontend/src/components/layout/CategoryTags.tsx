import { motion } from 'motion/react';

interface CategoryTagsProps {
  onSelect?: (category: string) => void;
}

const CategoryTags = ({ onSelect }: CategoryTagsProps) => {
  const categories = [
    'Inteligencia artificial',
    'Robótica',
    'Biotecnología',
    'Cambio climático',
    'Materiales',
    'Salud digital',
  ];

  return (
    <div className="flex flex-wrap justify-center gap-3 lg:gap-4">
      {categories.map((category, index) => (
        <motion.button
          key={category}
          className="btn btn-soft btn-primary btn-sm lg:btn-md font-geist"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.1 * index, duration: 0.3 }}
          whileHover={{ scale: 1.1, y: -2 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => onSelect?.(category)}
        >
          {category}
        </motion.button>
      ))}
    </div>
  );
};

export default CategoryTags;
