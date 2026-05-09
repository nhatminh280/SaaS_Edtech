import { useCallback, useState } from "react";

import { askQuestion } from "../api/client";

export function useChat() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const sendMessage = useCallback(async (question, userFacts = null) => {
    setError(null);
    setLoading(true);

    const userMsg = { id: crypto.randomUUID(), role: "user", content: question };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const response = await askQuestion(question, userFacts);
      const assistantMsg = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: response.answer,
        citations: response.citations || [],
        confidence: response.confidence,
        z3Result: response.z3_result,
        questionType: response.question_type,
        processingTimeMs: response.processing_time_ms,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return { messages, loading, error, sendMessage, clearChat };
}
