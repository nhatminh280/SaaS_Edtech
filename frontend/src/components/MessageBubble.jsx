import { CitationTag } from "./CitationTag";
import { ConfidenceBadge } from "./ConfidenceBadge";

export function MessageBubble({ message }) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 12 }}>
        <div
          style={{
            background: "#2563eb",
            color: "#fff",
            borderRadius: "14px 14px 4px 14px",
            padding: "10px 14px",
            maxWidth: "75%",
            fontSize: 14,
            lineHeight: 1.5,
            overflowWrap: "anywhere",
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
      <div
        style={{
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "14px 14px 14px 4px",
          padding: "12px 14px",
          maxWidth: "82%",
          fontSize: 14,
          lineHeight: 1.6,
          color: "#0f172a",
          overflowWrap: "anywhere",
        }}
      >
        <div style={{ whiteSpace: "pre-wrap" }}>{message.content}</div>

        {message.citations?.length > 0 && (
          <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginTop: 10 }}>
            {message.citations.map((citation, index) => (
              <CitationTag key={`${citation.chunk_id || citation.dieu_khoan}-${index}`} citation={citation} />
            ))}
          </div>
        )}

        {message.confidence !== undefined && (
          <ConfidenceBadge confidence={message.confidence} z3Result={message.z3Result} />
        )}

        {message.processingTimeMs !== undefined && (
          <div style={{ fontSize: 11, color: "#64748b", marginTop: 8 }}>{message.processingTimeMs}ms</div>
        )}
      </div>
    </div>
  );
}
