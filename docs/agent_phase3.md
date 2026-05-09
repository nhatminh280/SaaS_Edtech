# Agent Instructions — Phase 3: Connect & Demo (2h–3h15')

> Wire frontend ↔ backend, smoke test 5 câu demo thật, fix bug critical, deploy live URL.
> Phase 1 + 2 phải xong trước. Không thêm feature mới trong phase này — chỉ kết nối và fix.

---

## Mục tiêu Phase 3

Sau phase này:

1. Frontend gọi được backend thật, không còn mock data
2. Citation highlight hiển thị đúng trong chat bubble
3. Z3 badge hiện ra khi backend trả `z3_result`
4. 5 câu demo chạy ổn định, không crash
5. Live URL qua ngrok / Railway cho giám khảo test trực tiếp
6. User facts input UI (cho câu hỏi logic cần thông tin cá nhân)

---

## 3.1 Frontend hoàn chỉnh — `src/components/ChatWindow.jsx`

> Bổ sung: user_facts dialog, loading skeleton, error boundary, scroll to bottom.

```jsx
import { useState, useRef, useEffect, useCallback } from "react";
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
      tin_chi_tich_luy: 118,
      diem_tb: 2.65,
      no_mon: false,
      hoan_thanh_tttn: true,
    },
  },
  {
    text: "Tôi có được học bổng khuyến khích không?",
    type: "logical",
    facts: {
      diem_tb: 3.45,
      no_mon: false,
      diem_ren_luyen: 82,
    },
  },
];

export function ChatWindow() {
  const { messages, loading, error, sendMessage, clearChat } = useChat();
  const [input, setInput] = useState("");
  const [showFactsModal, setShowFactsModal] = useState(false);
  const [pendingQuestion, setPendingQuestion] = useState(null);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = useCallback(
    (question = input, facts = null) => {
      if (!question.trim() || loading) return;
      sendMessage(question.trim(), facts);
      setInput("");
      inputRef.current?.focus();
    },
    [input, loading, sendMessage]
  );

  const handleDemoClick = (demo) => {
    if (demo.facts) {
      // Câu hỏi logical → hỏi user có muốn dùng facts mẫu không
      sendMessage(demo.text, demo.facts);
    } else {
      sendMessage(demo.text, null);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100dvh",
        maxWidth: 760,
        margin: "0 auto",
        fontFamily: "'Segoe UI', system-ui, sans-serif",
        background: "#FAFAFA",
      }}
    >
      {/* Header */}
      <header
        style={{
          padding: "14px 20px",
          borderBottom: "0.5px solid #E8E8E8",
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
          <div style={{ fontWeight: 600, fontSize: 14, color: "#111" }}>
            QA Quy chế HCMUS
          </div>
          <div style={{ fontSize: 11, color: "#888", marginTop: 1 }}>
            RAG + Z3 Solver · Trả lời có trích dẫn điều khoản
          </div>
        </div>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <StatusDot />
          <button
            onClick={clearChat}
            style={{
              fontSize: 12,
              color: "#666",
              border: "0.5px solid #DDD",
              borderRadius: 8,
              padding: "5px 12px",
              cursor: "pointer",
              background: "none",
            }}
          >
            Xóa
          </button>
        </div>
      </header>

      {/* Messages */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        {messages.length === 0 && (
          <EmptyState demos={DEMO_QUESTIONS} onSelect={handleDemoClick} />
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {loading && <TypingIndicator />}

        {error && (
          <div
            style={{
              background: "#FAECE7",
              color: "#712B13",
              padding: "10px 14px",
              borderRadius: 12,
              fontSize: 13,
              border: "0.5px solid #F0997B",
            }}
          >
            ❌ {error}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div
        style={{
          padding: "12px 16px",
          borderTop: "0.5px solid #E8E8E8",
          background: "#FFF",
          flexShrink: 0,
        }}
      >
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Nhập câu hỏi về quy chế học vụ..."
            rows={2}
            style={{
              flex: 1,
              resize: "none",
              border: "0.5px solid #DDD",
              borderRadius: 12,
              padding: "10px 14px",
              fontSize: 14,
              fontFamily: "inherit",
              outline: "none",
              lineHeight: 1.5,
              background: "#F8F8F8",
              transition: "border-color .15s",
            }}
            onFocus={(e) => (e.target.style.borderColor = "#534AB7")}
            onBlur={(e) => (e.target.style.borderColor = "#DDD")}
          />
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              style={{
                padding: "10px 20px",
                background: input.trim() && !loading ? "#534AB7" : "#E0DEFF",
                color: input.trim() && !loading ? "#FFF" : "#9B93DB",
                border: "none",
                borderRadius: 12,
                cursor: input.trim() && !loading ? "pointer" : "default",
                fontSize: 14,
                fontWeight: 500,
                transition: "all .15s",
                whiteSpace: "nowrap",
              }}
            >
              {loading ? "..." : "Gửi ↗"}
            </button>
          </div>
        </div>
        <div style={{ fontSize: 11, color: "#AAA", marginTop: 6, textAlign: "center" }}>
          Enter để gửi · Shift+Enter xuống dòng
        </div>
      </div>
    </div>
  );
}

function StatusDot() {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
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
      <span style={{ fontSize: 11, color: "#1D9E75", fontWeight: 500 }}>Online</span>
    </div>
  );
}

function EmptyState({ demos, onSelect }) {
  return (
    <div style={{ textAlign: "center", paddingTop: 32 }}>
      <div style={{ fontSize: 36, marginBottom: 8 }}>📋</div>
      <div style={{ fontWeight: 600, fontSize: 15, color: "#222", marginBottom: 4 }}>
        Hỏi bất kỳ điều gì về quy chế HCMUS
      </div>
      <div style={{ fontSize: 13, color: "#888", marginBottom: 24 }}>
        Câu trả lời có trích dẫn điều khoản · Xác minh bằng Z3 Solver
      </div>
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 8,
          maxWidth: 520,
          margin: "0 auto",
        }}
      >
        {demos.map((demo, i) => (
          <button
            key={i}
            onClick={() => onSelect(demo)}
            style={{
              textAlign: "left",
              padding: "11px 16px",
              borderRadius: 12,
              border: "0.5px solid #E0E0E0",
              cursor: "pointer",
              background: "#FFF",
              fontSize: 13,
              color: "#333",
              display: "flex",
              alignItems: "center",
              gap: 10,
              transition: "background .12s, border-color .12s",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "#F4F3FF";
              e.currentTarget.style.borderColor = "#AFA9EC";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "#FFF";
              e.currentTarget.style.borderColor = "#E0E0E0";
            }}
          >
            <span
              style={{
                fontSize: 10,
                fontWeight: 600,
                padding: "2px 7px",
                borderRadius: 100,
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
            {demo.text}
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
        {[0, 1, 2].map((i) => (
          <div
            key={i}
            style={{
              width: 7,
              height: 7,
              borderRadius: "50%",
              background: "#999",
              animation: `bounce 1.2s ease-in-out ${i * 0.15}s infinite`,
            }}
          />
        ))}
        <style>{`@keyframes bounce{0%,80%,100%{transform:scale(0.8);opacity:.6}40%{transform:scale(1.1);opacity:1}}`}</style>
      </div>
    </div>
  );
}
```

