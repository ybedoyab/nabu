import React, { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import { apiService, type Article, type RecommendationResponse, type SummaryResponse, type ChatResponse, type SystemStatus, type SuggestedQuestion } from '../services/api';

// Types
export type ResearchStep = 'research-query' | 'recommendations' | 'summaries' | 'chat';

export interface ChatMessage {
  role: 'user' | 'assistant';
  message: string;
  timestamp?: Date;
}

export interface ResearchState {
  currentStep: ResearchStep;
  researchQuery: string;
  recommendations: Article[];
  selectedArticles: Article[];
  summaries: SummaryResponse | null;
  suggestedQuestions: SuggestedQuestion[];
  chatHistory: ChatMessage[];
  followUpQuestions: string[];
  systemStatus: SystemStatus | null;
  isLoading: boolean;
  error: string | null;
}

// Action Types
const ActionTypes = {
  SET_LOADING: 'SET_LOADING',
  SET_ERROR: 'SET_ERROR',
  SET_SYSTEM_STATUS: 'SET_SYSTEM_STATUS',
  
  SET_RESEARCH_QUERY: 'SET_RESEARCH_QUERY',
  
  SET_RECOMMENDATIONS: 'SET_RECOMMENDATIONS',
  SELECT_ARTICLE: 'SELECT_ARTICLE',
  DESELECT_ARTICLE: 'DESELECT_ARTICLE',
  CLEAR_SELECTIONS: 'CLEAR_SELECTIONS',
  
  SET_SUMMARIES: 'SET_SUMMARIES',
  SET_SUGGESTED_QUESTIONS: 'SET_SUGGESTED_QUESTIONS',
  
  ADD_CHAT_MESSAGE: 'ADD_CHAT_MESSAGE',
  SET_CHAT_HISTORY: 'SET_CHAT_HISTORY',
  SET_FOLLOW_UP_QUESTIONS: 'SET_FOLLOW_UP_QUESTIONS',
  
  NEXT_STEP: 'NEXT_STEP',
  RESET_RESEARCH: 'RESET_RESEARCH',
};

// Initial State
const initialState: ResearchState = {
  currentStep: 'research-query',
  researchQuery: '',
  recommendations: [],
  selectedArticles: [],
  summaries: null,
  suggestedQuestions: [],
  chatHistory: [],
  followUpQuestions: [],
  systemStatus: null,
  isLoading: false,
  error: null,
};

// Reducer
const researchReducer = (state: ResearchState, action: any): ResearchState => {
  switch (action.type) {
    case ActionTypes.SET_LOADING:
      return { ...state, isLoading: action.payload, error: null };
      
    case ActionTypes.SET_ERROR:
      return { ...state, isLoading: false, error: action.payload };
      
    case ActionTypes.SET_SYSTEM_STATUS:
      return { ...state, systemStatus: action.payload };
      
    case ActionTypes.SET_RESEARCH_QUERY:
      return { ...state, researchQuery: action.payload };
      
    case ActionTypes.SET_RECOMMENDATIONS:
      return { 
        ...state, 
        recommendations: action.payload,
        selectedArticles: [], // Clear previous selections
        summaries: null, // Clear previous summaries
        currentStep: 'recommendations',
        isLoading: false,
        error: null
      };
      
    case ActionTypes.SELECT_ARTICLE:
      const articleId = action.payload;
      const updatedRecommendations = state.recommendations.map(rec => 
        rec.id === articleId ? { ...rec, selected: true } : rec
      );
      const updatedSelectedArticles = [
        ...state.selectedArticles,
        ...state.recommendations.filter(rec => rec.id === articleId)
      ];
      
      return {
        ...state,
        recommendations: updatedRecommendations,
        selectedArticles: updatedSelectedArticles,
      };
      
    case ActionTypes.DESELECT_ARTICLE:
      const deselectedId = action.payload;
      const deselectedRecommendations = state.recommendations.map(rec => 
        rec.id === deselectedId ? { ...rec, selected: false } : rec
      );
      const deselectedArticles = state.selectedArticles.filter(rec => rec.id !== deselectedId);
      
      return {
        ...state,
        recommendations: deselectedRecommendations,
        selectedArticles: deselectedArticles,
      };
      
    case ActionTypes.CLEAR_SELECTIONS:
      const clearedRecommendations = state.recommendations.map(rec => ({ ...rec, selected: false }));
      return {
        ...state,
        recommendations: clearedRecommendations,
        selectedArticles: [],
      };
      
    case ActionTypes.SET_SUMMARIES:
      return { 
        ...state, 
        summaries: action.payload,
        currentStep: 'summaries',
        isLoading: false,
        error: null
      };
      
    case ActionTypes.SET_SUGGESTED_QUESTIONS:
      return { ...state, suggestedQuestions: action.payload };
      
    case ActionTypes.ADD_CHAT_MESSAGE:
      return {
        ...state,
        chatHistory: [...state.chatHistory, action.payload],
      };
      
    case ActionTypes.SET_CHAT_HISTORY:
      return { ...state, chatHistory: action.payload };
      
    case ActionTypes.SET_FOLLOW_UP_QUESTIONS:
      return { ...state, followUpQuestions: action.payload };
      
    case ActionTypes.NEXT_STEP:
      return { ...state, currentStep: action.payload };
      
    case ActionTypes.RESET_RESEARCH:
      return {
        ...initialState,
        systemStatus: state.systemStatus,
      };
      
    default:
      return state;
  }
};

// Context
const ResearchContext = createContext<ResearchState & {
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setResearchQuery: (query: string) => void;
  getRecommendations: (query: string, topK?: number) => Promise<RecommendationResponse>;
  selectArticle: (articleId: string) => void;
  deselectArticle: (articleId: string) => void;
  clearSelections: () => void;
  getSummaries: (selectedArticles: Article[], researchQuery: string) => Promise<SummaryResponse>;
  sendChatMessage: (userQuestion: string, selectedArticles: Article[], researchQuery: string, chatHistory: ChatMessage[]) => Promise<ChatResponse>;
  selectSuggestedQuestion: (question: string) => void;
  nextStep: (step: ResearchStep) => void;
  resetResearch: () => void;
} | null>(null);

// Provider component
export const ResearchProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(researchReducer, initialState);

  // Load system status on mount
  useEffect(() => {
    const loadSystemStatus = async () => {
      try {
        const status = await apiService.getStatus();
        dispatch({ type: ActionTypes.SET_SYSTEM_STATUS, payload: status });
      } catch (error) {
        console.error('Failed to load system status:', error);
      }
    };

    loadSystemStatus();
  }, []);

  // Action creators
  const actions = {
    setLoading: (loading: boolean) => dispatch({ type: ActionTypes.SET_LOADING, payload: loading }),
    setError: (error: string | null) => dispatch({ type: ActionTypes.SET_ERROR, payload: error }),
    
    setResearchQuery: (query: string) => dispatch({ type: ActionTypes.SET_RESEARCH_QUERY, payload: query }),
    
    getRecommendations: async (query: string, topK: number = 5) => {
      dispatch({ type: ActionTypes.SET_LOADING, payload: true });
      dispatch({ type: ActionTypes.SET_RESEARCH_QUERY, payload: query });
      try {
        const response = await apiService.getRecommendations(query, topK);
        dispatch({ type: ActionTypes.SET_RECOMMENDATIONS, payload: response.recommendations });
        return response;
      } catch (error: any) {
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        throw error;
      }
    },
    
    selectArticle: (articleId: string) => dispatch({ type: ActionTypes.SELECT_ARTICLE, payload: articleId }),
    deselectArticle: (articleId: string) => dispatch({ type: ActionTypes.DESELECT_ARTICLE, payload: articleId }),
    clearSelections: () => dispatch({ type: ActionTypes.CLEAR_SELECTIONS }),
    
    getSummaries: async (selectedArticles: Article[], researchQuery: string) => {
      if (!researchQuery || researchQuery.trim().length === 0) {
        const error = new Error('Research query is required');
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        throw error;
      }

      dispatch({ type: ActionTypes.SET_LOADING, payload: true });
      try {
        const response = await apiService.getSummaries(selectedArticles, researchQuery);
        console.log('getSummaries response:', response);
        dispatch({ type: ActionTypes.SET_SUMMARIES, payload: response });
        dispatch({ type: ActionTypes.SET_SUGGESTED_QUESTIONS, payload: response.suggested_questions });
        return response;
      } catch (error: any) {
        console.error('getSummaries error:', error);
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        throw error;
      }
    },
    
    sendChatMessage: async (userQuestion: string, selectedArticles: Article[], researchQuery: string, chatHistory: ChatMessage[]) => {
      try {
        const response = await apiService.chatWithArticles(
          userQuestion, 
          selectedArticles, 
          researchQuery, 
          chatHistory
        );
        
        dispatch({ type: ActionTypes.SET_CHAT_HISTORY, payload: response.chat_history });
        dispatch({ type: ActionTypes.SET_FOLLOW_UP_QUESTIONS, payload: response.follow_up_questions });
        dispatch({ type: ActionTypes.NEXT_STEP, payload: 'chat' });
        
        return response;
      } catch (error: any) {
        dispatch({ type: ActionTypes.SET_ERROR, payload: error.message });
        throw error;
      }
    },
    
    selectSuggestedQuestion: (question: string) => {
      dispatch({ type: ActionTypes.SET_RESEARCH_QUERY, payload: question });
    },
    
    nextStep: (step: ResearchStep) => dispatch({ type: ActionTypes.NEXT_STEP, payload: step }),
    resetResearch: () => dispatch({ type: ActionTypes.RESET_RESEARCH }),
  };


  const value = {
    ...state,
    ...actions,
  };

  return (
    <ResearchContext.Provider value={value}>
      {children}
    </ResearchContext.Provider>
  );
};

// Hook to use the context
export const useResearch = () => {
  const context = useContext(ResearchContext);
  if (!context) {
    throw new Error('useResearch must be used within a ResearchProvider');
  }
  return context;
};
