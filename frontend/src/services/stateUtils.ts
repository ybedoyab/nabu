export const handleApiError = (error: any): string => {
  if (error.response) {
    const { status, data } = error.response;

    switch (status) {
      case 400:
        return `Bad Request: ${data.message || "Invalid input"}`;
      case 404:
        return "API endpoint not found";
      case 500:
        return `Server Error: ${data.message || "Internal server error"}`;
      case 503:
        return `Service Unavailable: ${data.message || "AI service not ready"}`;
      default:
        return `API Error (${status}): ${data.message || "Unknown error"}`;
    }
  } else if (error.request) {
    return "Network Error: Unable to connect to the server. Please check your connection.";
  } else {
    return `Error: ${error.message}`;
  }
};

export const createLoadingState = () => ({
  isLoading: false,
  error: null,
  data: null,
});

export const setLoading = (state: any) => ({
  ...state,
  isLoading: true,
  error: null,
});

export const setSuccess = (state: any, data: any) => ({
  ...state,
  isLoading: false,
  error: null,
  data,
});

export const setError = (state: any, error: any) => ({
  ...state,
  isLoading: false,
  error,
  data: null,
});
