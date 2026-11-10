"""Audit real compilation of the two independent compatibility definitions."""

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
EXPECTED_MATHLIB = "56a005855ea17e0b0958f73ec801ae140b0a1679"
THEOREMS = ("bcsCriticalTemp_unfold", "debyeModel_unfold")
STANDARD = {"propext", "Classical.choice", "Quot.sound"}


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
    result = subprocess.run([executable, *command[1:]], cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    return {"command": [executable, *command[1:]], "cwd": str(cwd), "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}


def parse(output, name):
    matches = [line for line in output.splitlines() if name in line and "depends on axioms" in line]
    if len(matches) != 1:
        raise ValueError(f"cannot identify axiom output for {name}: {matches}")
    line = matches[0]
    axioms = [item.strip() for item in line.split("[", 1)[1].rsplit("]", 1)[0].split(",")]
    return {
        "depends_on_axioms": True,
        "axioms": axioms,
        "sorryAx": "sorryAx" in line,
        "nonstandard_axioms": sorted(set(axioms) - STANDARD),
        "raw": line,
    }


def run_all_tests():
    original = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")
    if sha256(original) != EXPECTED_ORIGINAL:
        raise ValueError("original source hash changed")
    if (ROOT / "CompatibleDefinitions.lean").read_bytes() != (BUILD / "CompatibleDefinitions.lean").read_bytes():
        raise ValueError("workspace and build copy definition sources differ")

    compile_result = run(["lake", "env", "lean", "-o", ".lake/build/lib/lean/CompatibleDefinitions.olean", "CompatibleDefinitions.lean"])
    (ROOT / "compatible-compile.log").write_text(json.dumps(compile_result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    output = compile_result["stdout"] + "\n" + compile_result["stderr"]
    if compile_result["exit_code"] != 0:
        raise ValueError(f"compatible definitions failed to compile: {output}")
    dependencies = {name: parse(output, name) for name in THEOREMS}
    for name, row in dependencies.items():
        if row["sorryAx"] or row["nonstandard_axioms"]:
            raise ValueError(f"unexpected dependency in {name}: {row}")

    lean_version = run(["lean", "--version"])
    mathlib_version = run(["git", "-C", str(BUILD / ".lake/packages/mathlib"), "rev-parse", "HEAD"])
    if lean_version["exit_code"] != 0 or mathlib_version["exit_code"] != 0 or mathlib_version["stdout"].strip() != EXPECTED_MATHLIB:
        raise ValueError("toolchain version verification failed")

    original_text = original.read_text(encoding="utf-8")
    sorry_lines = [index + 1 for index, line in enumerate(original_text.splitlines()) if re.match(r"^\s*sorry\b", line)]
    if sorry_lines != [93, 112, 185]:
        raise ValueError(f"original sorry lines changed: {sorry_lines}")

    data = {
        "schema": "lean-compatible-definitions-v1",
        "date": "2026-11-11",
        "scope": "两个独立定义的真实编译；只清偿常量、绑定和 Debye 类型，不处理 HasEquiv 或物理证明。",
        "original": {
            "path": str(original),
            "sha256": sha256(original),
            "source_modified": False,
            "sorry_lines": sorry_lines,
        },
        "original_compile": {
            "status": "source_incompatible",
            "original_theorem_axiom_audit_available": False,
        },
        "compile": {
            "status": "passed",
            "exit_code": compile_result["exit_code"],
            "machine_checked": True,
            "log": "compatible-compile.log",
        },
        "toolchain": {
            "lean_version": (lean_version["stdout"] + lean_version["stderr"]).strip(),
            "mathlib_rev": mathlib_version["stdout"].strip(),
            "build_copy": str(BUILD),
            "path_unchanged": True,
        },
        "dependencies": dependencies,
        "local_resolution": {
            "euler_constant": True,
            "ascii_lambda": True,
            "debye_types": True,
            "has_equiv_semantics": False,
        },
        "open_boundaries": {
            "original_file_compiled": False,
            "original_theorems_proven": False,
            "physical_validity_verified": False,
            "all_compatibility_complete": False,
        },
        "verification_scope": {
            "definitions_only": True,
            "new_axiom_or_sorry_added": False,
            "source_modified": False,
            "physical_validity_verified": False,
        },
    }
    (ROOT / "compatible-definitions.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Lean 兼容性清偿切片：常量、绑定与 Debye 类型",
        "",
        "> 2026-11-11。**两个定义展开通过，不是物理证明。**",
        "",
        "## 实际编译结果",
        "",
        "- `bcsCriticalTemp` 使用 `Real.eulerMascheroniConstant`，不再使用未限定的 `eulerMascheroni`。",
        "- `debyeModel` 显式给出 `ω₀ : ℝ` 与 `ℝ → ℝ` 函数类型，输入 `M : ℝ` 时返回 `ω₀ / Real.sqrt M`。",
        "- ASCII `lam` 继续沿用前述清洁定义切片；本文件没有 `HasEquiv`。",
        "- 两个 `rfl` 展开定理真实编译退出码为 0，均只依赖标准三公理，无 `sorryAx`。",
        "",
        "| 定理 | 编译 | sorryAx | 公理依赖 |",
        "|:--|:--|:--|:--|",
    ]
    for name, row in dependencies.items():
        lines.append(f"| `{name}` | 退出码 0 | 无 | {', '.join(row['axioms'])} |")
    lines += [
        "",
        "## 开放边界",
        "",
        "原文件未修改，原文件直译仍不兼容，原三条定理的 `sorryAx` 审计仍不可用。`HasEquiv ℝ` 的命题语义保持开放，不能通过构造实例强行通过。",
        "",
        "本切片不证明弱耦合极限、同位素比值或 Floquet 增强，不验证物理有效性、材料预测、数值模型或实验复现。实际命令与原始输出见 `compatible-run.log`、`compatible-compile.log` 和 `compatible-definitions.json`。",
        "",
    ]
    (ROOT / "COMPATIBLE_DEFINITIONS.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "compile": data["compile"]["status"],
        "exit_code": data["compile"]["exit_code"],
        "dependencies": {name: {"sorryAx": row["sorryAx"], "axioms": row["axioms"]} for name, row in dependencies.items()},
        "json_sha256": sha256(ROOT / "compatible-definitions.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
