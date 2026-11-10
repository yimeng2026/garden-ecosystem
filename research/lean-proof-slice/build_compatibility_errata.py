"""Build evidence-bound Lean source compatibility errata without editing the source."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ORIGINAL = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
ORIGINAL = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")
LOG = ROOT / "original-compile.log"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if sha256(ORIGINAL) != EXPECTED_ORIGINAL:
        raise ValueError("original source hash changed")
    log_text = LOG.read_text(encoding="utf-8")
    issues = [
        {
            "id": "euler_mascheroni",
            "severity": "P0",
            "status": "open",
            "evidence": "Unknown identifier `eulerMascheroni`",
            "next": "将未限定的 eulerMascheroni 改为经 Mathlib 源码确认存在的 Real.eulerMascheroniConstant，并核对所需 import 与数值语义。",
        },
        {
            "id": "lambda_identifier",
            "severity": "P0",
            "status": "open",
            "evidence": "unexpected token 'λ'",
            "next": "将绑定变量 λ 改为 ASCII lam，保持公式参数顺序与物理含义不变。",
        },
        {
            "id": "omega_d_binding",
            "severity": "P0",
            "status": "open",
            "evidence": "ω_D is unknown and autoImplicit cannot infer a function type",
            "next": "显式声明 ω_D : ℝ → ℝ 与 ω₀ : ℝ 的类型、单位和物理定义，禁止依赖 autoImplicit 猜测。",
        },
        {
            "id": "has_equiv_real",
            "severity": "P0",
            "status": "open",
            "evidence": "failed to synthesize instance of type class HasEquiv ℝ",
            "next": "不构造虚假实例；将约等号命题改写为等式、极限或显式误差估计，并注明近似条件。",
        },
    ]
    for row in issues:
        marker = {"euler_mascheroni": "eulerMascheroni", "lambda_identifier": "unexpected token 'λ'", "omega_d_binding": "ω_D", "has_equiv_real": "HasEquiv ℝ"}[row["id"]]
        if marker not in log_text:
            raise ValueError(f"missing direct log evidence for {row['id']}")
        row["log_marker"] = marker

    data = {
        "schema": "lean-compatibility-errata-v1",
        "date": "2026-11-11",
        "original": {
            "path": str(ORIGINAL),
            "sha256": sha256(ORIGINAL),
            "source_modified": False,
        },
        "original_compile": {
            "status": "source_incompatible",
            "exit_code": 1,
            "log": "original-compile.log",
            "log_sha256": sha256(LOG),
        },
        "issues": issues,
        "open_boundaries": {
            "original_file_compiled": False,
            "original_theorems_proven": False,
            "physical_validity_verified": False,
            "all_errata_resolved": False,
        },
        "verification_scope": {
            "errata_only": True,
            "new_axiom_or_sorry_added": False,
            "source_modified": False,
        },
    }
    (ROOT / "compatibility-issues.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Lean 原文件兼容性勘误：四类开放问题",
        "",
        "> 2026-11-11。只登记错误和清偿动作，不修改原文件，不宣称修复或物理证明。",
        "",
        "## 真实编译边界",
        "",
        f"原文件 SHA-256：`{EXPECTED_ORIGINAL}`。直接编译退出码为 1，原始日志为 `original-compile.log`。",
        "",
        "| 问题 | 直接证据 | 当前状态 | 清偿动作 |",
        "|:--|:--|:--|:--|",
    ]
    for row in issues:
        lines.append(f"| `{row['id']}` | {row['evidence']} | **{row['status']}／未解决** | {row['next']} |")
    lines += [
        "",
        "## 执行顺序",
        "",
        "1. 先修常量、绑定变量和显式类型，使最小定义可解析；不得用 autoImplicit 猜测物理函数。",
        "2. 再处理约等号的命题语义：等式、极限或显式误差估计三选一，不能为了通过编译构造虚假 `HasEquiv ℝ` 实例。",
        "3. 每项修复都必须以真实 Lean 命令、退出码和公理依赖审计验收；未通过前保持 `open`。",
        "4. 清洁定义切片继续独立保留，不把其成功当作原文件或三条物理定理的证明。",
        "",
        "原文件未修改，未新增公理、证明位 `sorry` 或物理结论。物理有效性、材料预测和实验验证仍未解决。",
        "",
    ]
    (ROOT / "COMPATIBILITY_ERRATA.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"issues": len(issues), "status": sorted({row["status"] for row in issues}), "log_sha256": data["original_compile"]["log_sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
