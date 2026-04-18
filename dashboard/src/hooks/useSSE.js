import { useEffect, useRef, useState } from "react";

export function useSSE(url) {
  const [data, setData] = useState(null);
  const [status, setStatus] = useState("idle");
  const sourceRef = useRef(null);

  useEffect(() => {
    if (!url) {
      return undefined;
    }

    const source = new EventSource(url);
    sourceRef.current = source;
    setStatus("connecting");

    source.onopen = () => setStatus("open");
    source.onerror = () => setStatus("error");
    source.onmessage = (event) => {
      try {
        setData(JSON.parse(event.data));
      } catch (error) {
        console.error("Failed to parse SSE payload", error);
      }
    };

    return () => {
      source.close();
    };
  }, [url]);

  return { data, status };
}
