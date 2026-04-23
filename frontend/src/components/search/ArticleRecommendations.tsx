import React from 'react';
import { motion } from 'motion/react';
import { ExternalLink, CheckCircle, Circle, Star, Users, Tag, FileText } from 'lucide-react';
import { type Article } from '../../services/api';

interface ArticleRecommendationsProps {
  recommendations: Article[];
  onSelectArticle: (articleId: string) => void;
  onDeselectArticle: (articleId: string) => void;
  onGetSummaries: (articles: Article[], query: string) => void;
  selectedArticles: Article[];
  researchQuery: string;
  isLoading: boolean;
}

const ArticleRecommendations: React.FC<ArticleRecommendationsProps> = ({ 
  recommendations, 
  onSelectArticle, 
  onDeselectArticle, 
  onGetSummaries,
  selectedArticles,
  researchQuery,
  isLoading 
}) => {
  const [sourceFilter, setSourceFilter] = React.useState<'all' | 'arxiv' | 'scholar'>('all');

  const normalizeSource = (source?: string, url?: string) => {
    const src = (source || '').toLowerCase();
    if (src.includes('arxiv')) return 'arxiv';
    if (src.includes('scholar') || src.includes('google')) return 'scholar';
    const link = (url || '').toLowerCase();
    if (link.includes('arxiv.org')) return 'arxiv';
    if (link.includes('scholar.google')) return 'scholar';
    return 'unknown';
  };

  const sourceLabel = (source?: string, url?: string) => {
    const normalized = normalizeSource(source, url);
    if (normalized === 'arxiv') return 'arXiv';
    if (normalized === 'scholar') return 'Google Scholar';
    return 'Otra fuente';
  };

  const sourceCounts = recommendations.reduce(
    (acc, article) => {
      const source = normalizeSource(article.source, article.url);
      if (source === 'arxiv') acc.arxiv += 1;
      if (source === 'scholar') acc.scholar += 1;
      return acc;
    },
    { arxiv: 0, scholar: 0 }
  );

  const visibleRecommendations = recommendations.filter((article) => {
    if (sourceFilter === 'all') return true;
    return normalizeSource(article.source, article.url) === sourceFilter;
  });

  const handleArticleToggle = (article: Article) => {
    if (article.selected) {
      onDeselectArticle(article.id);
    } else {
      onSelectArticle(article.id);
    }
  };

  const handleContinue = () => {
    if (selectedArticles.length > 0) {
      onGetSummaries(selectedArticles, researchQuery);
    }
  };

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="text-center py-12">
        <motion.div 
          className="alert alert-info max-w-md mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <FileText className="w-6 h-6" />
          <div className="text-base-content">
            <h3 className="font-semibold">No hay recomendaciones disponibles</h3>
            <p className="text-sm mt-1">
              Prueba con palabras clave más amplias, un método o una pregunta más específica.
            </p>
          </div>
        </motion.div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-base-content mb-4 font-geist">
          Artículos relevantes
        </h2>
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <p className="text-base-content/70">
            Selecciona los artículos que quieres resumir, comparar y usar como base para el siguiente paso.
          </p>
          <div className="join">
            <button
              type="button"
              className={`btn btn-sm join-item ${sourceFilter === 'all' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setSourceFilter('all')}
            >
              Todos ({recommendations.length})
            </button>
            <button
              type="button"
              className={`btn btn-sm join-item ${sourceFilter === 'arxiv' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setSourceFilter('arxiv')}
            >
              arXiv ({sourceCounts.arxiv})
            </button>
            <button
              type="button"
              className={`btn btn-sm join-item ${sourceFilter === 'scholar' ? 'btn-primary' : 'btn-outline'}`}
              onClick={() => setSourceFilter('scholar')}
            >
              Google Scholar ({sourceCounts.scholar})
            </button>
          </div>
        </div>
      </div>


      {/* Articles Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {visibleRecommendations.map((article, index) => (
          <motion.div
            key={article.id}
            className={`card shadow-lg border-2 transition-all duration-300 cursor-pointer ${
              article.selected 
                ? 'border-primary bg-primary/5 shadow-primary/20' 
                : 'border-base-300 hover:border-primary/50 hover:shadow-xl'
            }`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            onClick={() => handleArticleToggle(article)}
          >
            <div className="card-body p-6">
              {/* Article Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  {/* Article Number */}
                  <div className="badge badge-primary badge-lg font-bold">
                    {index + 1}
                  </div>
                  
                  {/* Selection Indicator */}
                  <div className="flex items-center space-x-2">
                    {article.selected ? (
                      <CheckCircle className="w-5 h-5 text-success" />
                    ) : (
                      <Circle className="w-5 h-5 text-base-content/40" />
                    )}
                    <span className="text-sm font-medium text-base-content/70">
                      {article.selected ? 'Seleccionado' : 'Haz clic para seleccionar'}
                    </span>
                  </div>
                </div>
                
                {/* Relevance Score */}
                <div className="flex items-center space-x-1">
                  <Star className="w-4 h-4 text-warning fill-current" />
                  <span className="text-sm font-semibold text-base-content">
                    {article.relevance_score}/10
                  </span>
                </div>
              </div>

              {/* Article Title */}
              <h3 className="card-title text-lg font-semibold text-base-content mb-3 line-clamp-2">
                {article.title}
              </h3>
              <div className="mb-3">
                <span className="badge badge-outline badge-sm">{sourceLabel(article.source, article.url)}</span>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-medium text-base-content mb-2">Aplicaciones potenciales:</h4>
                <div className="flex flex-wrap gap-2">
                  {article.research_applications.slice(0, 3).map((app, index) => (
                    <span
                      key={index}
                      className="badge badge-outline badge-sm"
                    >
                      {app}
                    </span>
                  ))}
                </div>
              </div>

              <div className="flex items-center gap-4 mb-3 text-sm text-base-content/70">
                {article.organisms.length > 0 && (
                  <div className="flex items-center gap-1">
                    <Users className="w-4 h-4" />
                    <span>Contexto: {article.organisms.slice(0, 2).join(', ')}</span>
                  </div>
                )}
                
                {article.key_concepts.length > 0 && (
                  <div className="flex items-center gap-1">
                    <Tag className="w-4 h-4" />
                    <span>{article.key_concepts.slice(0, 2).join(', ')}</span>
                  </div>
                )}
              </div>

              {/* Relevance Reasons */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-primary mb-2">Por qué coincide con tu búsqueda:</h4>
                <div className="flex flex-wrap gap-2">
                  {article.relevance_reasons.slice(0, 3).map((reason, reasonIndex) => (
                    <span 
                      key={reasonIndex}
                      className="badge badge-outline badge-primary badge-sm"
                    >
                      {reason}
                    </span>
                  ))}
                  {article.relevance_reasons.length > 3 && (
                    <span className="badge badge-outline badge-ghost badge-sm">
                      +{article.relevance_reasons.length - 3} más
                    </span>
                  )}
                </div>
              </div>

              <div className="card-actions justify-end">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="btn btn-ghost btn-sm"
                >
                  <ExternalLink className="w-4 h-4" />
                  Abrir artículo
                </a>
              </div>
            </div>
          </motion.div>
        ))}
      </div>

      {/* Continue Button */}
      <div className="flex justify-center">
        <button
          onClick={handleContinue}
          disabled={selectedArticles.length === 0 || isLoading}
          className="btn btn-primary btn-lg"
        >
          {isLoading ? (
            <>
              <span className="loading loading-spinner loading-sm"></span>
              Preparando resumen...
            </>
          ) : (
            `Continuar con ${selectedArticles.length} artículo${selectedArticles.length !== 1 ? 's' : ''}`
          )}
        </button>
      </div>
    </div>
  );
};

export default ArticleRecommendations;