---

## 3.2 MessageBubble hoàn chỉnh — `src/components/MessageBubble.jsx`

```jsx
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
          border: "0.5px solid #EBEBEB",
          borderRadius: "18px 18px 18px 4px",
          padding: "12px 16px",
          maxWidth: "82%",
          fontSize: 14,
          lineHeight: 1.65,
          boxShadow: "0 1px 4px rgba(0,0,0,0.04)",
        }}
      >
        {/* Answer text — render newlines */}
        <div style={{ whiteSpace: "pre-wrap", color: "#1A1A1A" }}>
          {message.content}
        </div>

        {/* Citations */}
        {message.citations?.length > 0 && (
          <div
            style={{
              marginTop: 12,
              paddingTop: 10,
              borderTop: "0.5px solid #F0F0F0",
              display: "flex",
              flexWrap: "wrap",
              gap: 6,
            }}
          >
            <span style={{ fontSize: 11, color: "#AAA", alignSelf: "center" }}>
              Trích dẫn:
            </span>
            {message.citations.map((c, i) => (
              <CitationTag key={i} citation={c} />
            ))}
          </div>
        )}

        {/* Confidence + Z3 */}
        {message.confidence !== undefined && (
          <ConfidenceBadge
            confidence={message.confidence}
            z3Result={message.z3Result}
            questionType={message.questionType}
          />
        )}

        {/* Processing time */}
        {message.processingTimeMs !== undefined && (
          <div
            style={{
              fontSize: 10,
              color: "#C0C0C0",
              marginTop: 8,
              textAlign: "right",
            }}
          >
            {message.processingTimeMs}ms
          </div>
        )}
      </div>
    </div>
  );
}
```

---

## 3.3 CitationTag với tooltip — `src/components/CitationTag.jsx`

