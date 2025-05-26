import React from "react";
import {
  BarChart3,
  TrendingUp,
  ThumbsUp,
  ThumbsDown,
  Tag,
  Lightbulb,
  Target,
} from "lucide-react";

const getSentimentColor = (sentiment) => {
  const colors = {
    "Very Positive": "#10b981",
    Positive: "#34d399",
    Mixed: "#f59e0b",
    Negative: "#f97316",
    "Very Negative": "#ef4444",
  };
  return colors[sentiment] || "#6b7280";
};

const AnalysisHeader = ({ analysisResults }) => {
  const totalReviews = analysisResults.total_reviews || 0;
  const processingTime =
    analysisResults.extractData?.extraction_time_seconds || 0;

  return (
    <div className="text-center mb-8 pb-6 border-b-2 border-gray-100">
      <h2 className="text-3xl font-bold text-gray-900 mb-4 flex items-center justify-center gap-3">
        <BarChart3 className="w-8 h-8 text-blue-600" />
        Review Analysis Results
      </h2>

      <div className="flex justify-center gap-12 flex-wrap">
        <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl min-w-[120px]">
          <div className="text-3xl font-bold text-blue-600">{totalReviews}</div>
          <div className="text-sm font-semibold text-blue-800 uppercase tracking-wide">
            Total Reviews
          </div>
        </div>
        <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 rounded-xl min-w-[120px]">
          <div className="text-3xl font-bold text-green-600">
            {processingTime}s
          </div>
          <div className="text-sm font-semibold text-green-800 uppercase tracking-wide">
            Processing Time
          </div>
        </div>
      </div>
    </div>
  );
};

const OverallSummary = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        📝 Executive Summary
      </h3>
      <div className="bg-gray-50 p-6 rounded-xl border-l-4 border-blue-500">
        <p className="text-gray-700 leading-relaxed">{summary}</p>
      </div>
    </div>
  );
};

