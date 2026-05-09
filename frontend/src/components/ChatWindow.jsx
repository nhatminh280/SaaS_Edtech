import { useEffect, useRef, useState } from "react";

import { useChat } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";

const DEMO_QUESTIONS = [
  "Điều kiện để được xét tốt nghiệp là gì?",
  "Sinh viên bị cảnh cáo học vụ khi nào?",
  "Điểm trung bình tích lũy tối thiểu để không bị đình chỉ học?",
  "Quy trình đăng ký bảo lưu kết quả học tập như thế nào?",
  "Học bổng khuyến khích cần điều kiện gì?",
];

export function ChatWindow() {
  const { messages, loading, error, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = () => {
    if (!input.trim() || loading) return;
    sendMessage(input.trim());
    setInput("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f1f5f9",
        color: "#0f172a",
        fontFamily: "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
      }}
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100vh",
          maxWidth: 820,
          margin: "0 auto",
          background: "#fff",
          borderLeft: "1px solid #e2e8f0",
          borderRight: "1px solid #e2e8f0",
        }}
      >
        <div
          style={{
            padding: "14px 20px",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            gap: 12,
            minHeight: 64,
          }}
        >
          <div
            style={{
              width: 36,
              height: 36,
              borderRadius: "50%",
              background: "#2563eb",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontWeight: 700,
              fontSize: 14,
              flexShrink: 0,
            }}
          >
            QA
          </div>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, fontSize: 15 }}>QA Quy chế HCMUS</div>
            <div style={{ fontSize: 12, color: "#64748b", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
              RAG + Z3 Solver - câu trả lời có trích dẫn điều khoản
            </div>
          </div>
          <button
            onClick={clearChat}
            style={{
              marginLeft: "auto",
              fontSize: 12,
              color: "#475569",
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              padding: "6px 10px",
              cursor: "pointer",
              background: "#fff",
              flexShrink: 0,
            }}
          >
            Xóa chat
          </button>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
          {messages.length === 0 && (
            <div style={{ color: "#475569", margin: "28px auto 0", maxWidth: 520 }}>
              <div style={{ fontWeight: 700, marginBottom: 14, color: "#0f172a" }}>
                Hỏi bất kỳ điều gì về quy chế HCMUS
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {DEMO_QUESTIONS.map((question) => (
                  <button
                    key={question}
                    onClick={() => sendMessage(question)}
                    style={{
                      textAlign: "left",
                      padding: "10px 12px",
                      borderRadius: 8,
                      border: "1px solid #e2e8f0",
                      cursor: "pointer",
                      background: "#f8fafc",
                      fontSize: 13,
                      color: "#1e293b",
                      lineHeight: 1.45,
                    }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((message) => (
            <MessageBubble key={message.id} message={message} />
          ))}

          {loading && (
            <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
              <div
                style={{
                  background: "#f1f5f9",
                  borderRadius: 14,
                  padding: "10px 14px",
                  fontSize: 13,
                  color: "#475569",
                }}
              >
                Đang tìm kiếm điều khoản...
              </div>
            </div>
          )}

          {error && (
            <div
              style={{
                background: "#fee2e2",
                color: "#991b1b",
                padding: "10px 14px",
                borderRadius: 8,
                fontSize: 13,
                marginBottom: 12,
              }}
            >
              {error}
            </div>
          )}

          <div ref={bottomRef} />
        </div>

        <div style={{ padding: "12px 20px", borderTop: "1px solid #e2e8f0", display: "flex", gap: 10 }}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi về quy chế học vụ..."
            rows={2}
            style={{
              flex: 1,
              resize: "none",
              border: "1px solid #cbd5e1",
              borderRadius: 8,
              padding: "10px 12px",
              fontSize: 14,
              fontFamily: "inherit",
              outline: "none",
              lineHeight: 1.5,
              minWidth: 0,
            }}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            style={{
              padding: "0 18px",
              background: "#2563eb",
              color: "#fff",
              border: "none",
              borderRadius: 8,
              cursor: loading || !input.trim() ? "not-allowed" : "pointer",
              fontSize: 14,
              fontWeight: 700,
              opacity: loading || !input.trim() ? 0.5 : 1,
              minWidth: 70,
            }}
          >
            Gửi
          </button>
        </div>
      </div>
    </div>
  );
}
