import logging

from z3 import And, Bool, Int, Or, Real, Solver, sat

logger = logging.getLogger(__name__)


def check_graduation_condition(user_facts: dict) -> dict:
    """
    Rule: eligible for graduation when:
    - accumulated credits >= 120
    - GPA >= 2.0
    - no failed/pending courses
    """
    tin_chi = Int("tin_chi")
    diem_tb = Real("diem_tb")
    no_mon = Bool("no_mon")

    solver = Solver()
    solver.add(tin_chi == user_facts.get("tin_chi_tich_luy", 0))
    solver.add(diem_tb == user_facts.get("diem_tb", 0.0))
    solver.add(no_mon == user_facts.get("no_mon", True))

    du_dieu_kien = And(tin_chi >= 120, diem_tb >= 2.0, no_mon == False)
    solver.add(du_dieu_kien)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 30, Khoản 1 - Điều kiện tốt nghiệp",
            "explanation": (
                f"Sinh viên ĐỦ điều kiện tốt nghiệp: {user_facts.get('tin_chi_tich_luy')} TC >= 120, "
                f"ĐTB {user_facts.get('diem_tb')} >= 2.0, không nợ môn."
            ),
        }

    reasons = []
    if user_facts.get("tin_chi_tich_luy", 0) < 120:
        reasons.append(f"thiếu {120 - user_facts.get('tin_chi_tich_luy', 0)} tín chỉ")
    if user_facts.get("diem_tb", 0) < 2.0:
        reasons.append(f"ĐTB {user_facts.get('diem_tb')} < 2.0")
    if user_facts.get("no_mon", False):
        reasons.append("còn nợ môn học")

    return {
        "verified": False,
        "rule_applied": "Điều 30, Khoản 1 - Điều kiện tốt nghiệp",
        "explanation": f"Sinh viên CHƯA đủ điều kiện: {'; '.join(reasons)}.",
    }


def check_canh_cao_hoc_vu(user_facts: dict) -> dict:
    """Rule: academic warning when semester GPA < 1.0 or accumulated GPA < 1.2."""
    diem_tb_hk = Real("diem_tb_hk")
    diem_tb_tl = Real("diem_tb_tl")
    solver = Solver()

    solver.add(diem_tb_hk == user_facts.get("diem_tb_hoc_ky", 2.0))
    solver.add(diem_tb_tl == user_facts.get("diem_tb_tich_luy", 2.0))

    solver.add(Or(diem_tb_hk < 1.0, diem_tb_tl < 1.2))

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 22 - Cảnh cáo học vụ",
            "explanation": "Sinh viên thuộc diện cảnh cáo học vụ theo quy chế.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 22 - Cảnh cáo học vụ",
        "explanation": "Sinh viên không thuộc diện cảnh cáo học vụ.",
    }


def check_hoc_bong_khuyen_khich(user_facts: dict) -> dict:
    """Rule: scholarship eligible when GPA >= 3.2 and no pending courses."""
    diem_tb = Real("diem_tb")
    no_mon = Bool("no_mon")
    solver = Solver()

    solver.add(diem_tb == user_facts.get("diem_tb", 0.0))
    solver.add(no_mon == user_facts.get("no_mon", True))
    solver.add(And(diem_tb >= 3.2, no_mon == False))

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 25 - Học bổng khuyến khích học tập",
            "explanation": f"Sinh viên ĐỦ điều kiện học bổng: ĐTB {user_facts.get('diem_tb')} >= 3.2, không nợ môn.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 25 - Học bổng khuyến khích học tập",
        "explanation": "Sinh viên chưa đủ điều kiện học bổng.",
    }


RULE_KEYWORDS = {
    "graduation": ["tốt nghiệp", "ra trường", "hoàn thành chương trình"],
    "canh_cao": ["cảnh cáo", "học vụ", "bị đuổi", "thôi học"],
    "hoc_bong": ["học bổng", "khuyến khích", "hỗ trợ tài chính"],
}


def run_z3_check(question: str, user_facts: dict) -> dict | None:
    """Choose and run the matching Z3 rule for a question."""
    question_lower = question.lower()

    if any(keyword in question_lower for keyword in RULE_KEYWORDS["graduation"]):
        return check_graduation_condition(user_facts)

    if any(keyword in question_lower for keyword in RULE_KEYWORDS["canh_cao"]):
        return check_canh_cao_hoc_vu(user_facts)

    if any(keyword in question_lower for keyword in RULE_KEYWORDS["hoc_bong"]):
        return check_hoc_bong_khuyen_khich(user_facts)

    logger.info("No matching Z3 rule found for question")
    return None
