import { motion } from 'motion/react';
import { useNavigate } from 'react-router-dom';

const CategoryTags = () => {
  const navigate = useNavigate();

  // Mapeo de categorías a términos de búsqueda específicos
  const categoryMap = {
    'LLMs': 'large language models transformers reasoning benchmark',
    'Computer Vision': 'computer vision object detection segmentation multimodal',
    'Robotics': 'robot learning manipulation policy planning reinforcement learning',
    'Healthcare AI': 'medical imaging clinical NLP diagnostic AI',
    'MLOps': 'model deployment observability evaluation drift monitoring',
    'NLP': 'retrieval augmented generation information extraction summarization',
    'Surveys': 'systematic review survey state of the art machine learning'
  };

  const categories = Object.keys(categoryMap);

  const handleCategoryClick = (category: string) => {
    const searchQuery = categoryMap[category as keyof typeof categoryMap];
    navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
  };

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
          onClick={() => handleCategoryClick(category)}
        >
          {category}
        </motion.button>
      ))}
    </div>
  );
};

export default CategoryTags;