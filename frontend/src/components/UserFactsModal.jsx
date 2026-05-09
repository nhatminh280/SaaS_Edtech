import { useEffect, useState } from "react";

const DEFAULT_FACTS = {
  tin_chi_tich_luy: 122,
  diem_tb: 2.75,
  no_mon: false,
  hoan_thanh_tttn: true,
  diem_ren_luyen: 85,
};

export function UserFactsModal({ open, initialFacts, question, onClose, onSubmit }) {
  const [facts, setFacts] = useState(DEFAULT_FACTS);

  useEffect(() => {
    if (open) {
      setFacts({ ...DEFAULT_FACTS, ...(initialFacts || {}) });
    }
  }, [initialFacts, open]);

  if (!open) return null;

  const update = (key, value) => setFacts((prev) => ({ ...prev, [key]: value }));

  const submit = (event) => {
    event.preventDefault();
    onSubmit({
      tin_chi_tich_luy: Number(facts.tin_chi_tich_luy) || 0,
      diem_tb: Number(facts.diem_tb) || 0,
      no_mon: Boolean(facts.no_mon),
      hoan_thanh_tttn: Boolean(facts.hoan_thanh_tttn),
      diem_ren_luyen: Number(facts.diem_ren_luyen) || 0,
    });
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Thông tin sinh viên"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(17, 24, 39, 0.42)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 16,
        zIndex: 50,
      }}
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <form
        onSubmit={submit}
        style={{
          width: "min(460px, 100%)",
          background: "#FFF",
          borderRadius: 8,
          border: "1px solid #E8E8E8",
          boxShadow: "0 18px 44px rgba(15, 23, 42, 0.22)",
          padding: 18,
          color: "#111",
        }}
      >
        <div style={{ fontWeight: 700, fontSize: 16 }}>Thông tin sinh viên</div>
        <div style={{ color: "#666", fontSize: 13, lineHeight: 1.5, marginTop: 4 }}>
          {question || "Dùng cho câu hỏi cần suy luận logic bằng Z3."}
        </div>

        <div style={{ display: "grid", gap: 12, marginTop: 16 }}>
          <NumberField
            label="Tín chỉ tích lũy"
            value={facts.tin_chi_tich_luy}
            min={0}
            onChange={(value) => update("tin_chi_tich_luy", value)}
          />
          <NumberField
            label="Điểm trung bình"
            value={facts.diem_tb}
            min={0}
            max={4}
            step="0.01"
            onChange={(value) => update("diem_tb", value)}
          />
          <NumberField
            label="Điểm rèn luyện"
            value={facts.diem_ren_luyen}
            min={0}
            max={100}
            onChange={(value) => update("diem_ren_luyen", value)}
          />
          <label style={checkboxStyle}>
            <input
              type="checkbox"
              checked={facts.no_mon}
              onChange={(event) => update("no_mon", event.target.checked)}
            />
            Còn nợ môn
          </label>
          <label style={checkboxStyle}>
            <input
              type="checkbox"
              checked={facts.hoan_thanh_tttn}
              onChange={(event) => update("hoan_thanh_tttn", event.target.checked)}
            />
            Hoàn thành thực tập tốt nghiệp
          </label>
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 18 }}>
          <button type="button" onClick={onClose} style={secondaryButtonStyle}>
            Hủy
          </button>
          <button type="submit" style={primaryButtonStyle}>
            Gửi kèm thông tin
          </button>
        </div>
      </form>
    </div>
  );
}

function NumberField({ label, value, onChange, min, max, step = "1" }) {
  return (
    <label style={{ display: "grid", gap: 5, fontSize: 13, color: "#444" }}>
      {label}
      <input
        type="number"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        style={{
          border: "1px solid #DDD",
          borderRadius: 8,
          padding: "9px 10px",
          fontSize: 14,
          fontFamily: "inherit",
        }}
      />
    </label>
  );
}

const checkboxStyle = {
  display: "flex",
  gap: 8,
  alignItems: "center",
  color: "#444",
  fontSize: 13,
};

const primaryButtonStyle = {
  border: "none",
  borderRadius: 8,
  background: "#534AB7",
  color: "#FFF",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  padding: "9px 12px",
};

const secondaryButtonStyle = {
  border: "1px solid #DDD",
  borderRadius: 8,
  background: "#FFF",
  color: "#444",
  cursor: "pointer",
  fontSize: 13,
  fontWeight: 600,
  padding: "9px 12px",
};
