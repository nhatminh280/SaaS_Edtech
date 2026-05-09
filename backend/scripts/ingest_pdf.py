"""
Ingest a PDF into ChromaDB.
Usage: python scripts/ingest_pdf.py --pdf data/quy_che.pdf
"""

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag.ingest import ingest_pdf  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf", required=True, help="Path đến file PDF quy chế")
    parser.add_argument("--reset", action="store_true", help="Xóa collection cũ trước khi ingest")
    args = parser.parse_args()

    pdf_path = args.pdf
    if not Path(pdf_path).exists():
        print(f"File không tồn tại: {pdf_path}")
        sys.exit(1)

    print(f"Ingesting: {pdf_path}")
    total = ingest_pdf(pdf_path, reset=args.reset)
    print(f"Đã ingest {total} chunks vào ChromaDB")


if __name__ == "__main__":
    main()
