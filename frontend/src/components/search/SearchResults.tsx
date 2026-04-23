import React, { useEffect } from "react";
import { motion } from "motion/react";
import { useSearchParams } from "react-router-dom";
import { useResearch } from "../../context/ResearchContext";
import ArticleRecommendations from "./ArticleRecommendations";
import ArticleSummaries from "./ArticleSummaries";
import { AlertCircle } from "lucide-react";
import LoadingAnimation from "../common/LoadingAnimation";

const SearchResults: React.FC = () => {
  const [searchParams] = useSearchParams();
  const {
    currentStep,
    recommendations,
    selectedArticles,
    summaries,
    researchQuery,
    isLoading,
    error,
    selectArticle,
    deselectArticle,
    getSummaries,
    nextStep,
    getRecommendations,
  } = useResearch();

  // Handle URL parameters for automatic search
  useEffect(() => {
    const query = searchParams.get('q');
    if (query && query !== researchQuery) {
      // Only trigger search if we're not already loading and don't have recommendations
      if (!isLoading && recommendations.length === 0) {
        getRecommendations(query);
      }
    }
  }, [searchParams, researchQuery, isLoading, recommendations.length, getRecommendations]);

  // Handle getting summaries
  const handleGetSummaries = async (articles: any[], query: string) => {
    try {
      await getSummaries(articles, query);
    } catch (err) {
      console.error('Error getting summaries:', err);
      // The error will be handled by the ResearchContext and displayed in the error state
    }
  };

  // Handle going back to recommendations
  const handleGoBack = () => {
    nextStep('recommendations');
  };

  // Render loading state
  if (isLoading) {
    const loadingMessage = currentStep === 'research-query' 
      ? 'Analizando tu consulta...' 
      : currentStep === 'recommendations' 
      ? 'Construyendo resúmenes...' 
      : 'Preparando respuestas fundamentadas...';
    
    return <LoadingAnimation message={loadingMessage} isFullScreen={false} />;
  }

  // Render error state
  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-base-100 via-base-200 to-base-100">
        <motion.div 
          className="alert alert-error max-w-md mx-auto"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <AlertCircle className="w-6 h-6" />
          <div>
            <h3 className="font-semibold">Ocurrió un error</h3>
            <p className="text-sm mt-1">{error}</p>
          </div>
        </motion.div>
      </div>
    );
  }

  // Render based on current step
  const renderCurrentStep = () => {
    switch (currentStep) {
      case 'recommendations':
        return (
          <ArticleRecommendations
            recommendations={recommendations}
            onSelectArticle={selectArticle}
            onDeselectArticle={deselectArticle}
            onGetSummaries={handleGetSummaries}
            selectedArticles={selectedArticles}
            researchQuery={researchQuery}
            isLoading={isLoading}
          />
        );

      case 'summaries':
      case 'chat': // Treat 'chat' same as 'summaries' - stay on summaries page
        if (!summaries) {
          // If no summaries but we're supposed to be on summaries page, 
          // stay on this page and let the chat show the error
          return (
            <div className="min-h-[60vh] flex items-center justify-center">
              <div className="alert alert-warning max-w-md">
                <AlertCircle className="w-6 h-6" />
                <div>
                  <h3 className="font-semibold">No hay resúmenes disponibles</h3>
                  <p className="text-sm mt-1">Selecciona artículos primero.</p>
                </div>
              </div>
            </div>
          );
        }
        return (
          <ArticleSummaries
            summaries={summaries}
            selectedArticles={selectedArticles}
            researchQuery={researchQuery}
            onGoBack={handleGoBack}
          />
        );

      default:
        return (
          <div className="text-center py-12">
            <motion.div 
              className="alert alert-info max-w-md mx-auto"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <AlertCircle className="w-6 h-6" />
              <div>
                <h3 className="font-semibold">No hay resultados</h3>
                <p className="text-sm mt-1">
                  Prueba buscando un tema, método o pregunta de investigación.
                </p>
              </div>
            </motion.div>
          </div>
        );
    }
  };

  return (
    <div className="bg-gradient-to-br from-base-100 via-base-200 to-base-100 min-h-screen">
      <div className="max-w-7xl mx-auto px-4 lg:px-6 py-8">
        {renderCurrentStep()}
      </div>
    </div>
  );
};

export default SearchResults;
