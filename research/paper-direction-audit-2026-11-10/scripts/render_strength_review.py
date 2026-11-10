"""55 篇强化系列的逐篇裁决、机读总账与状态图。

裁决只代表本轮文献与源文件初审，不是外部查新或证明复核。
运行：python scripts/render_strength_review.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import matplotlib.pyplot as plt
from matplotlib import font_manager

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = Path(__file__).resolve().parents[4]
TOE = WORKSPACE / "toe-sylva-audit"

RECORD_BASELINE_KEYS = {
    "id",
    "series",
    "title",
    "role",
    "novelty",
    "unfinished",
    "priority",
    "evidence",
    "source_line_1",
}
SUMMARY_BASELINE_KEYS = {
    "status",
    "reviewed",
    "series",
    "priorities",
    "unique_ids",
    "evidence_files_exist",
    "external_novelty_certified",
    "machine_proofs_certified_by_this_review",
}


def merge_extras(baseline, existing, baseline_keys):
    """Refresh baseline fields while preserving later evidence by paper ID."""
    merged = dict(existing)
    for key in baseline_keys:
        merged[key] = baseline[key]
    return merged


def supplement_suffix(markdown):
    """Return the exact K1a/K1b/K2 suffix, rejecting duplicate full titles."""
    heading_lines = [
        line
        for line in markdown.splitlines()
        if re.match(r"^## (?:K1a |K1b |K2 )", line)
    ]
    if len(heading_lines) != len(set(heading_lines)):
        raise ValueError("duplicate K1a/K1b/K2 supplement heading")
    matches = list(re.finditer(r"(?m)^## (?:K1a |K1b |K2 )", markdown))
    if not matches:
        return ""
    return markdown[matches[0].start():].rstrip() + "\n"


# role, novelty, unfinished, priority
MATH = [
    ("公理治理方法论", "四分类与清偿流程是项目内治理增量；分类学本身不主张外部首创。", "全量公理登记、最小独立集与模型级相对一致性；落实 O4.3 对 Flyspeck／Metamath 过度引申的更正。", "P0"),
    ("p-adic 与 L-函数课程接口", "主要复用 mathlib；价值在课程编排和胶水定理，不是重新证明解析延拓。", "完成 T1.1 计算、T1.6 唯一性、T2.3 绝对收敛与 T2.5 小 conductor 实例；记录课程顺序分歧。", "P1"),
    ("Dedekind 课程接口与计算流水线", "三种定义和唯一分解属于成熟理论；自建空间在实例化与 Kummer–Dedekind 工作流。", "落地 ℤ[√−5]、检验指数条件、做一个类数实例；补齐类域论的 Tate 上同调与局部互反支柱。", "P1"),
    ("纵向整合与证明度量", "依赖深度、证明长度、概念压缩率的组合是项目管理方案，非公认深层定理度量。", "实现三指标测量并用已知定理校准；修正 O4.3 文献引申；阈值只能拦截平凡项，不能认证深刻性。", "P0"),
    ("Zp 真实编译实证", "六条中间层小定理有当次编译证据；底层数学主要是 mathlib 复用。", "复跑保存的命令与公理审计；推进 Hensel 引理和闭单位球↔逆极限的显式等价，而非只换陈述。", "P1"),
    ("层化陈数的求和结构形式化", "整数权重的加权求和整性是真实但初等的项目内增量；不是 Chern–Weil 整性证明。", "登记 roots 并合并类型；给出层权重的独立物理来源和真实拓扑计算，不能用加权平均解释 137。", "P0"),
    ("信息几何修复路线", "对偶几何与最优传输为教材整理；已有玩具 Hessian／Bregman／Legendre 探针。", "把 FIM:=0 换成参数化分布族的真实定义；完成 KL／Gibbs、一般 Cramér–Rao 与源码落地，玩具恒等式不得冒充一般定理。", "P0"),
    ("Lie 理论与规范对称性课程", "Borel–Weil 等为成熟理论；项目增量是指出 U(1) 与群／代数类型错位。", "构造 U(1) 的周期商，分离 Lie 群与李代数类型；标准模型群结构化，并核验七层—权格联系是否仅为类比。", "P1"),
    ("相变信息几何的定理候选族", "统一判据、振幅与对数修正是组内强候选；尚未独立复核全部推导和外部查新。", "复算二维 Ising 曲率；做三维／四维数值检验与量子曲率；Lean 骨架去除 sorry 后再登记机器定理。", "P1"),
    ("随机矩阵的层化统一框架", "遗忘算子三分解是组织性提案；各组成普适性定理归原作者，β 几何待核。", "验证多割位势与 β 方向 Fisher；先实现 sine 核 Paley–Wiener 刻画，不提前宣称三层统一获证。", "P1"),
    ("最优传输与耗散几何", "EDE、Wasserstein 梯度流和熵正则极限以成熟理论为骨架；统一分类尚待严格化。", "证明猜想 D 的 Γ-收敛并处理非光滑情形；明确 EDE 与路径涨落定理的统一步骤，补高斯例逐行计算。", "P1"),
    ("谱序列的层化推理接口", "exact couple 提炼算子是项目内接口增量；谱序列与 Boardman 收敛均非新结果。", "构造真实 CNF 滤过复形；先机器化 S2 导出对正合性，再处理 lim¹／RE∞ 障碍证书。", "P1"),
    ("自由概率的统一表述", "五种独立性和 q 几何接口是研究纲领；自由 CLT、R-变换与渐近自由属于既有理论。", "完成五种独立性的精确统一、超收敛速率和 q 几何；先证自由独立时 R-变换可加，避免定义即定理的空转。", "P1"),
    ("RG 不动点几何与可复算演算", "两套显式计算有复算价值；不动点分类和 Fisher–Zamolodchikov 关系仍是候选。", "推进三维 Ising 不动点、两种度规的临界关系与边缘不动点分类；先闭合 S1 ε-展开的有理函数恒等式。", "P1"),
    ("可积系统与 Painlevé 机制链", "等谱／等单值桥和显式手工演算构成组内整合；不主张重写既有可积性理论。", "精确化 ARS 的适用范畴，构造 τ-函子并探索一般 β；先完成不依赖深层库的 I3／I4 代数核。", "P1"),
    ("几何量子化与整性接口", "三层量子化和轨道方法是成熟理论；与层化陈数的连接是项目内新接口。", "给出 Weil 整性证书，界定极化的函子性与 SYLVA 轨道边界；先做 G1 纯代数，不把结构同型说成物理导出。", "P1"),
    ("微分 Galois 可积性障碍", "正向可积与反向 Galois 障碍的对照有组内整合价值；判据统一未闭合。", "统一 Painlevé 与 Galois 判据的适用类，分析高阶复杂度；实现 G4 Kovacic 极点阶数判定。", "P1"),
    ("HoTT 与高阶结构路线", "主要是现代基础理论重构；CNF—Postnikov 障碍字典仍是猜想。", "跟踪半单纯类型问题，构造 CNF 障碍字典；用 Cubical 检验有限高群，并核查 mathlib 的 Kan 复形现状。", "P2"),
    ("张量网络—全息字典", "三层字典是项目内组织增量；min-cut 秩界与 MERA 计数为标准可证组件。", "显式构造 CNF 因果锥，处理 cMERA 连续极限障碍；先形式化 T2 min-cut，再计算纠缠 Hessian。", "P1"),
    ("广义对称性与高形式结构", "障碍三部曲和 SymTFT 层化联系为组内整合；非可逆融合代数已有成熟来源。", "研究连续 SymTFT 完备性与非可逆反常分类；完成 B²U(1) 可执行化和 G4 群上同调接口核查。", "P1"),
    ("代数 K 理论的普适化路线", "群完备化统一读法是组内重组；Grothendieck 群与 Bott 周期性为经典结果。", "先机器化 K0 的泛性质，比较 Bott 三条证明路线；再检验层化陈数与 RR／K 类的真实关系。", "P1"),
    ("遍历论三层结构与数值复算", "度量／拓扑／统计分层和 logistic、Feigenbaum 复算有教学研究价值，不是新遍历定理。", "先证 Garsia–Hopf 极大引理并推进 Birkhoff；再研究 SRB 显式收敛率与 KAM 最优渐近。", "P1"),
    ("朗兰兹校验器与物理走廊", "逐素数对账和校验器组织有复算价值；外部宣称与正式发表状态须独立更新。", "从 Part V 经典化陈述或有限组合引理起步；实现 Sturm 有效证书；CNF 的 L-函子保持无证据猜想。", "P2"),
    ("VOA／月光的对称代数接口", "VOA 作为朗兰兹与月光公共节点是组内组织；数值对账不等于证明月光定理。", "探索接口式下游定理与 Witten 猜想的数学化障碍；先做 V4 数值证书，VOA–CNF 保持纲领猜想。", "P2"),
    ("纽结／Chern–Simons 组合计算方向", "手工态和和机制联系有组内价值；skein、TQFT、Khovanov 与能级整性均为成熟理论。", "区分 unknot 探测、体积猜想和 CS 测度三个问题；先证明离散拓扑整性的极限保持，不能推出 137。", "P1"),
]

MODULE = [
    ("四力统一的玩具治理样本", "项目内价值是公理债务解剖；不是四力统一理论。", "将空集见证与真物理断言分离，清偿三条公理；所有参数需独立推导与可证伪检验。", "P0"),
    ("Einstein–Cartan 几何修复", "守恒律清偿是教材级增量；挠率—自旋耦合尚未实现。", "先证明两条守恒律；替换六条场方程占位并建立非平凡几何实例。", "P0"),
    ("黎曼ζ接口的健康脚手架", "主要复用 mathlib；不是黎曼猜想进展。", "清偿临界带和共轭对称两条公理；隔离其余实质假设并做独立公理审计。", "P1"),
    ("Navier–Stokes 循环论证警示", "只有负面包扎价值，不构成千禧问题求解。", "撤回解决措辞；给出非零初值的真实估计或小数据定理，禁止公理投影充当证明。", "P0"),
    ("Hodge 谓词空洞化警示", "揭示 subsingleton 使前提失真有审计价值；没有霍奇猜想数学增量。", "删除空洞化路径，改用有真实分量与代数循环的谓词；只保留可验证小例。", "P0"),
    ("拓扑绝缘体定义层", "良构约束较健康，属于可生长接口而非新拓扑物态理论。", "把 Brillouin 区实现为环面并建立 Bloch 哈密顿量实例；与 Berry／陈数模块共用类型。", "P1"),
    ("标准模型基础的快速清偿点", "Higgs 下界是初等证明增量；三条 axiom＋sorry 不可视为成果。", "消除三个 sorry 并先证 HiggsPotential 下界；随后实义化场强与协变导数。", "P0"),
    ("暗能量的最小可证模型", "ρ 常数化和加速膨胀是宇宙学入门定理，不是暗能量新机制。", "从 51 行无定理状态实现两条推论；澄清 w=−1 的假设与结论方向。", "P1"),
    ("量子化学哈密顿量语义修复", "负数值与空洞优势声明是反面教材；无可信量子优势结果。", "删除 ∃…True 公理，构造非零 H₂ 矩阵并以独立基准复核能量；不能用错误数值继续演示。", "P0"),
    ("Cook–Levin 可计算脚手架", "零债务门级实现是项目内最佳工程范式；Cook–Levin 定理未被重新证明。", "推进 Tseitin 变换的 equisatisfiability，保存可计算反例与复杂度假设，不直接跳到完整 NP 完备证明。", "P1"),
    ("Bloch 平移与周期性的接口", "平移行为是清晰可证的接口增量；另两条 True 不承载 Bloch 定理。", "先清偿 TranslationBehavior；将两条 True 改为实命题或移除并登记。", "P0"),
    ("Berry 联络的约束补全", "AbelLimit 可降级是工程增量；任意函数可称联络表明核心定义失真。", "先拆 AbelLimit，再给联络加几何约束并与曲率／线积分形成闭环。", "P0"),
    ("Berry 曲率与类型链接复", "Clairaut 委托链是后续可复用方法；原文九条平凡定理不构成曲率理论。", "修复曲率平凡化和 L3–L4 类型断裂；分别编译原树与补丁树，不把后续 worktree 修复倒填为原稿成果。", "P0"),
    ("陈数／TKNN 的真实化重建", "零占位诊断有治理价值；当前 wedge、外微分和陈数均不能支撑拓扑结论。", "实现反对称 wedge 与真实外微分；以小晶格计算非零陈数并与独立代码交叉验证。", "P0"),
    ("规范理论的假公理阻断项", "1.22=0.65 的可证伪公理是负面结果；骨架仍可作生长点。", "先移除或纠正可推 False 的断言，再实义化 trace、energyDensity 和 HodgeStar；登记受影响定理。", "P0"),
    ("超导定义与 d 波小定理", "三条易证公理和节点存在性是初等增量，不解释高温超导机制。", "清偿三条公理，机器验证 d 波节点；保持模型适用范围和物理近似显式。", "P1"),
    ("暴胀参数的谓词化治理", "Efolds 见证和 SlowRoll 谓词化是逻辑修复，不是暴胀参数推导。", "证明 Efolds 实例，将过强类型断言改为谓词并给出非平凡模型；避免全称断言引入矛盾。", "P0"),
    ("GKSL 真实骨架与语义债务", "双绘景实现值得保留；熵、速率和网络的常值 def 不是新物理。", "保留已证 GKSL 组件，逐一替换五处占位并验证示例；区分编译通过与语义忠实。", "P0"),
    ("信息几何的中心定义修复", "零矩阵诊断与 KL／Gibbs 路径有项目内价值；一般 Fisher 定理未完成。", "先闭合玩具 Hessian—CR 对照，再完成真实 FIM、KL、Gibbs 和一般 CR；不得以玩具结果晋升模块等级。", "P0"),
    ("连续极限的研究级脚手架", "十二条真定理与两条开放公理的分离是健康治理实例。", "保留尺度分析和有界性证明；实化 causalPreservation，分别检验两条谱收敛猜想。", "P1"),
    ("拓扑统计力学的编译抢救", "QGT 虚实分解可保留；原文融合叙事不构成可用理论。", "先使模块真实编译，删除悬空引用与零占位；只从 QGT 分解重建，其他五路分别验收。", "P0"),
    ("量子生物桥的占位清理", "负面前向引用与常值 helper 诊断有审计价值；没有量子生物实证。", "修复声明顺序，移除常值 helper 和 x≥x 式空洞；仅保留可独立复核的四个小定理。", "P0"),
    ("数论物理的 Selberg 债务隔离", "四条 mathlib 借力定理可保留；Montgomery–Odlyzko 的 stub 相同不是定律证明。", "修复编译，移除伪 rfl 证据；将 Selberg 断言转为明确猜想接口而非隐藏进公理。", "P0"),
    ("基本常数关系纠错", "正确关系 μ₀c/(2α) 是可核算的教材级结果；原 R_K 公式为假。", "更正并证明 R_K 关系，复跑数值一致性检查；保留 Landau 分母正性等真实证明。", "P0"),
    ("行列式复杂度的标题降级", "唯一价值是暴露占位与反向上下界；不是 Mignon–Ressayre 新证明。", "撤回下界已证措辞，替换三个零 def；把真正下界列为独立长期项目。", "P0"),
    ("NS 深度版的循环与反例治理", "诚实 docstring 可保留，但循环核与 1e8 固定界使中心声明不可接受。", "撤销解决／弱化解决措辞，构造大鼓包反例；在明确小数据条件下重新开始。", "P0"),
    ("图论电荷的可计算底座", "List 定义和非负性小定理可保留；谱界与陈数化电荷无证据。", "替换谱半径零占位和 True 公理，修正见证漏洞；先在完全图上做可计算谱验证。", "P0"),
    ("Hückel 模型从答案键到推导", "正则图拉普拉斯和键级 2/3 有真实计算价值；硬编码本征值不算推导。", "用循环矩阵 DFT 推导苯环谱，删除 n≠6 返回 0 的答案键；独立核对键级与轨道系数。", "P0"),
    ("配分函数与对角系综的核保留", "对角系综和 Ising 位运算可保留；启发式分段函数不是熵。", "替换四个零 def 与 True 公理，统一 Fisher 定义；从谱实算配分函数、熵与对角系综。", "P0"),
    ("学科桥的编译与命题真实性", "只能作为跨学科代码生成失败案例；deficiency=cyclomatic 关系本身可疑。", "先编译并删除悬空引用；用反应网络反例检验 deficiency 等式，按结果保留、修正或否决。", "P0"),
]


def cite(path: Path, label: str) -> str:
    text = path.read_text(encoding="utf-8-sig").splitlines()[0].lstrip("# ").strip()
    target = f"kimi-cite://text?path={quote(str(path))}&text={quote(text or label)}"
    return f"[{label}]({target} \"citation\")"


def main() -> None:
    math_focus = json.loads((AUDIT / "math-focus.json").read_text(encoding="utf-8"))
    assert len(math_focus) == len(MATH) == 25
    records = []
    for source, (role, novelty, unfinished, priority) in zip(math_focus, MATH):
        records.append({"id": source["id"], "series": "math", "title": source["title"], "role": role, "novelty": novelty, "unfinished": unfinished, "priority": priority, "evidence": source["id"].split(":", 1)[1]})

    readme = (TOE / "papers/模块强化_系列/README.md").read_text(encoding="utf-8")
    module_titles = re.findall(r"^\| (\d{2}) \| `([^`]+\.md)` \|", readme, re.M)
    assert len(module_titles) == len(MODULE) == 30, module_titles
    for (number, filename), (role, novelty, unfinished, priority) in zip(module_titles, MODULE):
        relative = f"papers/模块强化_系列/{filename}"
        records.append({"id": f"toe-sylva:{relative}", "series": "module", "title": f"{number}｜{Path(filename).stem}", "role": role, "novelty": novelty, "unfinished": unfinished, "priority": priority, "evidence": relative})

    assert len(records) == 55
    assert len({r["id"] for r in records}) == 55
    assert sum(r["series"] == "math" for r in records) == 25
    assert sum(r["series"] == "module" for r in records) == 30
    assert all(all(r[key].strip() for key in ("role", "novelty", "unfinished", "evidence")) for r in records)
    for r in records:
        path = TOE / r["evidence"]
        assert path.is_file(), path
        r["source_line_1"] = path.read_text(encoding="utf-8-sig").splitlines()[0]
    review_path = AUDIT / "strength-review.json"
    previous = (
        json.loads(review_path.read_text(encoding="utf-8"))["records"]
        if review_path.exists()
        else []
    )
    previous_by_id = {record["id"]: record for record in previous}
    new_ids = {record["id"] for record in records}
    for old in previous:
        if old["id"] not in new_ids and any(
            key not in RECORD_BASELINE_KEYS for key in old
        ):
            raise ValueError(f"baseline would remove extended record: {old['id']}")
    records = [
        merge_extras(record, previous_by_id.get(record["id"], {}), RECORD_BASELINE_KEYS)
        for record in records
    ]
    review_path.write_text(
        json.dumps(
            {"status": "initial_review_not_external_certification", "records": records},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )

    counts = {s: Counter(r["priority"] for r in records if r["series"] == s) for s in ("math", "module")}
    summary = {"status": "pass", "reviewed": len(records), "series": {"math": 25, "module": 30}, "priorities": counts, "unique_ids": len({r["id"] for r in records}), "evidence_files_exist": True, "external_novelty_certified": False, "machine_proofs_certified_by_this_review": False}
    summary_path = AUDIT / "strength-review-summary.json"
    previous_summary = (
        json.loads(summary_path.read_text(encoding="utf-8"))
        if summary_path.exists()
        else {}
    )
    summary = merge_extras(summary, previous_summary, SUMMARY_BASELINE_KEYS)
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    lines = [
        "# 数学基础与模块强化：55 篇逐篇方向及未竟工作初审", "",
        "> 日期：2026-11-10。范围：数学基础强化 25 篇、模块强化 30 篇。本文是基于各篇摘要、结论、局限／开放问题、系列 README 和已核 Lean 探针的**首轮裁决**，不是全库终审，更不是外部查新证明。", "",
        "## 一、裁决口径", "",
        "- **新方向**：只表示在项目内可形成独立问题族或证明工程；不自动意味着外部首创。", "",
        "- **P0**：存在假命题、循环论证、无法编译、占位替换中心对象或中心证据缺失；先修正，再扩展。", "",
        "- **P1**：有可执行的证明、计算或验证下一步；仍需保留已知假设和适用边界。", "",
        "- **P2**：长期研究或基础设施路线，近期以核查、数值证书和小接口为主。", "",
        "- 论文内的“已证”“原创”“定理”等自述不在本轮自动继承；本轮没有重新运行其全部手工推导或外部文献检索。", "",
        f"数量核对：**数学基础 P0 {counts['math']['P0']}、P1 {counts['math']['P1']}、P2 {counts['math']['P2']}；模块强化 P0 {counts['module']['P0']}、P1 {counts['module']['P1']}、P2 {counts['module']['P2']}。**合计恰为 55 个唯一 ID，证据文件均存在。", "",
        "![两组强化系列优先级](strength-review-status.png)", "",
        "图 1　优先级是本轮研究治理顺序，不是论文质量评分，也不是对外成果等级。", "",
        "## 二、两组系列构成哪些方向", "",
        "数学基础系列真正可持续的主线不是“再覆盖一个大领域”，而是四条相互支撑的证据链：**课程接口与复用登记（02／03／05／08）—非平凡定义与证明度量（01／04／07）—可复算机制链（09–17、19–22、25）—长期结构猜想（18、23、24）**。其中 05、06、07 提供了真实但有限的 Lean 证据；其余大量 Lean 段落仍是未编译设计稿，不能纳入机器定理计数。", "",
        "模块强化系列则构成一张“形式化病灶谱”：公理投影循环（04／26）、可推 False 的数值或函数界（15／24／26）、`True` 与 `subsingleton` 空洞化（05／11／12 等）、常值 def 与答案键（14／18／19／28／29）、前向引用和悬空引用（21–23／30）。这些文章适合作为修复工单和负例库，不应打包成 30 个已成立的新物理方向。", "",
        "## 三、数学基础强化：25 篇逐篇裁决", "",
        "| # | 论文 | 方向角色 | 新颖性边界 | 未竟工作与可执行下一步 | 优先级 |",
        "|---|---|---|---|---|---|",
    ]
    for index, r in enumerate([x for x in records if x["series"] == "math"], 1):
        lines.append(f"| {index:02d} | {cite(TOE / r['evidence'], r['title'])} | {r['role']} | {r['novelty']} | {r['unfinished']} | **{r['priority']}** |")
    lines += [
        "", "## 四、模块强化：30 篇逐篇裁决", "",
        "下表以系列 README 的历史诊断为起点；它记录的是各论文写作时的模块状态。后续分支若有补丁，必须给出该补丁自己的编译日志，不能据此宣称原稿原本已通过。", "",
        "| # | 论文 | 方向角色 | 新颖性边界 | 未竟工作与可执行下一步 | 优先级 |",
        "|---|---|---|---|---|---|",
    ]
    for index, r in enumerate([x for x in records if x["series"] == "module"], 1):
        lines.append(f"| {index:02d} | {cite(TOE / r['evidence'], r['title'])} | {r['role']} | {r['novelty']} | {r['unfinished']} | **{r['priority']}** |")
    lines += [
        "", "## 五、从现在起的执行顺序", "",
        "1. **阻断项先止损。** 假数值、循环核、无法编译和常值中心定义必须进入勘误或问题单；不能因论文已生成就豁免。", "",
        "2. **信息几何窄链已闭合一步。** 本轮新增 ψ″=1 时倒数为 1 的玩具恒等式，并完成真实编译；真实 FIM 与一般不等式仍独立开放。", "",
        "3. **随后处理跨系列接口冲突。** p+ip 相图与陈数符号须先统一约定、原始数据和计算脚本，再选择一个核心证明工程：K0 泛性质或 Garsia–Hopf 极大引理，二者不同时铺开。", "",
        "4. **把重复综述改造成共享接口。** p-adic／L-函数／Dedekind 与交叉联系表使用同一来源快照；陈数、Berry、几何量子化、K 理论和纽结共享“整性”问题时，必须记录共享的是数学定理还是仅有类比。", "",
        "5. **新论文的门槛后移。** 只有定义真实化、最小实例可算、证明或数据可复核、失败条件写清之后，才扩写新稿；否则优先补源文件、测试、原始结果与勘误。", "",
        "## 六、本轮实际证明：仅限玩具 Cramér–Rao 对照", "",
        "新增定理 `cramerRaoToy_inverse`，由已证的 `fisher_toy` 重写后 `norm_num` 闭合。其数学内容仅为：", "",
        "$$\\psi_{\\mathrm{toy}}''(\\mu)=1 \\quad\\Longrightarrow\\quad \\frac{1}{\\psi_{\\mathrm{toy}}''(\\mu)}=1,\\qquad \\mu\\in\\mathbb{R}.$$", "",
        f"这里 ψ_toy(μ)=μ²/2，不是任意分布族的 Fisher 信息。[探针源码](kimi-cite://text?path={quote(str(TOE / 'papers/数学基础强化_系列/_panel_records/ig_probe_20260812.lean'))}&text={quote('theorem cramerRaoToy_inverse (μ : ℝ) :')} \"citation\")", "",
        "在 `papers/数学基础强化_系列/_panel_records` 目录运行 `python verify_ig_probe_20261110.py`。使用 Lean 4.29.0 与既有 mathlib olean 缓存；本次编译器退出码 **0**，15/15 检查通过，八条探针定理的 `#print axioms` 均仅 `[propext, Classical.choice, Quot.sound]`。", "",
        f"完整命令、环境、退出码和原始输出已保存，不以文字结论替代运行证据。[编译日志](kimi-cite://text?path={quote(str(TOE / 'papers/数学基础强化_系列/_panel_records/ig_probe_compile_log_20261110.txt'))}&text={quote('退出码=0')} \"citation\")", "",
        "**边界：**它只证明二阶导为 1 时其倒数也为 1，不包含无偏估计、估计方差、样本量或一般 Cramér–Rao 不等式，也没有替换原模块的 `FIM := 0`。因此 T-待1 只能登记为“玩具链部分闭合”，不得迁移为信息几何修复完成。", "",
        "## 七、尚未覆盖与结论边界", "",
        "本轮没有完成 room_temp_sc 54 份、其他主题综述、p-adic 交叉联系表、落地验证、前沿 67 份、物理直觉 2 份和根目录独立 7 份的逐篇终审；也没有对这 55 篇逐条完成外部查新。这里的“未竟工作”是进入实际研究的入口，不代表这些研究已经完成。", "",
        "## 附：机器可读证据", "",
        "- `strength-review.json`：55 条完整记录，含 ID、角色、新颖性边界、未竟工作、优先级与证据路径。", "",
        "- `strength-review-summary.json`：数量、唯一 ID 和证据文件存在性断言结果。", "",
        "- 复核命令：`python scripts/render_strength_review.py`。退出码 0 仅表示总账结构与文件存在性检查通过，不表示数学证明或外部新颖性通过。", "",
    ]
    review_md_path = AUDIT / "STRENGTH_SERIES_REVIEW.md"
    existing_md = (
        review_md_path.read_text(encoding="utf-8") if review_md_path.exists() else ""
    )
    suffix = supplement_suffix(existing_md)
    baseline_md = "\n".join(lines).rstrip() + "\n"
    final_md = baseline_md if not suffix else baseline_md + "\n" + suffix
    review_md_path.write_text(final_md, encoding="utf-8", newline="\n")

    candidates = ["Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "Arial Unicode MS"]
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in candidates:
        if name in available:
            plt.rcParams["font.family"] = name
            break
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(10, 4.9), dpi=180)
    x = [0, 1]
    colors = {"P0": "#b94b4b", "P1": "#cc9138", "P2": "#397a76"}
    bottom = [0, 0]
    for p in ("P0", "P1", "P2"):
        vals = [counts[s][p] for s in ("math", "module")]
        bars = ax.bar(x, vals, bottom=bottom, color=colors[p], width=.52, label=p)
        for b, v, base in zip(bars, vals, bottom):
            if v:
                ax.text(b.get_x() + b.get_width()/2, base + v/2, str(v), ha="center", va="center", color="white", fontsize=13, fontweight="bold")
        bottom = [a+b for a, b in zip(bottom, vals)]
    ax.set_xticks(x, ["数学基础强化\n25 篇", "模块强化\n30 篇"])
    ax.set_ylabel("论文数")
    ax.set_ylim(0, 32)
    ax.set_title("55 篇强化系列的研究治理优先级")
    ax.legend(title="优先级", loc="upper left", frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=.16)
    fig.text(.5, .015, "P0＝先纠错或补中心证据；P1＝可执行下一步；P2＝长期路线。不是外部成果评级。", ha="center", fontsize=9, color="#4e5968")
    fig.tight_layout(rect=(0, .06, 1, 1))
    fig.savefig(AUDIT / "strength-review-status.png", bbox_inches="tight")
    svg_path = AUDIT / "strength-review-status.svg"
    fig.savefig(svg_path, bbox_inches="tight")
    # Matplotlib 在路径换行前留下空格；规范化以保持 git diff --check 干净。
    svg_path.write_text("\n".join(line.rstrip() for line in svg_path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8", newline="\n")
    plt.close(fig)
    print(json.dumps(summary, ensure_ascii=False, default=dict, indent=2))


if __name__ == "__main__":
    main()
