"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "./api";

/**
 * Load data from the API with loading / error states and a reload() function.
 * Only the newest request may update the state: when the path changes quickly (filters), a slower,
 * older response can never overwrite the newer one.
 */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [loading, setLoading] = useState<boolean>(!!path);
  const latest = useRef(0);

  const load = useCallback(async () => {
    if (!path) return;
    const id = ++latest.current;
    setLoading(true);
    try {
      const result = await api<T>(path);
      if (id !== latest.current) return;
      setData(result);
      setError(null);
    } catch (e) {
      if (id !== latest.current) return;
      setError(e instanceof ApiError ? e : new ApiError(0, String(e)));
    } finally {
      if (id === latest.current) setLoading(false);
    }
  }, [path]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, error, loading, reload: load, setData };
}

/** Run an action (POST/PUT/DELETE) and track busy + error state. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const run = useCallback(async <T,>(fn: () => Promise<T>): Promise<T | undefined> => {
    setBusy(true);
    setError(null);
    try {
      return await fn();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      return undefined;
    } finally {
      setBusy(false);
    }
  }, []);
  return { busy, error, setError, run };
}
