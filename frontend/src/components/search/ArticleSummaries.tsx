import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { FileText, MessageCircle, ArrowLeft, Lightbulb, Users, ChevronDown, X } from 'lucide-react';
import { type SummaryResponse, type Article, apiService } from '../../services/api';
import ChatInterface from './ChatInterface';

// Minimalist parser for markdown-like text
const parseMarkdownText = (text: string) => {
  if (!text) return null;

  // Remove all ** markers for bold text
  const cleanText = text.replace(/\*\*/g, '');

  // Split by numbered sections
  const sections = cleanText.split(/(?=\d+\.\s+[A-Z])/);
  
  return sections.map((section, index) => {
    if (!section.trim()) return null;

    // Check if this is a numbered section (e.g., "1. Key Findings:")
    const isNumberedSection = /^\d+\.\s+/.test(section.trim());
    
    if (isNumberedSection) {
      const match = section.match(/^(\d+)\.\s+([^:]+):\s*/);
      if (match) {
        const [fullMatch, sectionNum, title] = match;
        const content = section.replace(fullMatch, '').trim();
        
        // Split content by sentences/lines for better display
        const lines = content
          .split(/\n+/)
          .map(line => line.trim())
          .filter(line => line.length > 0);
        
        return (
          <div key={index} className="mb-4">
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-sm font-bold text-primary">{sectionNum}.</span>
              <h4 className="text-base font-semibold text-base-content">
                {title}
              </h4>
            </div>
            <div className="space-y-2 pl-5">
              {lines.map((line, lineIndex) => (
                <p key={lineIndex} className="text-sm text-base-content/70 leading-relaxed">
                  {line}
                </p>
              ))}
            </div>
          </div>
        );
      }
    }
    
    // Handle non-numbered sections (like "Article Summary:")
    const headerMatch = section.match(/^([^:]+):\s*/);
    if (headerMatch && !isNumberedSection) {
      const [fullMatch, header] = headerMatch;
      const content = section.replace(fullMatch, '').trim();
      
      return (
        <div key={index} className="mb-4">
          <h4 className="text-base font-semibold text-primary mb-2">
            {header}
          </h4>
          {content && (
            <p className="text-sm text-base-content/70 leading-relaxed pl-5">
              {content}
            </p>
          )}
        </div>
      );
    }
    
    return (
      <div key={index} className="mb-3">
        <p className="text-sm text-base-content/70 leading-relaxed">{section.trim()}</p>
      </div>
    );
  }).filter(Boolean);
};

interface ArticleSummariesProps {
  summaries: SummaryResponse;
  selectedArticles: Article[];
  researchQuery: string;
  onGoBack: () => void;
}

