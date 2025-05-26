import axios from "axios";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE ||
  "https://opinionflow-backend-dd9f15bcfb74.herokuapp.com/api/v1";

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
});

// API endpoints
export const endpoints = {
  discover: "/products/discover/",
  extractReviews: "/reviews/extract/",
  analyzeReviews: "/analysis/analyze/",
  askQuestion: "/analysis/question/",
};

// Helper function to handle API errors
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    return (
      error.response.data?.message ||
      error.response.statusText ||
      "Server error"
    );
  } else if (error.request) {
    // Request was made but no response received
    return "Network error - please check your connection";
  } else {
    // Something else happened
    return error.message || "An unexpected error occurred";
  }
};
