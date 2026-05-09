import { CitationTag } from "./CitationTag";
import { ConfidenceBadge } from "./ConfidenceBadge";

export function MessageBubble({ message }) {
  if (message.role === "user") {
    return (
      <div style={{ display: "flex", justifyContent: "flex-end", margin: "4px 0" }}>
        <div
          style={{
            background: "#534AB7",
            color: "#FFF",
            borderRadius: "18px 18px 4px 18px",
            padding: "10px 16px",
            maxWidth: "78%",
            fontSize: 14,
            lineHeight: 1.55,
            overflowWrap: "anywhere",
          }}
        >
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", justifyContent: "flex-start", margin: "4px 0" }}>
      <div
        style={{
          background: "#FFF",
          border: "1px solid #EBEBEB",
          borderRadius: "18px 18px 18px 4px",
          padding: "12px 16px",
          maxWidth: "82%",
          fontSize: 14,
          lineHeight: 1.65,
          color: "#1A1A1A",
          overflowWrap: "anywhere",
          boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
        }}
      >
        <div style={{ whiteSpace: "pre-wrap" }}>{message.content || "Không có câu trả lời."}</div>

        {message.citations?.length > 0 && (
          <div
            style={{
              marginTop: 12,
              paddingTop: 10,
              borderTop: "1px solid #F0F0F0",
              display: "flex",
              flexWrap: "wrap",
              gap: 6,
            }}
          >
            <span style={{ fontSize: 11, color: "#999", alignSelf: "center" }}>Trích dẫn:</span>
            {message.citations.map((citation, index) => (
              <CitationTag key={`${citation.chunk_id || citation.dieu_khoan}-${index}`} citation={citation} />
            ))}
          </div>
        )}

        {message.confidence !== undefined && (
          <ConfidenceBadge
            confidence={message.confidence}
            z3Result={message.z3Result}
            questionType={message.questionType}
          />
        )}

        {message.processingTimeMs !== undefined && (
          <div style={{ fontSize: 10, color: "#AAA", marginTop: 8, textAlign: "right" }}>
            {message.processingTimeMs}ms
          </div>
        )}
      </div>
    </div>
  );
}
