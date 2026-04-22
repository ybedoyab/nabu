import axios from 'axios';
export {
  handleApiError,
  createLoadingState,
  setLoading,
  setSuccess,
  setError,
} from "./stateUtils";

// AI API Configuration
const AI_API_BASE_URL = import.meta.env.VITE_APP_AI_API_BASE_URL || 'http://localhost:8000';
const AI_API_VERSION = import.meta.env.VITE_APP_AI_API_VERSION || 'v1';

// Data API Configuration
const DATA_API_BASE_URL = import.meta.env.VITE_APP_DATA_API_BASE_URL || 'http://localhost:8081';

// Use relative URL in development (with proxy) or full URL in production
const aiBaseURL = import.meta.env.DEV 
  ? `/api/${AI_API_VERSION}` 
  : `${AI_API_BASE_URL}/api/${AI_API_VERSION}`;

const dataBaseURL = import.meta.env.DEV 
  ? `/data-api` 
  : DATA_API_BASE_URL;

// Create axios instances
const aiApi = axios.create({
  baseURL: aiBaseURL,
  timeout: 120000, // 2 minutes timeout for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
});

const dataApi = axios.create({
  baseURL: dataBaseURL,
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptors
aiApi.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

dataApi.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptors
aiApi.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

dataApi.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Types for API responses
export interface Article {
  id: string;
  title: string;
  relevance_score: number;
  relevance_reasons: string[];
  research_applications: string[];
  url: string;
  organisms: string[];
  key_concepts: string[];
  selected?: boolean;
}

export interface RecommendationResponse {
  recommendations: Article[];
}

export interface SuggestedQuestion {
  id: string;
  question: string;
  type: string;
  focus: string;
  article_id: string;
  article_title: string;
}

export interface ArticleSummary {
  article_id: string;
  summary: string;
}

export interface SummaryResponse {
  status: string;
  step: string;
  research_query: string;
  article_summaries: ArticleSummary[];
  suggested_questions: SuggestedQuestion[];
  combined_summary?: string; // Optional since API might not return this
}

export interface ChatResponse {
  response: string;
  chat_history: Array<{
    role: 'user' | 'assistant';
    message: string;
  }>;
  follow_up_questions: string[];
}

export interface SystemStatus {
  status: string;
  message: string;
  articles_count: number;
  last_updated: string;
}

export interface QueryImageItem {
  study_id: string;
  passage_anchor?: string;
  summary?: string;
  image_url: string;
  caption?: string;
  source_url?: string;
}

export interface QueryImagesResponse {
  status: string;
  research_query: string;
  count: number;
  images: QueryImageItem[];
  timestamp: number;
}

// API Service Functions
export const apiService = {
  // AI API - Health and Status
  async getHealth() {
    const response = await aiApi.get('/health');
    return response.data;
  },

  async getStatus(): Promise<SystemStatus> {
    const response = await aiApi.get('/research/status');
    return response.data;
  },

  async getArticlesList(limit = 10) {
    const response = await aiApi.get(`/research/articles?limit=${limit}`);
    return response.data;
  },

  // AI API - Research Flow - Step 1: Get Recommendations
  async getRecommendations(researchQuery: string, topK: number = 5): Promise<RecommendationResponse> {
    const response = await aiApi.post('/research/recommendations', {
      research_query: researchQuery,
      top_k: topK,
    });
    return response.data;
  },

  // AI API - Research Flow - Step 2: Get Summaries and Questions
  async getSummaries(selectedArticles: Article[], researchQuery: string): Promise<SummaryResponse> {
    const response = await aiApi.post('/research/summaries', {
      selected_articles: selectedArticles,
      research_query: researchQuery,
    });
    return response.data;
  },

  // AI API - Research Flow - Step 3: Chat with Articles
  async chatWithArticles(
    userQuestion: string,
    selectedArticles: Article[],
    researchQuery: string,
    chatHistory: Array<{ role: 'user' | 'assistant'; message: string }> = []
  ): Promise<ChatResponse> {
    const response = await aiApi.post('/research/chat', {
      user_question: userQuestion,
      selected_articles: selectedArticles,
      research_query: researchQuery,
      chat_history: chatHistory,
    });
    return response.data;
  },

  // Stats - Query-relevant images (usa backend Data local)
  async getQueryImages(researchQuery: string, articleUrls?: string[]): Promise<QueryImagesResponse> {
    console.log('[API] getQueryImages called with:', { researchQuery, articleUrls });
    const payload: any = { research_query: researchQuery };
    if (articleUrls && articleUrls.length > 0) payload.article_urls = articleUrls;
    console.log('[API] Sending POST to /api/v1/stats/query-images with payload:', payload);
    const response = await dataApi.post('/api/v1/stats/query-images', payload);
    console.log('[API] getQueryImages response:', response.data);
    return response.data;
  },
};

// Export both API instances
export { aiApi, dataApi };
export default { aiApi, dataApi };
