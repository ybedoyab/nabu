import React, { useEffect, useRef, useState } from 'react';
import { Send, MessageCircle, AlertCircle } from 'lucide-react';
import { type Article } from '../../services/api';
import { useResearch } from '../../context/ResearchContext';

interface LocalMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: number;
  follow_up_questions?: { question: string }[];
  isPending?: boolean;
}

interface ChatInterfaceProps {
  selectedArticles: Article[];
  researchQuery: string;
  initialQuestion?: string | null;
  onQuestionSent?: () => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ 
  selectedArticles, 
  researchQuery,
  initialQuestion,
  onQuestionSent 
}) => {
  const { chatHistory, sendChatMessage, isLoading } = useResearch();
  const [message, setMessage] = useState('');
  const [localError, setLocalError] = useState<string | null>(null);
  const [localMessages, setLocalMessages] = useState<LocalMessage[]>([]);
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const previousQueryRef = useRef<string>(researchQuery);
  const lastChatHistoryLengthRef = useRef<number>(0);
  const initialQuestionProcessedRef = useRef<boolean>(false);

  // Sync with chatHistory from context
  useEffect(() => {
    if (previousQueryRef.current !== researchQuery) {
      // New search - clear everything
      setLocalMessages([]);
      setIsWaitingForResponse(false);
      previousQueryRef.current = researchQuery;
      setLocalError(null);
      lastChatHistoryLengthRef.current = 0;
      initialQuestionProcessedRef.current = false;
      return;
    }

    // Solo actualizar si hay nuevos mensajes en chatHistory
    const contextMessages = chatHistory as any[];
    if (contextMessages.length > lastChatHistoryLengthRef.current) {
      setLocalMessages(contextMessages.map(msg => ({
        ...msg,
        isPending: false
      })));
      
      // Si estamos esperando respuesta y llegaron nuevos mensajes, dejar de esperar
      if (isWaitingForResponse && contextMessages.length > lastChatHistoryLengthRef.current) {
        setIsWaitingForResponse(false);
      }
      
      lastChatHistoryLengthRef.current = contextMessages.length;
    }
  }, [researchQuery, chatHistory, isWaitingForResponse]);

  // Handle initial question from suggested questions - CORREGIDO
  useEffect(() => {
    if (initialQuestion && !initialQuestionProcessedRef.current) {
      initialQuestionProcessedRef.current = true;
      console.log('Processing initial question:', initialQuestion);
      handleQuestionClick(initialQuestion);
      onQuestionSent?.();
    }
  }, [initialQuestion]); // Removí isWaitingForResponse de las dependencias

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [localMessages, isWaitingForResponse]);

  const formatTimestamp = (ts: number) => new Date(ts * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || isLoading || isWaitingForResponse) return;
    
    const userMessage = message.trim();
    setMessage('');
    setLocalError(null);
    setIsWaitingForResponse(true);
    
    // Add user message immediately to local state
    const userMsg: LocalMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: userMessage,
      timestamp: Date.now() / 1000,
      isPending: false
    };
    
    setLocalMessages(prev => [...prev, userMsg]);
    
    try {
      await sendChatMessage(userMessage, selectedArticles, researchQuery, chatHistory as any);
    } catch (error) {
      console.error('Error sending message:', error);
      setLocalError('Failed to send message. Please try again.');
      setIsWaitingForResponse(false);
    }
  };

  const handleQuestionClick = async (q: string) => {
    if (isLoading || isWaitingForResponse) return;
    setLocalError(null);
    setIsWaitingForResponse(true);
    
    // Add user question immediately to local state
    const userMsg: LocalMessage = {
      id: `user-${Date.now()}`,
      type: 'user',
      content: q,
      timestamp: Date.now() / 1000,
      isPending: false
    };
    
    setLocalMessages(prev => [...prev, userMsg]);
    
    try {
      await sendChatMessage(q, selectedArticles, researchQuery, chatHistory as any);
    } catch (error) {
      console.error('Error sending question:', error);
      setLocalError('Failed to send question. Please try again.');
      setIsWaitingForResponse(false);
    }
  };

  const hasMessages = localMessages.length > 0;

  return (
    <div className="flex flex-col h-full">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {!hasMessages && !isWaitingForResponse ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-4">
            <MessageCircle className="w-12 h-12 text-primary/30 mb-4" />
            <h3 className="text-lg font-semibold text-base-content mb-2">Start a Conversation</h3>
            <p className="text-sm text-base-content/70 mb-6 max-w-sm">
              Ask questions about the selected articles or your research topic.
            </p>

            {/* Starter Questions */}
            <div className="w-full max-w-md space-y-2">
              <p className="text-xs text-base-content/60 font-medium mb-3">Suggested questions:</p>
              <button
                onClick={() => handleQuestionClick('What are the main findings of these studies?')}
                className="w-full text-left text-sm p-3 bg-primary/5 hover:bg-primary/10 border border-primary/20 hover:border-primary/40 rounded-lg transition-all text-base-content"
                disabled={isLoading || isWaitingForResponse}
              >
                What are the main findings of these studies?
              </button>
              <button
                onClick={() => handleQuestionClick('How do these studies relate to each other?')}
                className="w-full text-left text-sm p-3 bg-primary/5 hover:bg-primary/10 border border-primary/20 hover:border-primary/40 rounded-lg transition-all text-base-content"
                disabled={isLoading || isWaitingForResponse}
              >
                How do these studies relate to each other?
              </button>
              <button
                onClick={() => handleQuestionClick('What are the practical applications?')}
                className="w-full text-left text-sm p-3 bg-primary/5 hover:bg-primary/10 border border-primary/20 hover:border-primary/40 rounded-lg transition-all text-base-content"
                disabled={isLoading || isWaitingForResponse}
              >
                What are the practical applications?
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Display all local messages */}
            {localMessages.map((msg) => (
              <div key={msg.id} className={`chat ${msg.type === 'user' ? 'chat-end' : 'chat-start'}`}>
                <div 
                  className={`chat-bubble ${
                    msg.type === 'user' 
                      ? 'chat-bubble-primary' 
                      : 'bg-base-200 text-base-content'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  <div className="chat-footer opacity-60 text-xs mt-1">
                    {formatTimestamp(msg.timestamp)}
                  </div>
                  
                  {/* Follow-up questions in assistant messages */}
                  {msg.type === 'assistant' && msg.follow_up_questions && msg.follow_up_questions.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-base-content/10">
                      <p className="text-xs font-semibold mb-2 opacity-80">Follow-up questions:</p>
                      <div className="space-y-1.5">
                        {msg.follow_up_questions.slice(0, 2).map((q, i) => (
                          <button
                            key={i}
                            onClick={() => handleQuestionClick(q.question)}
                            className="block w-full text-left text-xs p-2.5 bg-base-content/5 hover:bg-base-content/10 rounded transition-colors border border-base-content/10 hover:border-base-content/20"
                            disabled={isLoading || isWaitingForResponse}
                          >
                            {q.question}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Typing indicator - 3 dots animation */}
            {isWaitingForResponse && (
              <div className="chat chat-start">
                <div className="chat-bubble bg-base-200 text-base-content">
                  <div className="flex gap-1.5 items-center py-1">
                    <span className="w-2 h-2 bg-base-content/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-2 h-2 bg-base-content/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-2 h-2 bg-base-content/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </div>
                </div>
              </div>
            )}

            {/* Error message */}
            {localError && (
              <div className="flex justify-center">
                <div className="alert alert-error alert-sm max-w-sm">
                  <AlertCircle className="w-4 h-4" />
                  <span className="text-xs">{localError}</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Message Input */}
      <div className="border-t border-base-300 bg-base-100 p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Ask a question..."
            className="input input-bordered flex-1 input-sm text-base-content bg-base-100"
            disabled={isLoading || isWaitingForResponse}
          />
          <button
            type="submit"
            disabled={!message.trim() || isLoading || isWaitingForResponse}
            className="btn btn-primary btn-sm btn-square"
          >
            {isLoading || isWaitingForResponse ? (
              <span className="loading loading-spinner loading-xs" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </form>
        <p className="text-xs text-base-content/60 mt-2 truncate">
          Topic: {researchQuery}
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;