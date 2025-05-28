import React, { useState } from "react";
import { Search, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";

const ProductSearch = ({ onSearch, loading, status }) => {
  const [query, setQuery] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    onSearch(query);
  };

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-4">
        <div className="flex-1">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., iPhone 14 Pro, Nike Air Max, Samsung TV, MacBook Pro..."
            className="text-black w-full px-4 py-3 border-2 border-white/30 bg-white/90 backdrop-blur-sm rounded-lg focus:border-white focus:bg-white focus:outline-none transition-colors text-lg placeholder-gray-500"
            disabled={loading}
          />
        </div>
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold rounded-lg hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 shadow-lg hover:shadow-xl"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Searching...
            </>
          ) : (
            <>
              <Search className="w-5 h-5" />
              Discover Products
            </>
          )}
        </button>
      </form>

      {/* Status Display */}
      {status && (
        <div
          className={`p-4 rounded-lg border-l-4 ${
            status.includes("❌")
              ? "bg-red-50 border-red-400 text-red-800"
              : status.includes("⚠️")
              ? "bg-yellow-50 border-yellow-400 text-yellow-800"
              : status.includes("🔍")
              ? "bg-blue-50 border-blue-400 text-blue-800"
              : "bg-green-50 border-green-400 text-green-800"
          }`}
        >
          {loading && status.includes("🔍") ? (
            <div className="flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="font-medium">{status}</span>
            </div>
          ) : (
            <ReactMarkdown className="prose prose-sm max-w-none">
              {status}
            </ReactMarkdown>
          )}
        </div>
      )}
    </div>
  );
};

export default ProductSearch;