```jsx
import { useState } from "react";

export function CitationTag({ citation }) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <button
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip((v) => !v)}
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 4,
          background: "#EEEDFE",
          color: "#3C3489",
          fontSize: 11,
          fontWeight: 500,
          padding: "3px 10px",
          borderRadius: 100,
          cursor: "pointer",
          border: "0.5px solid #AFA9EC",
          transition: "background .12s",
        }}
        onMouseEnterCapture={(e) => (e.currentTarget.style.background = "#DDD9FC")}
        onMouseLeaveCapture={(e) => (e.currentTarget.style.background = "#EEEDFE")}
      >
        📎 {citation.dieu_khoan}
      </button>

      {showTooltip && citation.noi_dung && (
        <div
          style={{
            position: "absolute",
            bottom: "calc(100% + 8px)",
            left: 0,
            background: "#1A1A2E",
            color: "#E8E8F0",
            padding: "10px 14px",
            borderRadius: 10,
            fontSize: 12,
            lineHeight: 1.55,
            width: 280,
            zIndex: 100,
            boxShadow: "0 4px 20px rgba(0,0,0,0.2)",
            pointerEvents: "none",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4, color: "#C8C4F8" }}>
            {citation.dieu_khoan}
          </div>
          <div style={{ opacity: 0.85 }}>{citation.noi_dung.slice(0, 200)}...</div>
          <div style={{ fontSize: 10, opacity: 0.5, marginTop: 6 }}>
            Nguồn: {citation.nguon}
          </div>
        </div>
      )}
    </div>
  );
}
```

---

## 3.4 ConfidenceBadge hoàn chỉnh — `src/components/ConfidenceBadge.jsx`

```jsx
export function ConfidenceBadge({ confidence, z3Result, questionType }) {
  const pct = Math.round((confidence || 0) * 100);

  const confStyle =
    pct >= 85
      ? { bg: "#E1F5EE", color: "#085041", label: `${pct}% tin cậy` }
      : pct >= 65
      ? { bg: "#FAEEDA", color: "#633806", label: `${pct}% tin cậy` }
      : { bg: "#FAECE7", color: "#712B13", label: `${pct}% tin cậy` };

  return (
    <div
      style={{
        display: "flex",
        gap: 6,
        alignItems: "center",
        flexWrap: "wrap",
        marginTop: 10,
      }}
    >
      <span
        style={{
          background: confStyle.bg,
          color: confStyle.color,
          fontSize: 11,
          fontWeight: 500,
          padding: "3px 10px",
          borderRadius: 100,
        }}
      >
        {confStyle.label}
      </span>

      {z3Result && (
        <span
          style={{
            background: z3Result.verified ? "#E1F5EE" : "#FAECE7",
            color: z3Result.verified ? "#085041" : "#712B13",
            fontSize: 11,
            fontWeight: 500,
            padding: "3px 10px",
            borderRadius: 100,
            border: `0.5px solid ${z3Result.verified ? "#5DCAA5" : "#F0997B"}`,
          }}
          title={z3Result.explanation}
        >
          {z3Result.verified ? "✓ Z3 xác minh" : "✗ Z3: chưa đủ điều kiện"}
        </span>
      )}

      {questionType && (
        <span
          style={{
            background: "#F1EFE8",
            color: "#5F5E5A",
            fontSize: 10,
            padding: "2px 8px",
            borderRadius: 100,
          }}
        >
          {questionType === "logical"
            ? "🔢 Logic"
            : questionType === "procedural"
            ? "📋 Quy trình"
            : "🔍 Tra cứu"}
        </span>
      )}
    </div>
  );
}
```

---

## 3.5 Deploy nhanh — các option theo thứ tự ưu tiên

### Option A: ngrok (nhanh nhất, 5 phút)

```bash
# Terminal 1: backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Terminal 2: ngrok
ngrok http 8000
# → Copy URL dạng https://xxxx.ngrok-free.app

# Terminal 3: frontend — update VITE_API_URL
cd frontend
VITE_API_URL=https://xxxx.ngrok-free.app/api/v1 npm run dev
```

### Option B: Railway (free tier, có persistent URL)

```bash
# Cài Railway CLI
npm install -g @railway/cli
railway login

cd backend
railway init
railway up

# Set env vars
railway variables set OPENAI_API_KEY=sk-...
railway variables set LLM_PROVIDER=openai
# ... các biến khác từ .env.example
```

### Option C: Docker Compose local (demo tại chỗ)

```bash
# Từ project root
docker-compose up --build

# Backend: http://localhost:8000
# Frontend: http://localhost:5173
```

---

## 3.6 Smoke test script — `scripts/smoke_test.py`

