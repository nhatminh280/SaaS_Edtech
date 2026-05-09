import { useCallback, useEffect, useRef, useState } from "react";

import { useChat } from "../hooks/useChat";
import { MessageBubble } from "./MessageBubble";
import { UserFactsModal } from "./UserFactsModal";

const DEMO_QUESTIONS = [
  {
    text: "Điều kiện để được xét tốt nghiệp là gì?",
    type: "factual",
    facts: null,
  },
  {
    text: "Sinh viên bị cảnh cáo học vụ trong trường hợp nào?",
    type: "factual",
    facts: null,
  },
  {
    text: "Quy trình xin bảo lưu kết quả học tập như thế nào?",
    type: "procedural",
    facts: null,
  },
  {
    text: "Tôi có đủ điều kiện tốt nghiệp không?",
    type: "logical",
    facts: {
      tin_chi_tich_luy: 122,
      diem_tb: 2.75,
      no_mon: false,
      hoan_thanh_tttn: true,
      diem_ren_luyen: 85,
    },
  },
  {
    text: "Tôi có được học bổng khuyến khích không?",
    type: "logical",
    facts: {
      tin_chi_tich_luy: 122,
      diem_tb: 3.5,
      no_mon: false,
      hoan_thanh_tttn: true,
      diem_ren_luyen: 85,
    },
  },
];

export function ChatWindow() {
  const { messages, loading, error, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState("");
  const [factsModal, setFactsModal] = useState({ open: false, question: "", facts: null });
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = useCallback(
    (question = input, facts = null) => {
      const trimmed = question.trim();
      if (!trimmed || loading) return;

      sendMessage(trimmed, facts);
      setInput("");
      inputRef.current?.focus();
    },
    [input, loading, sendMessage]
  );

  const openFactsForInput = () => {
    if (!input.trim() || loading) return;
    setFactsModal({ open: true, question: input.trim(), facts: null });
  };

  const handleDemoClick = (demo) => {
    if (loading) return;

    if (demo.facts) {
      setFactsModal({ open: true, question: demo.text, facts: demo.facts });
      return;
    }

    handleSend(demo.text, null);
  };

  const handleFactsSubmit = (facts) => {
    handleSend(factsModal.question, facts);
    setFactsModal({ open: false, question: "", facts: null });
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
        display: "flex",
        flexDirection: "column",
        height: "100dvh",
        maxWidth: 780,
        margin: "0 auto",
        fontFamily: "'Segoe UI', system-ui, -apple-system, BlinkMacSystemFont, sans-serif",
        background: "#FAFAFA",
        color: "#111",
      }}
    >
      <header
        style={{
          padding: "14px 20px",
          borderBottom: "1px solid #E8E8E8",
          background: "#FFF",
          display: "flex",
          alignItems: "center",
          gap: 12,
          flexShrink: 0,
        }}
      >
        <div
          style={{
            width: 38,
            height: 38,
            borderRadius: "50%",
            background: "#534AB7",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#FFF",
            fontWeight: 700,
            fontSize: 15,
            flexShrink: 0,
          }}
        >
          Q
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: 15, color: "#111" }}>QA Quy chế HCMUS</div>
          <div style={{ fontSize: 12, color: "#777", marginTop: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            RAG + Z3 Solver · Trả lời có trích dẫn điều khoản
          </div>
        </div>
        <StatusDot />
        <button onClick={clearChat} style={secondaryButtonStyle}>
          Xóa
        </button>
      </header>

      <main
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        {messages.length === 0 && <EmptyState demos={DEMO_QUESTIONS} onSelect={handleDemoClick} />}

        {messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))}

        {loading && <TypingIndicator />}

        {error && (
          <div
            style={{
              background: "#FAECE7",
              color: "#712B13",
              padding: "10px 14px",
              borderRadius: 8,
              fontSize: 13,
              border: "1px solid #F0997B",
              marginTop: 8,
            }}
          >
            {error}
          </div>
        )}

        <div ref={bottomRef} />
      </main>

      <footer
        style={{
          padding: "12px 16px",
          borderTop: "1px solid #E8E8E8",
          background: "#FFF",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi về quy chế học vụ..."
            rows={2}
            style={{
              flex: 1,
              minWidth: 0,
              resize: "none",
              border: "1px solid #DDD",
              borderRadius: 8,
              padding: "10px 12px",
              fontSize: 14,
              fontFamily: "inherit",
              outline: "none",
              lineHeight: 1.5,
              background: "#F8F8F8",
            }}
            onFocus={(event) => (event.currentTarget.style.borderColor = "#534AB7")}
            onBlur={(event) => (event.currentTarget.style.borderColor = "#DDD")}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <button onClick={openFactsForInput} disabled={loading || !input.trim()} style={factsButtonStyle}>
              Thông tin
            </button>
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              style={{
                ...sendButtonStyle,
                background: input.trim() && !loading ? "#534AB7" : "#E0DEFF",
                color: input.trim() && !loading ? "#FFF" : "#756FC0",
                cursor: input.trim() && !loading ? "pointer" : "default",
              }}
            >
              {loading ? "..." : "Gửi"}
            </button>
          </div>
        </div>
        <div style={{ fontSize: 11, color: "#AAA", marginTop: 6, textAlign: "center" }}>
          Enter để gửi · Shift+Enter xuống dòng
        </div>
      </footer>

      <UserFactsModal
        open={factsModal.open}
        question={factsModal.question}
        initialFacts={factsModal.facts}
        onClose={() => setFactsModal({ open: false, question: "", facts: null })}
        onSubmit={handleFactsSubmit}
      />
    </div>
  );
}

