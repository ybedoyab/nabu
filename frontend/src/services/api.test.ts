import { describe, expect, it } from "vitest";

import {
  createLoadingState,
  handleApiError,
  setError,
  setLoading,
  setSuccess,
} from "./stateUtils";

describe("handleApiError", () => {
  it("handles 400 errors", () => {
    const msg = handleApiError({ response: { status: 400, data: { message: "Bad data" } } });
    expect(msg).toContain("Bad Request");
  });
  it("handles 400 errors with default message", () => {
    const msg = handleApiError({ response: { status: 400, data: {} } });
    expect(msg).toBe("Bad Request: Invalid input");
  });

  it("handles 404 errors", () => {
    const msg = handleApiError({ response: { status: 404, data: {} } });
    expect(msg).toBe("API endpoint not found");
  });

  it("handles 500 errors", () => {
    const msg = handleApiError({ response: { status: 500, data: { message: "Crash" } } });
    expect(msg).toContain("Server Error");
  });
  it("handles 500 errors with default message", () => {
    const msg = handleApiError({ response: { status: 500, data: {} } });
    expect(msg).toBe("Server Error: Internal server error");
  });

  it("handles 503 errors", () => {
    const msg = handleApiError({ response: { status: 503, data: { message: "Unavailable" } } });
    expect(msg).toContain("Service Unavailable");
  });
  it("handles 503 errors with default message", () => {
    const msg = handleApiError({ response: { status: 503, data: {} } });
    expect(msg).toBe("Service Unavailable: AI service not ready");
  });

  it("handles generic response errors", () => {
    const msg = handleApiError({ response: { status: 418, data: { message: "Teapot" } } });
    expect(msg).toContain("API Error (418)");
  });
  it("handles generic response errors with default message", () => {
    const msg = handleApiError({ response: { status: 418, data: {} } });
    expect(msg).toBe("API Error (418): Unknown error");
  });

  it("handles network errors", () => {
    const msg = handleApiError({ request: {} });
    expect(msg).toContain("Network Error");
  });

  it("handles unknown errors", () => {
    const msg = handleApiError({ message: "Oops" });
    expect(msg).toBe("Error: Oops");
  });

  it("handles loading state helpers", () => {
    const initial = createLoadingState();
    expect(initial).toEqual({ isLoading: false, error: null, data: null });

    const loading = setLoading(initial);
    expect(loading).toEqual({ isLoading: true, error: null, data: null });

    const success = setSuccess(loading, { ok: true });
    expect(success).toEqual({ isLoading: false, error: null, data: { ok: true } });

    const failed = setError(success, "bad");
    expect(failed).toEqual({ isLoading: false, error: "bad", data: null });
  });
});