const ArticleSummaries: React.FC<ArticleSummariesProps> = ({
  summaries,
  selectedArticles,
  researchQuery,
  onGoBack,
}) => {
  const [openAccordion, setOpenAccordion] = useState<string | null>(
    summaries.article_summaries?.[0]?.article_id || null
  );
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<string | null>(null);
  
  // Estados para imágenes
  type RelatedImage = { image_url: string; source_url?: string; caption?: string };
  const [relatedImages, setRelatedImages] = useState<RelatedImage[]>([]);
  const [imagesLoading, setImagesLoading] = useState(false);
  const [imagesError, setImagesError] = useState<string | null>(null);

  const toggleAccordion = (articleId: string) => {
    setOpenAccordion(openAccordion === articleId ? null : articleId);
  };

  // Cargar imágenes relacionadas
  useEffect(() => {
    console.log('🔥🔥🔥 [ArticleSummaries] useEffect TRIGGERED - researchQuery:', researchQuery);
    let cancelled = false;
    const loadImages = async () => {
      if (!researchQuery) {
        console.log('❌ [ArticleSummaries] No researchQuery');
        return;
      }
      if (!selectedArticles || selectedArticles.length === 0) {
        console.log('❌ [ArticleSummaries] No selectedArticles');
        return;
      }
      
      console.log('✅ [ArticleSummaries] Loading images...');
      setImagesLoading(true);
      setImagesError(null);
      
      try {
        const urls = selectedArticles.map(a => a?.url).filter(Boolean) as string[];
        console.log('📋 [ArticleSummaries] Article URLs:', urls);
        
        if (urls.length === 0) {
          console.log('⚠️ [ArticleSummaries] No valid URLs');
          setImagesError('No hay URLs de artículos disponibles');
          return;
        }
        
        console.log('🚀 [ArticleSummaries] Calling apiService.getQueryImages...');
        const response = await apiService.getQueryImages(researchQuery, urls);
        console.log('📦 [ArticleSummaries] Response:', response);
        console.log('📦 [ArticleSummaries] Response.images:', response.images);
        console.log('📦 [ArticleSummaries] Response.count:', response.count);
        
        if (!cancelled) {
          const images = response.images || [];
          setRelatedImages(images);
          console.log('✅ [ArticleSummaries] Images set:', images.length, images);
        }
      } catch (e: any) {
        console.error('❌ [ArticleSummaries] Error loading images:', e);
        if (!cancelled) setImagesError('No se pudieron cargar las imágenes.');
      } finally {
        if (!cancelled) setImagesLoading(false);
      }
    };
    
    loadImages();
    return () => { cancelled = true; };
  }, [researchQuery, selectedArticles]);

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <motion.div 
        className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div>
          <h2 className="text-3xl font-bold text-primary mb-2">
            Resumen de investigación
          </h2>
          <p className="text-lg text-base-content/70">
            Basado en {selectedArticles.length} artículo{selectedArticles.length > 1 ? 's' : ''} seleccionado{selectedArticles.length > 1 ? 's' : ''}
          </p>
        </div>
        <button 
          className="btn btn-ghost gap-2"
          onClick={onGoBack}
        >
          <ArrowLeft className="w-4 h-4" />
          Volver a artículos
        </button>
      </motion.div>
      
      {/* Floating Chat Toggle Button */}
      <button
        type="button"
        aria-label="Abrir chat"
        onClick={() => setIsChatOpen(true)}
        className="fixed bottom-6 right-6 btn btn-primary btn-circle shadow-xl z-40"
      >
        <MessageCircle className="w-5 h-5" />
      </button>

      {/* Floating Chat Panel */}
      {isChatOpen && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 20 }}
          transition={{ duration: 0.2 }}
          className="fixed bottom-24 right-6 z-50 w-[90vw] max-w-[440px] h-[70vh] bg-base-100 border border-base-300 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
        >
          {/* Chat Header */}
          <div className="flex items-center justify-between px-4 py-2 border-b border-base-300 bg-base-200/60">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium">Chat IA</span>
            </div>
            <button
              type="button"
              aria-label="Cerrar chat"
              onClick={() => setIsChatOpen(false)}
              className="btn btn-ghost btn-xs"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Chat Body */}
          <div className="flex-1 min-h-0">
            <ChatInterface 
              selectedArticles={selectedArticles} 
              researchQuery={researchQuery}
              initialQuestion={selectedQuestion}
              onQuestionSent={() => setSelectedQuestion(null)}
            />
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Summary */}
        <motion.div 
          className="lg:col-span-2"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          <div className="card shadow-xl border-2 border-primary/20 bg-gradient-to-br from-base-100 to-base-200/30">
            <div className="card-body p-6 lg:p-8">
              {/* Header */}
              <div className="flex items-center gap-3 mb-6 pb-6 border-b-2 border-base-300">
                <div className="p-3 bg-gradient-to-br from-primary to-primary/70 rounded-xl shadow-lg">
                  <FileText className="w-6 h-6 text-primary-content" />
                </div>
                <div className="flex-1">
                  <h3 className="text-2xl font-bold text-primary">Respuesta sintetizada</h3>
                  <p className="text-sm text-base-content/60 mt-1">Consulta: {researchQuery}</p>
                </div>
              </div>
              
              {/* Summary Content */}
              <div className="max-w-none">
                {summaries.combined_summary ? (
                  <div className="space-y-4">
                    {parseMarkdownText(summaries.combined_summary)}
                  </div>
                ) : summaries.article_summaries && summaries.article_summaries.length > 0 ? (
                  <div className="space-y-6">
                    {summaries.article_summaries.map((summary, index) => (
                        <div key={index} className="space-y-4">
                          <div className="flex items-center gap-3 mb-4 p-3 bg-primary/5 rounded-lg border-l-4 border-primary">
                          <div className="badge badge-primary badge-lg">Artículo {index + 1}</div>
                          
                          <h4 className="text-base font-semibold text-primary flex-1">
                            {selectedArticles[index]?.title}
                          </h4>
                        </div>
                        {parseMarkdownText(summary.summary)}
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="alert alert-info">
                    <Lightbulb className="w-5 h-5" />
                    <span>No hay resumen disponible para los artículos seleccionados.</span>
                  </div>
                )}
              </div>

              {/* Related Images Section */}
              <div className="divider my-8"></div>
              <div className="mb-8">
                <h4 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Figuras y visuales relacionados
                </h4>
                
                {imagesLoading ? (
                  <div className="flex items-center justify-center gap-3 py-12 text-base-content/60">
                    <span className="loading loading-spinner loading-lg" />
                    <span className="text-sm">Cargando imágenes...</span>
                  </div>
                ) : imagesError ? (
                  <div className="alert alert-warning">
                    <span className="text-sm">{imagesError}</span>
                  </div>
                ) : relatedImages.length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {relatedImages.map((img, idx) => (
                      <a 
                        key={idx} 
                        href={img.image_url} 
                        target="_blank" 
                        rel="noreferrer" 
                        className="block group relative overflow-hidden rounded-lg border-2 border-base-300 hover:border-primary/50 transition-all shadow-md hover:shadow-xl"
                        title={img.caption || 'Ver imagen completa'}
                      >
                        <img 
                          src={img.image_url} 
                          alt={img.caption || 'Figura de investigación'} 
                          className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-300" 
                          onError={(e) => {
                            console.error('Image failed to load:', img.image_url);
                            e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="100" height="100"%3E%3Crect fill="%23ddd" width="100" height="100"/%3E%3Ctext x="50%25" y="50%25" text-anchor="middle" dy=".3em" fill="%23999"%3ENo image%3C/text%3E%3C/svg%3E';
                          }}
                        />
                        {img.caption && (
                          <div className="absolute bottom-0 left-0 right-0 bg-base-100/95 backdrop-blur-sm p-2 border-t border-base-300">
                            <p className="text-xs text-base-content/80 line-clamp-2">{img.caption}</p>
                          </div>
                        )}
                      </a>
                    ))}
                  </div>
                ) : (
                  <div className="alert alert-info">
                  <Lightbulb className="w-5 h-5" />
                  <span className="text-sm">No se encontraron visuales relacionados para los artículos seleccionados.</span>
                </div>
              )}
              </div>

              {/* Selected Articles Reference */}
              <div className="divider my-8"></div>
              <div>
                <h4 className="text-lg font-semibold text-primary mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Basado en estos artículos:
                </h4>
                <div className="grid grid-cols-1 gap-3">
                  {selectedArticles.map((article, index) => (
                    <motion.div 
                      key={article.id} 
                      className="flex items-center gap-3 p-4 bg-base-200/50 rounded-lg border border-base-300 hover:border-primary/30 hover:bg-base-200 transition-all"
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                    >
                      <div className="badge badge-primary badge-lg">{index + 1}</div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-sm truncate">{article.title}</p>
                        <div className="flex flex-wrap items-center gap-2 mt-1">
                          <span className="text-xs text-base-content/60">
                            Relevancia: {article.relevance_score}/10
                          </span>
                          {article.organisms.length > 0 && (
                            <>
                              <span className="text-xs text-base-content/40">•</span>
                              <span className="text-xs text-base-content/60">
                                {article.organisms.join(', ')}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Individual Summaries */}
          <motion.div 
            className="card shadow-lg border-2 border-primary/20 bg-base-100"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <div className="card-body p-6">
              <h3 className="card-title text-lg text-primary mb-4 flex items-center gap-2">
                <Users className="w-5 h-5" />
                Notas por artículo
              </h3>
              
              <div className="space-y-3">
                {summaries.article_summaries && summaries.article_summaries.length > 0 ? (
                  summaries.article_summaries.map((summary, index) => {
                    const article = selectedArticles.find(a => a.id === summary.article_id);
                    const isOpen = openAccordion === summary.article_id;
                    
                    return (
                      <div key={summary.article_id} className="border-2 border-base-300 rounded-lg overflow-hidden bg-base-100 hover:border-primary/30 transition-colors">
                        <button
                          className="w-full p-4 text-left flex items-center justify-between hover:bg-base-200 transition-colors group"
                          onClick={() => toggleAccordion(summary.article_id)}
                        >
                          <span className="text-sm font-semibold flex-1 pr-2 group-hover:text-primary transition-colors">
                            {article?.title || `Artículo ${index + 1}`}
                          </span>
                          <div className={`transition-transform duration-300 ${isOpen ? 'rotate-180' : ''}`}>
                            <ChevronDown className="w-4 h-4 text-primary" />
                          </div>
                        </button>
                        {isOpen && (
                          <motion.div 
                            className="border-t-2 border-base-300 bg-base-50"
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            transition={{ duration: 0.3 }}
                          >
                            <div className="p-4 text-sm">
                              {parseMarkdownText(summary.summary)}
                            </div>
                          </motion.div>
                        )}
                      </div>
                    );
                  })
                ) : (
                  <p className="text-sm text-base-content/60 text-center py-4">No hay resúmenes individuales disponibles.</p>
                )}
              </div>
            </div>
          </motion.div>

          {/* Suggested Questions */}
          <motion.div 
            className="card shadow-lg border-2 border-primary/20 bg-gradient-to-br from-info/5 to-base-100"
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <div className="card-body p-6">
              <h3 className="card-title text-lg text-primary mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5" />
                Preguntas sugeridas
              </h3>
              
              <div className="space-y-2">
                {summaries.suggested_questions && summaries.suggested_questions.length > 0 ? (
                  summaries.suggested_questions.map((questionObj, index) => (
                    <motion.button
                      key={questionObj.id || index}
                      className="btn btn-sm w-full justify-start text-left h-auto py-3 px-4 hover:bg-primary/10 hover:border-primary/40 border-2 border-base-300 bg-base-100"
                      onClick={() => {
                        setSelectedQuestion(questionObj.question);
                        setIsChatOpen(true);
                      }}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={{ x: 5 }}
                    >
                      <span className="text-sm">{questionObj.question}</span>
                    </motion.button>
                  ))
                ) : (
                  <p className="text-sm text-base-content/60 text-center py-4">No hay preguntas sugeridas disponibles.</p>
                )}
              </div>
            </div>
          </motion.div>
        </div>
      </div>

      {/* Help Text */}
      <motion.div 
        className="text-center mt-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.5 }}
      >
        <div className="alert alert-info shadow-lg max-w-2xl mx-auto border-2 border-info/30">
          <Lightbulb className="w-5 h-5" />
          <div>
            <h4 className="font-semibold">¿Qué sigue?</h4>
            <p className="text-sm">
              Haz preguntas de seguimiento, explora las sugerencias o sigue refinando la literatura hasta decidir qué leer después.
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

export default ArticleSummaries;
