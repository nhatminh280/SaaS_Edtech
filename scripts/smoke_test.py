"""
Run the five Phase 3 demo questions against a backend URL.

Usage:
    python3 scripts/smoke_test.py --url http://localhost:8000
"""

import argparse
import sys
import time

import httpx


TEST_CASES = [
    {
        "name": "Factual: Canh cao hoc vu",
        "payload": {"question": "Sinh viên bị cảnh cáo học vụ khi nào?"},
        "expect_citation": True,
        "expect_z3": False,
    },
    {
        "name": "Factual: Dieu kien tot nghiep",
        "payload": {"question": "Điều kiện để được xét tốt nghiệp là gì?"},
        "expect_citation": True,
        "expect_z3": False,
    },
    {
        "name": "Procedural: Bao luu",
        "payload": {"question": "Quy trình xin bảo lưu kết quả học tập như thế nào?"},
        "expect_citation": True,
        "expect_z3": False,
    },
    {
        "name": "Logical + Z3: Tot nghiep",
        "payload": {
            "question": "Tôi có đủ điều kiện tốt nghiệp không?",
            "user_facts": {
                "tin_chi_tich_luy": 122,
                "diem_tb": 2.75,
                "no_mon": False,
                "hoan_thanh_tttn": True,
                "diem_ren_luyen": 85,
            },
        },
        "expect_citation": True,
        "expect_z3": True,
    },
    {
        "name": "Logical + Z3: Hoc bong",
        "payload": {
            "question": "Tôi có được học bổng khuyến khích không?",
            "user_facts": {
                "tin_chi_tich_luy": 122,
                "diem_tb": 3.5,
                "no_mon": False,
                "hoan_thanh_tttn": True,
                "diem_ren_luyen": 85,
            },
        },
        "expect_citation": True,
        "expect_z3": True,
    },
]


def run_tests(base_url: str) -> bool:
    print(f"\nSmoke test: {base_url}\n{'=' * 50}")
    passed = 0
    failed = 0

    with httpx.Client(timeout=30) as client:
        for index, test_case in enumerate(TEST_CASES, start=1):
            print(f"\n[{index}/5] {test_case['name']}")
            started = time.time()

            try:
                response = client.post(f"{base_url.rstrip('/')}/api/v1/ask", json=test_case["payload"])
            except Exception as exc:
                print(f"  FAIL request error: {exc}")
                failed += 1
                continue

            elapsed_ms = int((time.time() - started) * 1000)

            if response.status_code != 200:
                print(f"  FAIL HTTP {response.status_code}: {response.text[:180]}")
                failed += 1
                continue

            data = response.json()
            checks = []
            case_ok = True

            if data.get("answer"):
                checks.append("answer")
            else:
                checks.append("answer missing")
                case_ok = False

            if test_case["expect_citation"]:
                if data.get("citations"):
                    checks.append(f"{len(data['citations'])} citations")
                else:
                    checks.append("citations missing")
                    case_ok = False

            if test_case["expect_z3"]:
                z3_result = data.get("z3_result")
                if z3_result:
                    checks.append(f"Z3 verified={z3_result.get('verified')}")
                else:
                    checks.append("z3_result missing")
                    case_ok = False

            checks.append(f"conf={data.get('confidence', 0):.0%}")
            print(f"  {' | '.join(checks)} [{elapsed_ms}ms]")
            print(f"  {data.get('answer', '')[:140]}...")

            if case_ok:
                passed += 1
            else:
                failed += 1

    print(f"\n{'=' * 50}")
    print(f"{passed}/5 passed, {failed} failed\n")
    return failed == 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000", help="Backend base URL")
    args = parser.parse_args()
    return 0 if run_tests(args.url) else 1


if __name__ == "__main__":
    sys.exit(main())
