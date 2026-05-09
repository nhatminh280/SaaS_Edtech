"""
Seed a small local demo knowledge base for Phase 3 smoke tests.

This is not a replacement for ingesting the official regulation PDF. It only
provides enough demo clauses for the five scripted questions when no PDF data is
available locally.

Usage:
    EMBEDDING_PROVIDER=hash python3 scripts/seed_demo_data.py --reset
"""

import argparse
import hashlib
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.ingest import get_chroma_collection  # noqa: E402


DEMO_CHUNKS = [
    {
        "dieu_khoan": "Điều 22 - Cảnh cáo học vụ",
        "chuong": "Demo quy chế học vụ",
        "nguon": "demo_phase3_seed",
        "text": (
            "Điều 22 - Cảnh cáo học vụ. Sinh viên bị cảnh cáo học vụ nếu điểm "
            "trung bình học kỳ dưới 1.0 hoặc điểm trung bình tích lũy dưới 1.2. "
            "Sinh viên thuộc diện cảnh cáo phải liên hệ cố vấn học tập để lập kế "
            "hoạch học tập cải thiện."
        ),
    },
    {
        "dieu_khoan": "Điều 30, Khoản 1 - Điều kiện tốt nghiệp",
        "chuong": "Demo quy chế học vụ",
        "nguon": "demo_phase3_seed",
        "text": (
            "Điều 30, Khoản 1 - Điều kiện tốt nghiệp. Sinh viên được xét tốt "
            "nghiệp khi tích lũy tối thiểu 120 tín chỉ, điểm trung bình tích lũy "
            "từ 2.0 trở lên, không còn nợ môn học và hoàn thành thực tập hoặc đồ "
            "án tốt nghiệp theo chương trình đào tạo."
        ),
    },
    {
        "dieu_khoan": "Điều 35 - Bảo lưu kết quả học tập",
        "chuong": "Demo quy chế học vụ",
        "nguon": "demo_phase3_seed",
        "text": (
            "Điều 35 - Bảo lưu kết quả học tập. Sinh viên muốn bảo lưu phải nộp "
            "đơn theo mẫu cho phòng đào tạo, kèm minh chứng lý do hợp lệ. Hồ sơ "
            "được khoa xác nhận trước khi phòng đào tạo ra quyết định. Thời gian "
            "bảo lưu được tính theo từng học kỳ."
        ),
    },
    {
        "dieu_khoan": "Điều 25 - Học bổng khuyến khích",
        "chuong": "Demo quy chế học vụ",
        "nguon": "demo_phase3_seed",
        "text": (
            "Điều 25 - Học bổng khuyến khích học tập. Sinh viên được xét học "
            "bổng khi điểm trung bình học kỳ hoặc tích lũy đạt từ 3.2, điểm rèn "
            "luyện đạt từ 80, không nợ môn và không bị kỷ luật trong học kỳ xét."
        ),
    },
    {
        "dieu_khoan": "Điều 10 - Đăng ký học phần",
        "chuong": "Demo quy chế học vụ",
        "nguon": "demo_phase3_seed",
        "text": (
            "Điều 10 - Đăng ký học phần. Sinh viên được đăng ký học phần trong "
            "thời gian quy định nếu đã hoàn thành học phần tiên quyết và không "
            "thuộc diện bị cấm đăng ký học phần."
        ),
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete existing collection contents first")
    args = parser.parse_args()

    load_dotenv()
    collection = get_chroma_collection()

    if args.reset:
        existing = collection.get()
        ids = existing.get("ids", [])
        if ids:
            collection.delete(ids=ids)

    ids = [hashlib.md5(chunk["text"].encode("utf-8")).hexdigest()[:12] for chunk in DEMO_CHUNKS]
    collection.upsert(
        ids=ids,
        documents=[chunk["text"] for chunk in DEMO_CHUNKS],
        metadatas=[
            {
                "dieu_khoan": chunk["dieu_khoan"],
                "chuong": chunk["chuong"],
                "nguon": chunk["nguon"],
            }
            for chunk in DEMO_CHUNKS
        ],
    )

    print(f"Seeded {len(DEMO_CHUNKS)} demo chunks into collection '{collection.name}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
