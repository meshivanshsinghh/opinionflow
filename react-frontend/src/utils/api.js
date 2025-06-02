import axios from "axios";

export const API_BASE =
  "https://opinionflow-backend-392699812750.us-central1.run.app/api/v1";

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    "Content-Type": "application/json",
  },
  maxRedirects: 0,
});

// API endpoints
export const endpoints = {
  discover: "products/discover",
  extractReviews: "reviews/extract",
  analyzeReviews: "analysis/analyze",
  askQuestion: "analysis/question",
  enhanceSpecifications: "products/enhance-specifications",
};

// Error handling utility function
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    return (
      error.response.data?.message ||
      error.response.data?.error ||
      `Server error: ${error.response.status}`
    );
  } else if (error.request) {
    // Request was made but no response received
    return "Network error: Unable to reach the server";
  } else {
    // Something else happened
    return error.message || "An unexpected error occurred";
  }
};