function StatusDot() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5, flexShrink: 0 }}>
      <div
        style={{
          width: 7,
          height: 7,
          borderRadius: "50%",
          background: "#1D9E75",
          animation: "pulse 2s infinite",
        }}
      />
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}`}</style>
      <span style={{ fontSize: 11, color: "#1D9E75", fontWeight: 600 }}>Online</span>
    </div>
  );
}

function EmptyState({ demos, onSelect }) {
  return (
    <div style={{ textAlign: "center", paddingTop: 28 }}>
      <div style={{ fontWeight: 700, fontSize: 16, color: "#222", marginBottom: 5 }}>
        Hỏi bất kỳ điều gì về quy chế HCMUS
      </div>
      <div style={{ fontSize: 13, color: "#777", marginBottom: 22 }}>
        Câu trả lời có trích dẫn điều khoản · Xác minh bằng Z3 Solver
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, maxWidth: 540, margin: "0 auto" }}>
        {demos.map((demo) => (
          <button
            key={demo.text}
            onClick={() => onSelect(demo)}
            style={{
              textAlign: "left",
              padding: "11px 14px",
              borderRadius: 8,
              border: "1px solid #E0E0E0",
              cursor: "pointer",
              background: "#FFF",
              fontSize: 13,
              color: "#333",
              display: "flex",
              alignItems: "center",
              gap: 10,
              lineHeight: 1.45,
            }}
            onMouseEnter={(event) => {
              event.currentTarget.style.background = "#F4F3FF";
              event.currentTarget.style.borderColor = "#AFA9EC";
            }}
            onMouseLeave={(event) => {
              event.currentTarget.style.background = "#FFF";
              event.currentTarget.style.borderColor = "#E0E0E0";
            }}
          >
            <span
              style={{
                fontSize: 10,
                fontWeight: 700,
                padding: "2px 7px",
                borderRadius: 999,
                flexShrink: 0,
                ...(demo.type === "logical"
                  ? { background: "#EEEDFE", color: "#3C3489" }
                  : demo.type === "procedural"
                    ? { background: "#E1F5EE", color: "#085041" }
                    : { background: "#F1EFE8", color: "#444441" }),
              }}
            >
              {demo.type === "logical" ? "Z3" : demo.type === "procedural" ? "Quy trình" : "Tra cứu"}
            </span>
            <span>{demo.text}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div style={{ display: "flex", justifyContent: "flex-start", padding: "4px 0" }}>
      <div
        style={{
          background: "#F0F0F0",
          borderRadius: "16px 16px 16px 4px",
          padding: "12px 16px",
          display: "flex",
          gap: 5,
          alignItems: "center",
        }}
      >
        {[0, 1, 2].map((index) => (
          <div
            key={index}
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "#999",
              animation: `bounce 1.2s ease-in-out ${index * 0.15}s infinite`,
            }}
          />
        ))}
        <style>{`@keyframes bounce{0%,80%,100%{transform:scale(0.8);opacity:.6}40%{transform:scale(1.1);opacity:1}}`}</style>
      </div>
    </div>
  );
}

const secondaryButtonStyle = {
  fontSize: 12,
  color: "#666",
  border: "1px solid #DDD",
  borderRadius: 8,
  padding: "6px 10px",
  cursor: "pointer",
  background: "none",
  flexShrink: 0,
};

const factsButtonStyle = {
  padding: "8px 12px",
  background: "#FFF",
  color: "#534AB7",
  border: "1px solid #C8C4F8",
  borderRadius: 8,
  cursor: "pointer",
  fontSize: 12,
  fontWeight: 600,
  whiteSpace: "nowrap",
};

const sendButtonStyle = {
  padding: "10px 18px",
  border: "none",
  borderRadius: 8,
  fontSize: 14,
  fontWeight: 700,
  transition: "all .15s",
  whiteSpace: "nowrap",
};