const SentimentAnalysis = ({ sentiment }) => {
  if (!sentiment || Object.keys(sentiment).length === 0) return null;

  return (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5" />
        Sentiment Analysis
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {Object.entries(sentiment).map(([store, data]) => {
          const sentimentColor = getSentimentColor(data.sentiment_label || "");

          return (
            <div
              key={store}
              className="bg-white border-2 border-gray-100 rounded-xl p-6 shadow-sm"
            >
              <div className="text-center mb-4">
                <div className="text-lg font-bold text-gray-800 mb-1">
                  {store.charAt(0).toUpperCase() + store.slice(1)}
                </div>
                <div
                  className="text-3xl font-bold mb-1"
                  style={{ color: sentimentColor }}
                >
                  {(data.average_rating || 0).toFixed(1)}/5
                </div>
                <div
                  className="font-semibold"
                  style={{ color: sentimentColor }}
                >
                  {data.sentiment_label || "Unknown"}
                </div>
              </div>

              <div className="space-y-2">
                <div className="flex h-3 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className="bg-green-500"
                    style={{ width: `${data.positive_percentage || 0}%` }}
                  ></div>
                  <div
                    className="bg-yellow-500"
                    style={{ width: `${data.neutral_percentage || 0}%` }}
                  ></div>
                  <div
                    className="bg-red-500"
                    style={{ width: `${data.negative_percentage || 0}%` }}
                  ></div>
                </div>
                <div className="text-xs text-gray-600 text-center">
                  {data.positive_percentage || 0}% Positive •{" "}
                  {data.neutral_percentage || 0}% Neutral •{" "}
                  {data.negative_percentage || 0}% Negative
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const ProsAndCons = ({ proscons }) => {
  if (!proscons || (!proscons.pros?.length && !proscons.cons?.length))
    return null;

  return (
    <div className="mb-8">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Pros */}
        <div>
          <h3 className="text-xl font-bold text-green-700 mb-4 flex items-center gap-2">
            <ThumbsUp className="w-5 h-5" />
            Top Pros
          </h3>
          <ul className="space-y-2">
            {(proscons.pros || []).map((pro, index) => (
              <li
                key={index}
                className="bg-green-50 border border-green-200 rounded-lg p-3 border-l-4 border-l-green-500"
              >
                {pro}
              </li>
            ))}
          </ul>
        </div>

        {/* Cons */}
        <div>
          <h3 className="text-xl font-bold text-red-700 mb-4 flex items-center gap-2">
            <ThumbsDown className="w-5 h-5" />
            Top Cons
          </h3>
          <ul className="space-y-2">
            {(proscons.cons || []).map((con, index) => (
              <li
                key={index}
                className="bg-red-50 border border-red-200 rounded-lg p-3 border-l-4 border-l-red-500"
              >
                {con}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

const CommonThemes = ({ themes }) => {
  if (!themes || themes.length === 0) return null;

  const getFrequencyColor = (frequency) => {
    const colors = { High: "#ef4444", Medium: "#f59e0b", Low: "#6b7280" };
    return colors[frequency] || "#6b7280";
  };

  return (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <Tag className="w-5 h-5" />
        Common Discussion Topics
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {themes.map((theme, index) => {
          const frequencyColor = getFrequencyColor(theme.frequency);

          return (
            <div
              key={index}
              className="bg-white border-2 border-gray-100 rounded-xl p-4 shadow-sm"
            >
              <div className="flex justify-between items-start mb-2">
                <span className="font-semibold text-gray-900">
                  {theme.theme || "Unknown"}
                </span>
                <span
                  className="text-xs font-bold px-2 py-1 rounded text-white"
                  style={{ backgroundColor: frequencyColor }}
                >
                  {theme.frequency || "Unknown"}
                </span>
              </div>
              <p className="text-sm text-gray-600 leading-relaxed">
                {theme.description || ""}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const ProductComparison = ({ comparison, selectedProducts }) => {
  if (
    !comparison ||
    Object.keys(comparison).length === 0 ||
    Object.keys(selectedProducts).length <= 1
  )
    return null;

  return (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        ⚖️ Product Comparison
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {Object.entries(comparison).map(([category, details]) => {
          if (typeof details !== "object" || !details.summary) return null;

          return (
            <div
              key={category}
              className="bg-white border-2 border-gray-100 rounded-xl p-4 shadow-sm"
            >
              <h4 className="font-bold text-gray-900 mb-2">
                {category
                  .replace("_", " ")
                  .replace(/\b\w/g, (l) => l.toUpperCase())}
              </h4>
              <p className="text-gray-700 text-sm leading-relaxed">
                {details.summary}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const KeyInsights = ({ insights }) => {
  if (!insights || insights.length === 0) return null;

  return (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <Lightbulb className="w-5 h-5" />
        Key Insights
      </h3>

      <div className="space-y-3">
        {insights.map((insight, index) => (
          <div
            key={index}
            className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-lg p-4 border-l-4 border-l-blue-500"
          >
            <Lightbulb className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <p className="text-gray-800 leading-relaxed">{insight}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

const Recommendations = ({ recommendations }) => {
  if (!recommendations || Object.keys(recommendations).length === 0)
    return null;

  return (
    <div className="mb-8">
      <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
        <Target className="w-5 h-5" />
        Recommendations
      </h3>

      <div className="space-y-4">
        {recommendations.best_overall && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-6 border-l-4 border-l-yellow-500">
            <h4 className="font-bold text-yellow-800 mb-2 flex items-center gap-2">
              🏆 Best Overall Choice
            </h4>
            <p className="text-yellow-900">{recommendations.best_overall}</p>
          </div>
        )}

        {recommendations.best_value && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 border-l-4 border-l-green-500">
            <h4 className="font-bold text-green-800 mb-2 flex items-center gap-2">
              💰 Best Value for Money
            </h4>
            <p className="text-green-900">{recommendations.best_value}</p>
          </div>
        )}

        {recommendations.considerations && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-6 border-l-4 border-l-red-500">
            <h4 className="font-bold text-red-800 mb-2 flex items-center gap-2">
              ⚠️ Important Considerations
            </h4>
            <p className="text-red-900">{recommendations.considerations}</p>
          </div>
        )}
      </div>
    </div>
  );
};

const AnalysisResults = ({ analysisResults, selectedProducts }) => {
  if (!analysisResults || analysisResults.error) {
    return (
      <div className="text-center py-8">
        <div className="text-red-600 font-semibold">
          Analysis failed. Please try again.
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <AnalysisHeader analysisResults={analysisResults} />
      <OverallSummary summary={analysisResults.overall_summary} />
      <SentimentAnalysis sentiment={analysisResults.sentiment_analysis} />
      <ProsAndCons proscons={analysisResults.pros_cons} />
      <CommonThemes themes={analysisResults.common_themes} />
      <ProductComparison
        comparison={analysisResults.product_comparison}
        selectedProducts={selectedProducts}
      />
      <KeyInsights insights={analysisResults.key_insights} />
      <Recommendations recommendations={analysisResults.recommendations} />
    </div>
  );
};

export default AnalysisResults;
