import axios from 'axios';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://angella-ungarmented-balefully.ngrok-free.dev';
const API_VERSION = import.meta.env.VITE_API_VERSION || 'v1';

// Use relative URL in development (with proxy) or full URL in production
const baseURL = import.meta.env.DEV 
  ? `/api/${API_VERSION}` 
  : `${API_BASE_URL}/api/${API_VERSION}`;

// Create axios instance
const api = axios.create({
  baseURL,
  timeout: 120000, // 2 minutes timeout for AI operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Instancia separada para Data backend (localhost:8000)
const api2 = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
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
  source?: string;
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
  status?: string;
  step?: string;
  research_query?: string;
  chat_history: Array<{
    id?: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp?: number;
    follow_up_questions?: Array<{ question: string; type?: string }>;
  }>;
  follow_up_questions: Array<{ id?: string; question: string; type?: string }>;
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

interface MockResearchData {
  system_status: SystemStatus;
  recommendations: Article[];
  summary: SummaryResponse;
  chat: {
    response: string;
    follow_up_questions: string[];
  };
}

let mockResearchDataPromise: Promise<MockResearchData> | null = null;

const shouldForceMockData = () => {
  if (typeof window === 'undefined') return false;
  return new URLSearchParams(window.location.search).get('mock') === '1';
};

const getMockResearchData = async (): Promise<MockResearchData> => {
  if (!mockResearchDataPromise) {
    mockResearchDataPromise = fetch('/mock-research.json').then(async (response) => {
      if (!response.ok) {
        throw new Error('No se pudo cargar mock-research.json');
      }
      return response.json();
    });
  }

  return mockResearchDataPromise;
};

const buildMockSummary = async (selectedArticles: Article[], researchQuery: string): Promise<SummaryResponse> => {
  const mockData = await getMockResearchData();
  const fallbackArticles = selectedArticles.length > 0
    ? selectedArticles
    : mockData.recommendations.slice(0, 3);

  return {
    ...mockData.summary,
    research_query: researchQuery,
    article_summaries: mockData.summary.article_summaries.filter((summary) =>
      fallbackArticles.some((article) => article.id === summary.article_id)
    ),
    suggested_questions: mockData.summary.suggested_questions.filter((question) =>
      fallbackArticles.some((article) => article.id === question.article_id)
    ),
  };
};

const buildMockChatResponse = async (
  userQuestion: string,
  chatHistory: Array<{ role: 'user' | 'assistant'; content: string }> = []
): Promise<ChatResponse> => {
  const mockData = await getMockResearchData();
  const assistantMessage = `${mockData.chat.response}\n\nPregunta actual: ${userQuestion}`;

  return {
    status: 'success',
    step: 'chat',
    chat_history: [
      ...chatHistory,
      { role: 'user', content: userQuestion },
      { role: 'assistant', content: assistantMessage },
    ],
    follow_up_questions: mockData.chat.follow_up_questions.map(q => ({ question: q })),
  };
};

// API Service Functions
export const apiService = {
  // Health and Status
  async getHealth() {
    const response = await api.get('/health', { baseURL: import.meta.env.DEV ? undefined : API_BASE_URL });
    return response.data;
  },

  async getStatus(): Promise<SystemStatus> {
    if (shouldForceMockData()) {
      const mockData = await getMockResearchData();
      return mockData.system_status;
    }

    const response = await api.get('/research/status');
    return response.data;
  },

  async getArticlesList(limit = 10) {
    const response = await api.get(`/research/articles?limit=${limit}`);
    return response.data;
  },

  // Research Flow - Step 1: Get Recommendations
  async getRecommendations(researchQuery: string, topK: number = 10): Promise<RecommendationResponse> {
    if (shouldForceMockData()) {
      const mockData = await getMockResearchData();
      return {
        recommendations: mockData.recommendations.slice(0, topK).map((article) => ({
          ...article,
          selected: false,
        })),
      };
    }

    const response = await api.post('/research/recommendations', {
      research_query: researchQuery,
      top_k: topK,
    });
    return response.data;
  },

  // Research Flow - Step 2: Get Summaries and Questions
  async getSummaries(selectedArticles: Article[], researchQuery: string): Promise<SummaryResponse> {
    if (shouldForceMockData()) {
      return buildMockSummary(selectedArticles, researchQuery);
    }

    const response = await api.post('/research/summaries', {
      selected_articles: selectedArticles,
      research_query: researchQuery,
    });
    return response.data;
  },

  // Research Flow - Step 3: Chat with Articles
  async chatWithArticles(
    userQuestion: string,
    selectedArticles: Article[],
    researchQuery: string,
    chatHistory: Array<{ role: 'user' | 'assistant'; content: string }> = []
  ): Promise<ChatResponse> {
    if (shouldForceMockData()) {
      return buildMockChatResponse(userQuestion, chatHistory);
    }

    const response = await api.post('/research/chat', {
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
    const response = await api2.post('/api/v1/stats/query-images', payload);
    console.log('[API] getQueryImages response:', response.data);
    return response.data;
  },
};

// Error handling utility
export const handleApiError = (error: any): string => {
  if (error.response) {
    // Server responded with error status
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return `Bad Request: ${data.message || 'Invalid input'}`;
      case 404:
        return 'API endpoint not found';
      case 500:
        return `Server Error: ${data.message || 'Internal server error'}`;
      case 503:
        return `Service Unavailable: ${data.message || 'AI service not ready'}`;
      default:
        return `API Error (${status}): ${data.message || 'Unknown error'}`;
    }
  } else if (error.request) {
    // Network error
    return 'Network Error: Unable to connect to the server. Please check your connection.';
  } else {
    // Other error
    return `Error: ${error.message}`;
  }
};

// Loading states utility
export const createLoadingState = () => ({
  isLoading: false,
  error: null,
  data: null,
});

export const setLoading = (state: any) => ({
  ...state,
  isLoading: true,
  error: null,
});

export const setSuccess = (state: any, data: any) => ({
  ...state,
  isLoading: false,
  error: null,
  data,
});

export const setError = (state: any, error: any) => ({
  ...state,
  isLoading: false,
  error,
  data: null,
});

export default api;
