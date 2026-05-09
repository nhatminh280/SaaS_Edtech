export function ConfidenceBadge({ confidence, z3Result }) {
  const pct = Math.round(confidence * 100);
  const color = pct >= 80 ? "#047857" : pct >= 60 ? "#a16207" : "#b91c1c";
  const background = pct >= 80 ? "#d1fae5" : pct >= 60 ? "#fef3c7" : "#fee2e2";

  return (
    <div style={{ display: "flex", flexWrap: "wrap", gap: 8, alignItems: "center", marginTop: 10 }}>
      <span
        style={{
          background,
          color,
          fontSize: 11,
          fontWeight: 600,
          padding: "3px 9px",
          borderRadius: 999,
        }}
      >
        {pct}% tin cậy
      </span>
      {z3Result && (
        <span
          style={{
            background: z3Result.verified ? "#d1fae5" : "#fee2e2",
            color: z3Result.verified ? "#065f46" : "#991b1b",
            fontSize: 11,
            fontWeight: 600,
            padding: "3px 9px",
            borderRadius: 999,
          }}
        >
          {z3Result.verified ? "Z3 xác minh" : "Z3 chưa đủ điều kiện"}
        </span>
      )}
    </div>
  );
}
