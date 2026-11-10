"""Run and record real Lean compilation for original and clean definition slices."""

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent
BUILD = Path("D:/migration/lean-proof-slice-build")
EXPECTED_ORIGINAL = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
EXPECTED_ELAN = "fad2e980a191c15884cc1d80d170ffc5fa84f3774541020145b66d1a644c6111"
EXPECTED_MATHLIB = "56a005855ea17e0b0958f73ec801ae140b0a1679"
THEOREMS = ("allenDynesTc_unfold", "h3s_tc_prediction_unfold", "lah10_tc_prediction_unfold")
DEBT_THEOREMS = ("allenDynes_weak_coupling_limit", "bcs_isotope_effect", "floquet_enhanced_tc")
STANDARD_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd=BUILD, timeout=240):
    env = os.environ.copy()
    env.update({
        "ELAN_HOME": "D:/migration/toolchains/elan/home",
        "XDG_CACHE_HOME": "D:/migration/cache",
        "HOME": "D:/migration/home",
        "TMP": "D:/migration/tmp",
        "TEMP": "D:/migration/tmp",
        "TMPDIR": "D:/migration/tmp",
        "PATH": "D:/migration/toolchains/elan/home/bin" + os.pathsep + env.get("PATH", ""),
    })
    pinned = {
        "lake": "D:/migration/toolchains/elan/home/bin/lake.exe",
        "lean": "D:/migration/toolchains/elan/home/bin/lean.exe",
    }
    executable = pinned.get(command[0]) or shutil.which(command[0], path=env["PATH"])
    if not executable or not Path(executable).exists():
        raise FileNotFoundError(f"executable not found: {command[0]} -> {executable}")
    command = [executable, *command[1:]]
    result = subprocess.run(command, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {
        "command": command,
        "cwd": str(cwd),
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def combined(result):
    return result["stdout"] + "\n" + result["stderr"]


def parse_new_theorem(output, name):
    matches = [line for line in output.splitlines() if name in line and "depends on axioms" in line]
    if len(matches) != 1:
        raise ValueError(f"cannot identify axiom output for {name}: {matches}")
    line = matches[0]
    axioms_text = line.split("[", 1)[1].rsplit("]", 1)[0]
    axioms = [item.strip() for item in axioms_text.split(",")]
    return {
        "depends_on_axioms": True,
        "axioms": axioms,
        "sorryAx": "sorryAx" in line,
        "nonstandard_axioms": sorted(set(axioms) - STANDARD_AXIOMS),
        "raw": line,
    }


def run_all_tests():
    original_source = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")
    copy = ROOT / "RoomTempSC_Formalization.lean"
    if sha256(original_source) != EXPECTED_ORIGINAL or sha256(copy) != EXPECTED_ORIGINAL:
        raise ValueError("original source or copy hash changed")
    if (ROOT / "ProofSlice.lean").read_bytes() != (BUILD / "ProofSlice.lean").read_bytes():
        raise ValueError("clean slice source differs between workspace and build copy")

    original_result = run([
        "lake", "env", "lean", "-o", ".lake/build/lib/lean/RoomTempSC_Formalization.olean",
        "RoomTempSC_Formalization.lean",
    ])
    (ROOT / "original-compile.log").write_text(
        json.dumps(original_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    original_output = combined(original_result)
    error_markers = ["eulerMascheroni", "unexpected token 'λ'", "ω_D", "HasEquiv"]
    missing = [marker for marker in error_markers if marker not in original_output]
    if original_result["exit_code"] == 0 or missing:
        raise ValueError(f"original incompatibility not reproduced as expected: code={original_result['exit_code']}, missing={missing}")

    clean_result = run([
        "lake", "env", "lean", "-o", ".lake/build/lib/lean/ProofSlice.olean", "ProofSlice.lean",
    ])
    (ROOT / "clean-compile.log").write_text(
        json.dumps(clean_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    clean_output = combined(clean_result)
    if clean_result["exit_code"] != 0:
        raise ValueError(f"clean definition slice failed: {clean_output}")
    new_dependencies = {name: parse_new_theorem(clean_output, name) for name in THEOREMS}
    for name, row in new_dependencies.items():
        if row["sorryAx"] or row["nonstandard_axioms"]:
            raise ValueError(f"unexpected dependency in {name}: {row}")

    lean_version_result = run(["lean", "--version"])
    if lean_version_result["exit_code"] != 0:
        raise ValueError("Lean version check failed")
    mathlib_result = run(["git", "-C", str(BUILD / ".lake/packages/mathlib"), "rev-parse", "HEAD"])
    if mathlib_result["exit_code"] != 0 or mathlib_result["stdout"].strip() != EXPECTED_MATHLIB:
        raise ValueError(f"Mathlib revision mismatch: {mathlib_result}")

    original_text = original_source.read_text(encoding="utf-8")
    sorry_lines = [index + 1 for index, line in enumerate(original_text.splitlines()) if re.match(r"^\s*sorry\b", line)]
    if sorry_lines != [93, 112, 185]:
        raise ValueError(f"original static sorry lines changed: {sorry_lines}")

    data = {
        "schema": "lean-definition-proof-slice-v1",
        "date": "2026-11-11",
        "scope": "独立清洁定义切片；原文件直接编译不兼容，原物理命题未证明。",
        "original": {
            "path": str(original_source),
            "copy_path": str(copy),
            "sha256": sha256(original_source),
            "copy_sha256": sha256(copy),
            "source_modified": False,
            "sorry_lines": sorry_lines,
            "direct_compile_unavailable": True,
        },
        "toolchain": {
            "lean_version": combined(lean_version_result).strip(),
            "mathlib_rev": mathlib_result["stdout"].strip(),
            "elan_asset_sha256": EXPECTED_ELAN,
            "elan_home": "D:/migration/toolchains/elan/home",
            "build_copy": str(BUILD),
            "path_unchanged": True,
        },
        "original_compile": {
            "status": "source_incompatible",
            "exit_code": original_result["exit_code"],
            "error_markers": error_markers,
            "log": "original-compile.log",
            "original_theorem_axiom_audit_available": False,
        },
        "compile": {
            "status": "passed",
            "exit_code": clean_result["exit_code"],
            "machine_checked": True,
            "scope": "clean_definition_slice",
            "log": "clean-compile.log",
        },
        "dependencies": {
            "new_theorems": new_dependencies,
            "original_theorems": {
                name: {"audit_available": False, "static_debt": True, "sorryAx": None}
                for name in DEBT_THEOREMS
            },
            "debt_preserved": True,
            "physical_theorems_proven": False,
        },
        "verification_scope": {
            "definition_slice_only": True,
            "original_file_compiled": False,
            "original_theorem_axiom_audit_available": False,
            "physical_validity_verified": False,
            "material_prediction_verified": False,
            "experimental_verification": False,
        },
    }
    (ROOT / "proof-slice.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Lean 独立清洁定义切片：真实编译与边界",
        "",
        "> 2026-11-11。**定义展开通过，不是物理证明。**",
        "",
        "## 实际结果",
        "",
        "- Lean 4.35.0 与固定 Mathlib `56a005855ea17e0b0958f73ec801ae140b0a1679` 已在 D 盘隔离运行。",
        "- 三个清洁定义展开定理编译退出码为 0；每个仅依赖 `propext`、`Classical.choice`、`Quot.sound`，没有 `sorryAx` 或额外公理。",
        "- 原文件直接编译失败，存在 `eulerMascheroni` 未定义、希腊字母 `λ` 标识符错误、`ω_D` 未绑定和 `HasEquiv ℝ` 缺失。",
        "- 原文件仍有 3 处既有 `sorry`（第 93、112、185 行）；由于编译失败，原三条定理的 `sorryAx` 审计不可用，不能伪造该结果。",
        "",
        "## 三个定义展开",
        "",
        "| 定理 | 编译 | sorryAx | 公理依赖 |",
        "|:--|:--|:--|:--|",
    ]
    for name, row in new_dependencies.items():
        lines.append(f"| `{name}` | 退出码 0 | 无 | {', '.join(row['axioms'])} |")
    lines += [
        "",
        "## 明确边界",
        "",
        "本次只验证三个清洁定义的展开，不调用原三条物理定理，不证明其弱耦合极限、同位素效应或 Floquet 增强命题。原文件复制件哈希与原文件一致，原文件未修改。",
        "",
        "物理有效性、材料预测、数值模型和实验验证均未验证。Mathlib 的版本差异和原文件语法错误必须另行处理，不能用本次切片替代。",
        "",
        "实际命令、原始输出和退出码见 `run.log`、`original-compile.log`、`clean-compile.log` 与 `proof-slice.json`。",
        "",
    ]
    (ROOT / "PROOF_SLICE.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "original_compile": data["original_compile"]["status"],
        "clean_compile": data["compile"]["status"],
        "exit_code": data["compile"]["exit_code"],
        "new_theorems": {name: {"sorryAx": row["sorryAx"], "axioms": row["axioms"]} for name, row in new_dependencies.items()},
        "original_theorem_audit_available": False,
        "proof_slice_sha256": sha256(ROOT / "proof-slice.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
