import React, { useState, useRef, useEffect } from "react";
import { Send, MessageCircle, Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

const ChatMessage = ({ message, isUser }) => {
  return (
    <div
      className={`flex gap-3 ${isUser ? "justify-end" : "justify-start"} mb-4`}
    >
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
          <Bot className="w-4 h-4 text-white" />
        </div>
      )}

      <div className={`max-w-[80%] ${isUser ? "order-first" : ""}`}>
        <div
          className={`rounded-2xl px-4 py-3 ${
            isUser
              ? "bg-blue-600 text-white ml-auto"
              : "bg-gray-100 text-gray-900"
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message}</p>
          ) : (
            <ReactMarkdown
              className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-strong:text-gray-900"
              components={{
                p: ({ children }) => (
                  <p className="mb-2 last:mb-0">{children}</p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside mb-2 space-y-1">
                    {children}
                  </ul>
                ),
                li: ({ children }) => <li className="text-sm">{children}</li>,
                strong: ({ children }) => (
                  <strong className="font-semibold">{children}</strong>
                ),
                em: ({ children }) => <em className="italic">{children}</em>,
              }}
            >
              {message}
            </ReactMarkdown>
          )}
        </div>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
          <User className="w-4 h-4 text-white" />
        </div>
      )}
    </div>
  );
};

const SuggestedQuestions = ({ onQuestionClick }) => {
  const suggestions = [
    "Which product has better battery life?",
    "What do customers say about durability?",
    "Compare the prices and value",
    "What are the main complaints?",
    "Which store has better customer service?",
    "Tell me about shipping experiences",
  ];

  return (
    <div className="mb-6">
      <h4 className="text-sm font-semibold text-gray-700 mb-3">
        💡 Try asking:
      </h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {suggestions.map((question, index) => (
          <button
            key={index}
            onClick={() => onQuestionClick(question)}
            className="text-left p-3 text-sm bg-gray-50 hover:bg-blue-50 border border-gray-200 hover:border-blue-300 rounded-lg transition-colors duration-200"
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
};

const ChatInterface = ({ onChat, selectedProducts }) => {
  const [message, setMessage] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userMessage = message.trim();
    setMessage("");
    setIsLoading(true);

    // Add user message to history
    const newHistory = [...chatHistory, { user: userMessage, bot: null }];
    setChatHistory(newHistory);

    try {
      // Get bot response
      const updatedHistory = await onChat(userMessage, chatHistory);
      setChatHistory(updatedHistory);
    } catch (error) {
      console.error("Chat error:", error);
      setChatHistory((prev) => [
        ...prev.slice(0, -1),
        {
          user: userMessage,
          bot: "Sorry, I encountered an error. Please try again.",
        },
      ]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSuggestedQuestion = (question) => {
    setMessage(question);
    inputRef.current?.focus();
  };

  const selectedProductNames = Object.entries(selectedProducts)
    .map(
      ([store, product]) =>
        `${store.charAt(0).toUpperCase() + store.slice(1)}: ${product.name}`
    )
    .join(", ");

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Chat Area */}
      <div className="lg:col-span-2">
        <div className="bg-white border-2 border-gray-200 rounded-xl overflow-hidden">
          {/* Chat Header */}
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
            <div className="flex items-center gap-3">
              <MessageCircle className="w-6 h-6" />
              <div>
                <h3 className="font-bold">Review Intelligence Assistant</h3>
                <p className="text-sm opacity-90">
                  Ask me anything about your selected products
                </p>
              </div>
            </div>
          </div>

          {/* Chat Messages */}
          <div className="h-96 overflow-y-auto p-4 bg-gray-50">
            {chatHistory.length === 0 ? (
              <div className="text-center py-8">
                <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">
                  Hello! I'm ready to answer questions about your selected
                  products:
                </p>
                <p className="text-sm text-gray-500 font-medium">
                  {selectedProductNames}
                </p>
                <p className="text-sm text-gray-500 mt-4">
                  Ask me anything about features, reviews, comparisons, or
                  recommendations!
                </p>
              </div>
            ) : (
              <>
                {chatHistory.map((chat, index) => (
                  <div key={index}>
                    <ChatMessage message={chat.user} isUser={true} />
                    {chat.bot && (
                      <ChatMessage message={chat.bot} isUser={false} />
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3 justify-start mb-4">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                    <div className="bg-gray-100 rounded-2xl px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.1s" }}
                          ></div>
                          <div
                            className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                            style={{ animationDelay: "0.2s" }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600">
                          Thinking...
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Chat Input */}
          <div className="border-t border-gray-200 p-4 bg-white">
            <form onSubmit={handleSubmit} className="flex gap-3">
              <input
                ref={inputRef}
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask a question about your products..."
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:border-blue-500 focus:outline-none"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={!message.trim() || isLoading}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200 flex items-center gap-2"
              >
                <Send className="w-4 h-4" />
                Send
              </button>
            </form>
          </div>
        </div>
      </div>

      {/* Suggested Questions Sidebar */}
      <div className="lg:col-span-1">
        <div className="bg-white border-2 border-gray-200 rounded-xl p-6">
          <SuggestedQuestions onQuestionClick={handleSuggestedQuestion} />

          {/* Selected Products Summary */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">
              📦 Analyzing:
            </h4>
            <div className="space-y-2">
              {Object.entries(selectedProducts).map(([store, product]) => (
                <div key={store} className="text-xs bg-gray-50 rounded-lg p-2">
                  <div className="font-semibold text-blue-600 uppercase tracking-wide">
                    {store}
                  </div>
                  <div className="text-gray-700 mt-1 leading-tight">
                    {product.name.length > 40
                      ? product.name.substring(0, 40) + "..."
                      : product.name}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
