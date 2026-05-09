import logging

from z3 import And, Bool, Int, Or, Real, Solver, sat

logger = logging.getLogger(__name__)


def check_graduation(facts: dict) -> dict:
    """Điều kiện tốt nghiệp đại học hệ chính quy."""
    solver = Solver()
    tin_chi = Int("tin_chi")
    diem_tb = Real("diem_tb")
    no_mon = Bool("no_mon")
    hoan_thanh_tttn = Bool("hoan_thanh_tttn")

    solver.add(tin_chi == facts.get("tin_chi_tich_luy", 0))
    solver.add(diem_tb == facts.get("diem_tb", 0.0))
    solver.add(no_mon == facts.get("no_mon", True))
    solver.add(hoan_thanh_tttn == facts.get("hoan_thanh_tttn", False))

    rule = And(tin_chi >= 120, diem_tb >= 2.0, no_mon == False, hoan_thanh_tttn == True)
    solver.add(rule)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 30, Khoản 1 - Điều kiện tốt nghiệp",
            "explanation": (
                f"Đủ điều kiện tốt nghiệp: {facts.get('tin_chi_tich_luy')} TC (>=120), "
                f"ĐTB {facts.get('diem_tb')} (>=2.0), không nợ môn, đã hoàn thành thực tập."
            ),
        }

    missing = []
    if facts.get("tin_chi_tich_luy", 0) < 120:
        missing.append(f"thiếu {120 - facts.get('tin_chi_tich_luy', 0)} TC")
    if facts.get("diem_tb", 0) < 2.0:
        missing.append(f"ĐTB {facts.get('diem_tb')} < 2.0")
    if facts.get("no_mon", True):
        missing.append("còn nợ môn học")
    if not facts.get("hoan_thanh_tttn", False):
        missing.append("chưa hoàn thành thực tập/ĐATN")

    return {
        "verified": False,
        "rule_applied": "Điều 30, Khoản 1 - Điều kiện tốt nghiệp",
        "explanation": f"Chưa đủ điều kiện tốt nghiệp: {'; '.join(missing)}.",
    }


def check_canh_cao(facts: dict) -> dict:
    """Cảnh cáo học vụ."""
    solver = Solver()
    diem_tb_hk = Real("diem_tb_hk")
    diem_tb_tl = Real("diem_tb_tl")

    solver.add(diem_tb_hk == facts.get("diem_tb_hoc_ky", 2.0))
    solver.add(diem_tb_tl == facts.get("diem_tb_tich_luy", 2.0))

    rule = Or(diem_tb_hk < 1.0, diem_tb_tl < 1.2)
    solver.add(rule)

    if solver.check() == sat:
        reasons = []
        if facts.get("diem_tb_hoc_ky", 2.0) < 1.0:
            reasons.append(f"ĐTB học kỳ {facts.get('diem_tb_hoc_ky')} < 1.0")
        if facts.get("diem_tb_tich_luy", 2.0) < 1.2:
            reasons.append(f"ĐTB tích lũy {facts.get('diem_tb_tich_luy')} < 1.2")
        return {
            "verified": True,
            "rule_applied": "Điều 22 - Cảnh cáo học vụ",
            "explanation": f"Thuộc diện cảnh cáo học vụ: {'; '.join(reasons)}.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 22 - Cảnh cáo học vụ",
        "explanation": "Không thuộc diện cảnh cáo học vụ.",
    }


def check_dinh_chi(facts: dict) -> dict:
    """Bị đình chỉ học tập."""
    solver = Solver()
    so_lan_canh_cao = Int("so_lan_canh_cao")
    diem_tb_tl = Real("diem_tb_tl")

    solver.add(so_lan_canh_cao == facts.get("so_lan_canh_cao", 0))
    solver.add(diem_tb_tl == facts.get("diem_tb_tich_luy", 2.0))

    rule = Or(so_lan_canh_cao >= 2, diem_tb_tl < 0.8)
    solver.add(rule)

    if solver.check() == sat:
        reasons = []
        if facts.get("so_lan_canh_cao", 0) >= 2:
            reasons.append(f"{facts.get('so_lan_canh_cao')} lần cảnh cáo (>=2)")
        if facts.get("diem_tb_tich_luy", 2.0) < 0.8:
            reasons.append(f"ĐTB {facts.get('diem_tb_tich_luy')} < 0.8")
        return {
            "verified": True,
            "rule_applied": "Điều 23 - Đình chỉ học tập",
            "explanation": f"Thuộc diện đình chỉ: {'; '.join(reasons)}.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 23 - Đình chỉ học tập",
        "explanation": "Không thuộc diện đình chỉ học tập.",
    }


