import axios from "axios";

export const API_BASE =
  "https://opinionflow-backend-392699812750.us-central1.run.app/api/v1";
// export const API_BASE = "http://127.0.0.1:8000/api/v1";

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
  discover: "/products/discover",
  extractReviews: "/reviews/extract",
  analyzeReviews: "/analysis/analyze",
  askQuestion: "/analysis/question",
};

// Add request interceptor to log requests
// apiClient.interceptors.request.use(
//   (config) => {
//     console.log(
//       `Making ${config.method?.toUpperCase()} request to:`,
//       config.url
//     );
//     return config;
//   },
//   (error) => {
//     return Promise.reject(error);
//   }
// );

// Add response interceptor to handle errors
// apiClient.interceptors.response.use(
//   (response) => {
//     return response;
//   },
//   (error) => {
//     console.error("API Error:", error);

//     // Handle redirect errors specifically
//     if (error.response?.status === 307 || error.response?.status === 308) {
//       console.error("Redirect detected - this might cause CORS issues");
//     }

//     return Promise.reject(error);
//   }
// );

// Helper function to handle API errors
// export const handleApiError = (error) => {
//   if (error.response) {
//     // Server responded with error status
//     return (
//       error.response.data?.message ||
//       error.response.statusText ||
//       "Server error"
//     );
//   } else if (error.request) {
//     // Request was made but no response received
//     return "Network error - please check your connection";
//   } else {
//     // Something else happened
//     return error.message || "An unexpected error occurred";
//   }
// };
