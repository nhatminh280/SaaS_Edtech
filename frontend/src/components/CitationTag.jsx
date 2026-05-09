export function CitationTag({ citation }) {
  return (
    <span
      title={citation.noi_dung}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        background: "#eef2ff",
        color: "#3730a3",
        fontSize: 11,
        fontWeight: 600,
        padding: "3px 8px",
        borderRadius: 999,
        cursor: "help",
        border: "1px solid #c7d2fe",
      }}
    >
      {citation.dieu_khoan}
    </span>
  );
}
