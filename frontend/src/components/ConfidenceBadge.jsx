export function ConfidenceBadge({ confidence, z3Result, questionType }) {
  const pct = Math.round((confidence || 0) * 100);

  const confStyle =
    pct >= 85
      ? { background: "#E1F5EE", color: "#085041" }
      : pct >= 65
        ? { background: "#FAEEDA", color: "#633806" }
        : { background: "#FAECE7", color: "#712B13" };

  return (
    <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginTop: 10 }}>
      <span
        style={{
          background: confStyle.background,
          color: confStyle.color,
          fontSize: 11,
          fontWeight: 600,
          padding: "3px 10px",
          borderRadius: 999,
        }}
      >
        {pct}% tin cậy
      </span>

      {z3Result && (
        <span
          title={z3Result.explanation}
          style={{
            background: z3Result.verified ? "#E1F5EE" : "#FAECE7",
            color: z3Result.verified ? "#085041" : "#712B13",
            fontSize: 11,
            fontWeight: 600,
            padding: "3px 10px",
            borderRadius: 999,
            border: `1px solid ${z3Result.verified ? "#5DCAA5" : "#F0997B"}`,
          }}
        >
          {z3Result.verified ? "Z3 xác minh" : "Z3 chưa đủ điều kiện"}
        </span>
      )}

      {questionType && (
        <span
          style={{
            background: "#F1EFE8",
            color: "#5F5E5A",
            fontSize: 10,
            fontWeight: 600,
            padding: "2px 8px",
            borderRadius: 999,
          }}
        >
          {questionType === "logical" ? "Logic" : questionType === "procedural" ? "Quy trình" : "Tra cứu"}
        </span>
      )}
    </div>
  );
}
