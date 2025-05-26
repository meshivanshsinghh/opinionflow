"use client";

import React, { useState } from "react";
import { v4 as uuidv4 } from "uuid";
import axios from "axios";
import {
  Search,
  ShoppingCart,
  BarChart3,
  MessageCircle,
  Loader2,
} from "lucide-react";
import ProductSearch from "./ProductSearch";
import ProductSelection from "./ProductSelection";
import AnalysisResults from "./AnalysisResults";
import ChatInterface from "./ChatInterface";
import { apiClient, endpoints, handleApiError } from "../utils/api";

const OpinionFlow = () => {
  const [sessionId] = useState(() => uuidv4());
  const [selectedProducts, setSelectedProducts] = useState({});
  const [analysisResults, setAnalysisResults] = useState(null);
  const [productsData, setProductsData] = useState({});
  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [searchStatus, setSearchStatus] = useState("");
  const [analysisStatus, setAnalysisStatus] = useState("");

  const searchProducts = async (query, maxPerStore = 5) => {
    if (!query.trim()) {
      setSearchStatus("⚠️ Please enter a product name to search.");
      return;
    }

    setLoading(true);
    setSearchStatus("🔍 Searching for products across stores...");

    try {
      const response = await apiClient.post(
        `${endpoints.discover}`,
        { query, max_per_store: maxPerStore },
        { timeout: 60000 }
      );

      const data = response.data;
      const products = data.products || {};
      setProductsData(products);

      if (
        !Object.keys(products).length ||
        !Object.values(products).some((arr) => arr.length > 0)
      ) {
        setSearchStatus("❌ No products found. Try a different search term.");
        return;
      }

      const totalProducts = Object.values(products).reduce(
        (sum, arr) => sum + arr.length,
        0
      );
      setSearchStatus(`✅ Found ${totalProducts} products for: **${query}**`);
      setCurrentStep(2);
    } catch (error) {
      const errorMessage = handleApiError(error);
      setSearchStatus(`❌ Error searching products: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const selectProduct = (store, product) => {
    setSelectedProducts((prev) => ({
      ...prev,
      [store]: product,
    }));
  };

  const analyzeReviews = async () => {
    if (!Object.keys(selectedProducts).length) {
      setAnalysisStatus("❌ Please select at least one product first");
      return;
    }

    setLoading(true);
    setAnalysisStatus(
      "🔬 Extracting and analyzing reviews... This may take a moment."
    );

    try {
      // Step 1: Extract reviews
      const extractResponse = await apiClient.post(
        endpoints.extractReviews,
        {
          session_id: sessionId,
          selected_products: selectedProducts,
        },
        { timeout: 120000 }
      );

      const extractData = extractResponse.data;

      // Step 2: Analyze reviews
      const analysisResponse = await apiClient.post(
        endpoints.analyzeReviews,
        {
          session_id: sessionId,
          selected_products: selectedProducts,
        },
        { timeout: 60000 }
      );

      const analysisData = analysisResponse.data;
      setAnalysisResults({ ...analysisData, extractData });

      setAnalysisStatus(
        `✅ Analysis Complete! Processed ${
          extractData.total_reviews || 0
        } reviews`
      );
      setCurrentStep(3);
    } catch (error) {
      setAnalysisStatus(`❌ Analysis failed: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const chatWithReviews = async (message, history) => {
    if (!analysisResults) {
      return [
        ...history,
        {
          user: message,
          bot: "Please complete the review analysis first before asking questions.",
        },
      ];
    }

    if (!message.trim()) {
      return history;
    }

    // Handle greeting messages
    const greetings = ["hi", "hello", "hey", "hi there", "hello there"];
    if (greetings.includes(message.toLowerCase().trim())) {
      const selectedProductNames = Object.entries(selectedProducts)
        .map(
          ([store, product]) =>
            `${store.charAt(0).toUpperCase() + store.slice(1)}: ${product.name}`
        )
        .join(", ");

      const greetingResponse = `
Hello! 👋 I'm your Review Intelligence Assistant. 

I've analyzed reviews for your selected products:
${selectedProductNames}

You can ask me questions like:
• "Which product has better battery life?"
• "What do customers say about durability?"
• "Compare the prices and value"
• "What are the main complaints?"
• "Which store has better customer service?"

What would you like to know about these products?
      `;

      return [...history, { user: message, bot: greetingResponse }];
    }

    try {
      const response = await apiClient.post(
        endpoints.askQuestion,
        {
          session_id: sessionId,
          question: message,
        },
        { timeout: 30000 }
      );

      const answerData = response.data;

      if (answerData.error) {
        return [
          ...history,
          {
            user: message,
            bot: `❌ I encountered an error: ${answerData.error}`,
          },
        ];
      }

      let botResponse = answerData.answer || "I could not generate an answer.";

      // Add sources
      const sources = answerData.sources || [];
      if (sources.length > 0) {
        botResponse += "\n\n**📚 Sources from reviews:**";
        sources.slice(0, 3).forEach((source, i) => {
          const store = source.store || "Unknown";
          const rating = source.rating || 0;
          const snippet = source.text_snippet || "";
          botResponse += `\n\n**${i + 1}. ${
            store.charAt(0).toUpperCase() + store.slice(1)
          } Review** (⭐${rating}/5):\n*"${snippet}"*`;
        });
      }

      const confidence = answerData.confidence || 0;
      if (confidence > 0) {
        botResponse += `\n\n*Confidence: ${(confidence * 100).toFixed(0)}%*`;
      }

      return [...history, { user: message, bot: botResponse }];
    } catch (error) {
      const errorResponse = `❌ Sorry, I encountered an error processing your question: ${error.message}`;
      return [...history, { user: message, bot: errorResponse }];
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white py-8 px-6 text-center shadow-lg">
        <h1 className="text-4xl font-bold mb-2">🗣️ OpinionFlow</h1>
        <p className="text-xl opacity-95">
          AI-Powered Cross-Store Product Review Intelligence
        </p>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Step 1: Product Discovery */}
        <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
              1
            </div>
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Search className="w-6 h-6" />
              Discover Products
            </h2>
          </div>

          <ProductSearch
            onSearch={searchProducts}
            loading={loading}
            status={searchStatus}
          />
        </div>

        {/* Step 2: Product Selection */}
        {currentStep >= 2 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
                2
              </div>
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <ShoppingCart className="w-6 h-6" />
                Select Products to Compare
              </h2>
            </div>

            <ProductSelection
              productsData={productsData}
              selectedProducts={selectedProducts}
              onSelectProduct={selectProduct}
              onAnalyze={analyzeReviews}
              loading={loading}
              status={analysisStatus}
            />
          </div>
        )}

        {/* Step 3: Analysis Results */}
        {currentStep >= 3 && analysisResults && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
                3
              </div>
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <BarChart3 className="w-6 h-6" />
                Analysis Results
              </h2>
            </div>

            <AnalysisResults
              analysisResults={analysisResults}
              selectedProducts={selectedProducts}
            />
          </div>
        )}

        {/* Step 4: Chat Interface */}
        {currentStep >= 3 && analysisResults && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
                4
              </div>
              <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
                <MessageCircle className="w-6 h-6" />
                Ask Questions About Your Products
              </h2>
            </div>

            <ChatInterface
              onChat={chatWithReviews}
              selectedProducts={selectedProducts}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default OpinionFlow;