def check_hoc_bong(facts: dict) -> dict:
    """Học bổng khuyến khích học tập."""
    solver = Solver()
    diem_tb = Real("diem_tb")
    no_mon = Bool("no_mon")
    diem_rl = Int("diem_rl")

    solver.add(diem_tb == facts.get("diem_tb", 0.0))
    solver.add(no_mon == facts.get("no_mon", True))
    solver.add(diem_rl == facts.get("diem_ren_luyen", 0))

    rule = And(diem_tb >= 3.2, no_mon == False, diem_rl >= 80)
    solver.add(rule)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 25 - Học bổng khuyến khích",
            "explanation": (
                f"Đủ điều kiện học bổng: ĐTB {facts.get('diem_tb')} >= 3.2, "
                f"điểm rèn luyện {facts.get('diem_ren_luyen')} >= 80, không nợ môn."
            ),
        }

    missing = []
    if facts.get("diem_tb", 0) < 3.2:
        missing.append(f"ĐTB {facts.get('diem_tb')} < 3.2")
    if facts.get("no_mon", True):
        missing.append("còn nợ môn")
    if facts.get("diem_ren_luyen", 0) < 80:
        missing.append(f"điểm rèn luyện {facts.get('diem_ren_luyen')} < 80")

    return {
        "verified": False,
        "rule_applied": "Điều 25 - Học bổng khuyến khích",
        "explanation": f"Chưa đủ điều kiện học bổng: {'; '.join(missing)}.",
    }


def check_dang_ky_mon(facts: dict) -> dict:
    """Điều kiện đăng ký môn học."""
    solver = Solver()
    hoan_thanh_tien_quyet = Bool("hoan_thanh_tien_quyet")
    khong_bi_cam = Bool("khong_bi_cam")
    dang_trong_thoi_gian_dk = Bool("dang_trong_thoi_gian_dk")

    solver.add(hoan_thanh_tien_quyet == facts.get("hoan_thanh_tien_quyet", False))
    solver.add(khong_bi_cam == facts.get("khong_bi_cam", True))
    solver.add(dang_trong_thoi_gian_dk == facts.get("trong_thoi_gian_dang_ky", False))

    rule = And(hoan_thanh_tien_quyet == True, khong_bi_cam == True, dang_trong_thoi_gian_dk == True)
    solver.add(rule)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 10 - Đăng ký học phần",
            "explanation": "Đủ điều kiện đăng ký môn học.",
        }

    missing = []
    if not facts.get("hoan_thanh_tien_quyet", False):
        missing.append("chưa hoàn thành môn tiên quyết")
    if not facts.get("khong_bi_cam", True):
        missing.append("đang bị cấm đăng ký")
    if not facts.get("trong_thoi_gian_dang_ky", False):
        missing.append("ngoài thời gian đăng ký")

    return {
        "verified": False,
        "rule_applied": "Điều 10 - Đăng ký học phần",
        "explanation": f"Không đủ điều kiện đăng ký: {'; '.join(missing)}.",
    }


def check_bao_luu(facts: dict) -> dict:
    """Điều kiện bảo lưu kết quả học tập."""
    solver = Solver()
    ly_do_hop_le = Bool("ly_do_hop_le")
    da_hoc_it_nhat_1_hk = Bool("da_hoc_it_nhat_1_hk")

    solver.add(ly_do_hop_le == facts.get("ly_do_hop_le", False))
    solver.add(da_hoc_it_nhat_1_hk == facts.get("da_hoc_it_nhat_1_hk", False))

    rule = And(ly_do_hop_le == True, da_hoc_it_nhat_1_hk == True)
    solver.add(rule)

    if solver.check() == sat:
        return {
            "verified": True,
            "rule_applied": "Điều 35 - Bảo lưu kết quả",
            "explanation": "Đủ điều kiện bảo lưu kết quả học tập.",
        }

    return {
        "verified": False,
        "rule_applied": "Điều 35 - Bảo lưu kết quả",
        "explanation": "Chưa đủ điều kiện bảo lưu: cần lý do hợp lệ và đã học >= 1 học kỳ.",
    }


RULE_MAP = {
    "graduation": {
        "keywords": ["tốt nghiệp", "ra trường", "hoàn thành chương trình", "bằng tốt nghiệp"],
        "fn": check_graduation,
    },
    "canh_cao": {
        "keywords": ["cảnh cáo", "học vụ", "xếp loại yếu"],
        "fn": check_canh_cao,
    },
    "dinh_chi": {
        "keywords": ["đình chỉ", "bị đuổi", "thôi học", "buộc thôi học"],
        "fn": check_dinh_chi,
    },
    "hoc_bong": {
        "keywords": ["học bổng", "khuyến khích", "hỗ trợ học tập"],
        "fn": check_hoc_bong,
    },
    "dang_ky_mon": {
        "keywords": ["đăng ký môn", "đăng ký học phần", "đăng ký tín chỉ"],
        "fn": check_dang_ky_mon,
    },
    "bao_luu": {
        "keywords": ["bảo lưu", "tạm dừng học", "nghỉ học"],
        "fn": check_bao_luu,
    },
}


def run_z3_check(question: str, user_facts: dict) -> dict | None:
    question_lower = question.lower()
    for rule_key, config in RULE_MAP.items():
        if any(keyword in question_lower for keyword in config["keywords"]):
            logger.info("[Z3] matched rule: %s", rule_key)
            try:
                return config["fn"](user_facts)
            except Exception as exc:
                logger.error("[Z3] error in %s: %s", rule_key, exc)
                return None
    return None