```python
"""
Chạy 5 câu demo và in kết quả.
Usage: python3 scripts/smoke_test.py --url http://localhost:8000
"""
import httpx
import json
import sys
import argparse
import time

TEST_CASES = [
    {
        "name": "Factual: Cảnh cáo học vụ",
        "payload": {"question": "Sinh viên bị cảnh cáo học vụ khi nào?"},
        "expect_citation": True,
        "expect_z3": False,
    },
    {
        "name": "Factual: Điều kiện tốt nghiệp",
        "payload": {"question": "Điều kiện để được xét tốt nghiệp là gì?"},
        "expect_citation": True,
        "expect_z3": False,
    },
    {
        "name": "Procedural: Bảo lưu",
        "payload": {"question": "Quy trình xin bảo lưu kết quả học tập như thế nào?"},
        "expect_citation": True,
        "expect_z3": False,
    },
    {
        "name": "Logical + Z3: Tốt nghiệp",
        "payload": {
            "question": "Tôi có đủ điều kiện tốt nghiệp không?",
            "user_facts": {
                "tin_chi_tich_luy": 122,
                "diem_tb": 2.75,
                "no_mon": False,
                "hoan_thanh_tttn": True,
            },
        },
        "expect_citation": True,
        "expect_z3": True,
    },
    {
        "name": "Logical + Z3: Học bổng",
        "payload": {
            "question": "Tôi có được học bổng khuyến khích không?",
            "user_facts": {
                "diem_tb": 3.5,
                "no_mon": False,
                "diem_ren_luyen": 85,
            },
        },
        "expect_citation": True,
        "expect_z3": True,
    },
]


def run_tests(base_url: str):
    print(f"\n🧪 Smoke test: {base_url}\n{'='*50}")
    passed = 0
    failed = 0

    for i, tc in enumerate(TEST_CASES):
        print(f"\n[{i+1}/5] {tc['name']}")
        t0 = time.time()
        try:
            r = httpx.post(
                f"{base_url}/api/v1/ask",
                json=tc["payload"],
                timeout=30,
            )
            elapsed = int((time.time() - t0) * 1000)

            if r.status_code != 200:
                print(f"  ❌ HTTP {r.status_code}: {r.text[:100]}")
                failed += 1
                continue

            data = r.json()

            checks = []

            # Check answer not empty
            if data.get("answer"):
                checks.append("✓ answer")
            else:
                checks.append("✗ answer MISSING")

            # Check citations
            if tc["expect_citation"] and data.get("citations"):
                checks.append(f"✓ {len(data['citations'])} citations")
            elif tc["expect_citation"]:
                checks.append("⚠ citations empty")

            # Check Z3
            if tc["expect_z3"] and data.get("z3_result"):
                z3 = data["z3_result"]
                checks.append(f"✓ Z3 {'✓' if z3['verified'] else '✗'}")
            elif tc["expect_z3"]:
                checks.append("⚠ z3_result missing")

            # Confidence
            conf = data.get("confidence", 0)
            checks.append(f"conf={conf:.0%}")

            print(f"  {' · '.join(checks)} [{elapsed}ms]")
            print(f"  → {data['answer'][:120]}...")
            passed += 1

        except Exception as e:
            print(f"  ❌ Exception: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"{'✅' if failed == 0 else '⚠'} {passed}/5 passed, {failed} failed\n")
    return failed == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL của backend")
    args = parser.parse_args()

    ok = run_tests(args.url)
    sys.exit(0 if ok else 1)
```

---

## 3.7 Frontend `vite.config.js` với proxy

```js
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Dev proxy: tránh CORS khi FE và BE chạy khác port
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
```

Khi dùng proxy, update `client.js`:

```js
// src/api/client.js — dùng proxy, không cần VITE_API_URL
const BASE_URL = "/api/v1";
```

---

## 3.8 Checklist demo live — chạy trước khi pitch

```bash
# 1. Health check
curl http://localhost:8000/api/v1/health
# → Phải thấy "status":"ok" và total_chunks > 0

# 2. Chạy smoke test
python3 scripts/smoke_test.py --url http://localhost:8000
# → 5/5 passed

# 3. Mở frontend trên browser
open http://localhost:5173

# 4. Test từng câu demo bằng tay, confirm:
#    - Citation tag hiện ra
#    - Z3 badge hiện cho câu hỏi logical
#    - Không có lỗi console

# 5. Test trên mobile (quan trọng cho demo)
# Dùng ngrok URL mở trên điện thoại
```

---

## Checklist Phase 3 Done ✅

- [ ] `smoke_test.py` chạy 5/5 passed
- [ ] Citation tooltip hiện khi hover trên desktop
- [ ] Z3 badge màu xanh/đỏ hiện đúng theo kết quả
- [ ] Loading animation (3 dots bounce) hiện khi đang xử lý
- [ ] 5 demo buttons ở empty state, click được
- [ ] Live URL (ngrok/Railway) accessible từ điện thoại
- [ ] Không có hardcode URL trong FE code (dùng env hoặc proxy)

---

*Sang Phase 4: UI polish, 5-slide pitch deck, rehearse 2 lần.*
