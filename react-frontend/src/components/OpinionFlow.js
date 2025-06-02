"use client";

import React, { useState } from "react";
import { Search, ShoppingCart, BarChart3, MessageCircle } from "lucide-react";
import ProductSearch from "./ProductSearch";
import ProductSelection from "./ProductSelection";
import AnalysisResults from "./AnalysisResults";
import ChatInterface from "./ChatInterface";
import { apiClient, endpoints, handleApiError } from "../utils/api";

const OpinionFlow = () => {
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
        endpoints.discover,
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
          selected_products: selectedProducts,
        },
        { timeout: 120000 }
      );

      const extractData = extractResponse.data;

      // Step 2: Analyze reviews
      const analysisResponse = await apiClient.post(
        endpoints.analyzeReviews,
        {
          selected_products: selectedProducts,
        },
        { timeout: 120000 }
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
          question: message,
          selected_products: selectedProducts,
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
    <div className="min-h-screen bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-700">
      {/* Enhanced Header with Search */}
      <div className="relative text-white overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent"></div>
        </div>

        <div className="relative z-10 py-16 px-6 text-center max-w-6xl mx-auto">
          {/* Logo and Title Section */}
          <div className="mb-8">
            <div className="inline-flex items-center justify-center w-20 h-20 bg-white/20 backdrop-blur-sm rounded-2xl mb-6 shadow-xl">
              <span className="text-4xl">🗣️</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-bold mb-4 bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
              OpinionFlow
            </h1>
            <div className="w-24 h-1 bg-gradient-to-r from-yellow-400 to-orange-500 mx-auto rounded-full mb-6"></div>
          </div>

          {/* Tagline */}
          <div className="max-w-4xl mx-auto">
            <p className="text-xl md:text-2xl font-medium mb-4 leading-relaxed">
              AI-Powered Cross-Store Product Review Intelligence
            </p>
            <p className="text-lg opacity-90 mb-8 max-w-2xl mx-auto leading-relaxed">
              Discover, compare, and analyze products across multiple stores
              with intelligent review insights
            </p>
          </div>

          {/* Search Section - Now in Header */}
          <div className="max-w-2xl mx-auto mb-8">
            <ProductSearch
              onSearch={searchProducts}
              loading={loading}
              status={searchStatus}
            />
          </div>

          {/* Feature Pills */}
          <div className="flex flex-wrap justify-center gap-3">
            <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
              <Search className="w-4 h-4" />
              Smart Discovery
            </div>
            <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
              <BarChart3 className="w-4 h-4" />
              Deep Analysis
            </div>
            <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm px-4 py-2 rounded-full text-sm font-medium">
              <MessageCircle className="w-4 h-4" />
              AI Chat
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-0 space-y-8">
        {/* Success Message when products are found */}
        {currentStep >= 2 && (
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-white/90 backdrop-blur-sm text-green-800 px-4 py-2 rounded-full">
              {" "}
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="font-medium">
                Products Found! Choose items to compare below.
              </span>
            </div>
          </div>
        )}

        {/* Step 1: Product Selection */}
        {currentStep >= 2 && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
                1
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

        {/* Step 2: Analysis Results */}
        {currentStep >= 3 && analysisResults && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
                2
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

        {/* Step 3: Chat Interface */}
        {currentStep >= 3 && analysisResults && (
          <div className="bg-white rounded-2xl shadow-lg p-6 border-2 border-gray-100">
            <div className="flex items-center gap-3 mb-6">
              <div className="flex items-center justify-center w-8 h-8 bg-blue-600 text-white rounded-full font-bold">
                3
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
