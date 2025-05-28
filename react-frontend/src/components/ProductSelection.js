import React from "react";
import { Star, ShoppingBag, Loader2, BarChart3 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import Image from "next/image";

const ProductCard = ({ product, store, isSelected, onSelect }) => {
  const displayName =
    product.name.length > 50
      ? product.name.substring(0, 50) + "..."
      : product.name;
  const price = product.price ? `$${product.price.toFixed(2)}` : "Price N/A";
  const rating = product.rating || 0;
  const reviewCount = product.review_count || 0;
  const specs = product.specifications || {};
  const imageUrl =
    product.image_url || "https://via.placeholder.com/100x100?text=No+Image";

  // Create star rating
  const stars = Array.from({ length: 5 }, (_, i) => (
    <Star
      key={i}
      className={`w-4 h-4 ${
        i < Math.floor(rating)
          ? "text-yellow-400 fill-current"
          : "text-gray-300"
      }`}
    />
  ));

  // Create spec tags (limit to 2 for compact layout)
  const specTags = Object.entries(specs).map(([key, value]) => (
    <span
      key={key}
      className="inline-block bg-gray-100 text-gray-600 px-2 py-1 rounded text-xs mr-1 mb-1"
    >
      {key}: {value}
    </span>
  ));

  return (
    <div
      className={`border-2 rounded-xl p-4 cursor-pointer transition-all duration-200 hover:shadow-lg ${
        isSelected
          ? "border-green-500 bg-green-50 shadow-md"
          : "border-gray-200 bg-white hover:border-blue-300"
      }`}
      onClick={() => onSelect(store, product)}
    >
      <div className="flex items-center gap-4">
        {/* Product Image */}
        <div className="flex-shrink-0 w-20 h-20 bg-gray-100 rounded-lg overflow-hidden">
          <Image
            src={imageUrl}
            alt={displayName}
            width={80}
            height={80}
            className="w-full h-full object-contain"
            onError={(e) => {
              e.target.src =
                "https://via.placeholder.com/100x100?text=No+Image";
            }}
            unoptimized={true}
          />
        </div>

        {/* Product Info */}
        <div className="flex-1 min-w-0">
          <h3
            className="font-semibold text-gray-800 mb-2 leading-tight h-10 overflow-hidden"
            style={{
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              wordBreak: "break-word",
            }}
          >
            {product.name}
          </h3>

          <div className="text-lg font-bold text-red-600 mb-2">{price}</div>

          <div className="flex items-center gap-2 mb-2">
            <div className="flex">{stars}</div>
            <span className="text-sm text-gray-600">
              {rating.toFixed(1)} ({reviewCount.toLocaleString()})
            </span>
          </div>

          {specTags.length > 0 && (
            <div className="mb-2 max-h-16 overflow-hidden">{specTags}</div>
          )}
        </div>

        {/* Selection Indicator */}
        <div className="flex-shrink-0">
          {isSelected ? (
            <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
              <svg
                className="w-4 h-4 text-white"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          ) : (
            <div className="w-6 h-6 border-2 border-gray-300 rounded-full"></div>
          )}
        </div>
      </div>
    </div>
  );
};

const StoreSection = ({
  store,
  products,
  selectedProducts,
  onSelectProduct,
}) => {
  if (!products || products.length === 0) return null;

  const selectedProduct = selectedProducts[store];

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 p-3 bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg border-l-4 border-blue-500">
        <ShoppingBag className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-bold text-gray-800">
          {store.charAt(0).toUpperCase() + store.slice(1)} Products
        </h3>
        <span className="text-sm text-gray-600">({products.length} found)</span>
      </div>

      <div className="space-y-3">
        {products.map((product, index) => (
          <ProductCard
            key={product.id || `${store}_${index}`}
            product={product}
            store={store}
            isSelected={selectedProduct && selectedProduct.id === product.id}
            onSelect={onSelectProduct}
          />
        ))}
      </div>
    </div>
  );
};

const SelectionSummary = ({ selectedProducts }) => {
  if (Object.keys(selectedProducts).length === 0) return null;

  return (
    <div className="bg-blue-50 border-2 border-blue-200 rounded-xl p-6 mt-6">
      <h3 className="text-lg font-bold text-blue-900 mb-4 flex items-center gap-2">
        📋 Selected Products for Analysis
      </h3>

      <div className="space-y-3">
        {Object.entries(selectedProducts).map(([store, product]) => {
          const price = product.price
            ? `$${product.price.toFixed(2)}`
            : "Price N/A";
          const rating = product.rating || 0;

          return (
            <div
              key={store}
              className="bg-white rounded-lg p-4 border border-blue-200"
            >
              <div className="font-semibold text-blue-600 text-sm uppercase tracking-wide">
                {store}
              </div>
              <div className="font-medium text-gray-900 mt-1">
                {product.name}
              </div>
              <div className="text-sm text-gray-600 mt-1">
                {price} • ⭐ {rating.toFixed(1)}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-4 p-3 bg-green-100 border border-green-300 rounded-lg text-center">
        <span className="text-green-800 font-semibold">
          Ready to analyze reviews from these products!
        </span>
      </div>
    </div>
  );
};

const ProductSelection = ({
  productsData,
  selectedProducts,
  onSelectProduct,
  onAnalyze,
  loading,
  status,
}) => {
  const hasProducts = Object.values(productsData).some(
    (products) => products && products.length > 0
  );
  const canAnalyze = Object.keys(selectedProducts).length >= 1;

  if (!hasProducts) {
    return (
      <div className="text-center py-8 text-gray-500">
        No products to display. Please search for products first.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Store Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Object.entries(productsData).map(([store, products]) => (
          <StoreSection
            key={store}
            store={store}
            products={products}
            selectedProducts={selectedProducts}
            onSelectProduct={onSelectProduct}
          />
        ))}
      </div>

      {/* Selection Summary */}
      <SelectionSummary selectedProducts={selectedProducts} />

      {/* Analysis Button */}
      {canAnalyze && (
        <div className="flex justify-center pt-4">
          <button
            onClick={onAnalyze}
            disabled={loading}
            className="px-8 py-4 bg-gradient-to-r from-green-600 to-blue-600 text-white font-bold rounded-xl hover:from-green-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-3 shadow-lg hover:shadow-xl text-lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-6 h-6 animate-spin" />
                Analyzing Reviews...
              </>
            ) : (
              <>
                <BarChart3 className="w-6 h-6" />
                Analyze Reviews
              </>
            )}
          </button>
        </div>
      )}

      {/* Status Display */}
      {status && (
        <div
          className={`p-4 rounded-lg border-l-4 ${
            status.includes("❌")
              ? "bg-red-50 border-red-400 text-red-800"
              : status.includes("🔬")
              ? "bg-blue-50 border-blue-400 text-blue-800"
              : "bg-green-50 border-green-400 text-green-800"
          }`}
        >
          {loading && status.includes("🔬") ? (
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

export default ProductSelection;
