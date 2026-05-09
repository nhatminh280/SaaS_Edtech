import { useState } from "react";

export function CitationTag({ citation }) {
  const [showTooltip, setShowTooltip] = useState(false);
  const label = citation.dieu_khoan || "Trích dẫn";
  const preview = citation.noi_dung ? citation.noi_dung.slice(0, 220) : "";
  const Tag = citation.pdf_url ? "a" : "button";
  const linkProps = citation.pdf_url
    ? {
        href: citation.pdf_url,
        target: "_blank",
        rel: "noreferrer",
        title: citation.page ? `Mở PDF trang ${citation.page}` : "Mở PDF nguồn",
      }
    : { type: "button" };

  return (
    <span style={{ position: "relative", display: "inline-flex" }}>
      <Tag
        {...linkProps}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        onClick={(event) => {
          if (!citation.pdf_url) {
            event.preventDefault();
            setShowTooltip((value) => !value);
          }
        }}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 4,
          background: "#EEEDFE",
          color: "#3C3489",
          fontSize: 11,
          fontWeight: 600,
          padding: "3px 9px",
          borderRadius: 999,
          cursor: "pointer",
          border: "1px solid #AFA9EC",
          fontFamily: "inherit",
          lineHeight: 1.4,
          textDecoration: "none",
        }}
      >
        {label}
        {citation.page ? <span style={{ opacity: 0.75 }}>tr. {citation.page}</span> : null}
      </Tag>

      {showTooltip && preview && (
        <span
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: 0,
            background: "#1A1A2E",
            color: "#E8E8F0",
            padding: "10px 12px",
            borderRadius: 8,
            fontSize: 12,
            lineHeight: 1.55,
            width: 280,
            maxWidth: "calc(100vw - 40px)",
            zIndex: 20,
            boxShadow: "0 8px 24px rgba(0,0,0,0.22)",
            pointerEvents: "none",
            textAlign: "left",
          }}
        >
          <span style={{ display: "block", fontWeight: 700, marginBottom: 4, color: "#C8C4F8" }}>{label}</span>
          <span style={{ display: "block", opacity: 0.9 }}>{preview}{citation.noi_dung.length > 220 ? "..." : ""}</span>
          {citation.nguon && (
            <span style={{ display: "block", fontSize: 10, opacity: 0.6, marginTop: 6 }}>Nguồn: {citation.nguon}</span>
          )}
          {citation.pdf_url && (
            <span style={{ display: "block", fontSize: 10, opacity: 0.7, marginTop: 4 }}>
              Click để mở PDF{citation.page ? ` trang ${citation.page}` : ""}
            </span>
          )}
        </span>
      )}
    </span>
  );
}
