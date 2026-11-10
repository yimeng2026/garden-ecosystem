import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathFraction, MathRun,
  Packer, PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell,
  TableRow, TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REPORT.docx");
const root = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(root, "disorder_results.json"), "utf8"));
const independent = JSON.parse(fs.readFileSync(path.join(root, "disorder_independent.json"), "utf8"));
const baseline = JSON.parse(fs.readFileSync(path.join(root, "results.json"), "utf8"));
const oldDisorder = JSON.parse(fs.readFileSync(path.join(path.dirname(root), "floquet-bdg-disorder", "results.json"), "utf8"));
const font = { ascii: "Times New Roman", hAnsi: "Times New Roman", cs: "Times New Roman", eastAsia: "SimSun" };
const palette = { dark: "293B40", primary: "356A64", accent: "A25B3F", light: "687A7E", fill: "EDF3F1" };
const run = (text, options = {}) => new TextRun({ text: String(text), font, size: 20, ...options });
const para = (children, options = {}) => new Paragraph({ spacing: { after: 100, line: 270 }, ...options, children: Array.isArray(children) ? children : [children] });
const body = (text) => para(run(text), { indent: { firstLine: 400 } });
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 24, color: palette.dark }), { heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2, spacing: { before: 200, after: 110 }, keepNext: true });
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs><w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr><w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent><w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/><w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText><w:fldChar w:fldCharType="separate"/></w:r></w:p>${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 13) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 190 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 30, bottom: 30, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 13) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const fmt = (value, digits = 6) => value === null || value === undefined ? "—" : typeof value === "string" ? value : Number(value).toPrecision(digits).replace(/\.0+$/, "");
const titles = ["一、模型、时间帧与振幅勘误", "二、静态与洁净 kicked 基准", "三、无序与均匀均值结果", "四、未收敛类别与独立复核", "五、科学边界与复现"];
const baselineRows = [
  ["静态拓扑 ω=7", "0", baseline.static.topological_omega7.zero],
  ["静态拓扑 ω=7", "π", baseline.static.topological_omega7.pi],
  ["静态平凡 ω=17", "0", baseline.static.trivial_omega17.zero],
  ["静态平凡 ω=17", "π", baseline.static.trivial_omega17.pi],
  ["洁净 kicked N=80", "0", baseline.clean.zero],
  ["洁净 kicked N=80", "π", baseline.clean.pi],
].map(([name, target, row]) => [name, target, fmt(row.value, 12), String(row.nearest_integer), fmt(row.min_bulk_gap)]);
const summaryRows = data.summary.map((row) => [
  String(row.strength), row.kind === "disorder" ? "无序" : "均匀均值", row.target === "zero" ? "0" : "π",
  `${row.valid_winding_count}/4`, Object.entries(row.nearest_integer_frequencies).map(([key, value]) => `${key}:${value}`).join("；"),
  fmt(row.minimum_bulk_gap), `${row.endpoint_joint_pass_count}/4`,
]);
const ncRows = [];
for (const row of data.realizations) {
  for (const target of ["zero", "pi"]) {
    if (row[target].status === "ok") continue;
    const check = independent.checks.find((item) => item.strength === row.strength && item.seed === row.seed && item.kind === row.kind && item.target === target);
    ncRows.push([String(row.strength), String(row.seed), target === "zero" ? "0" : "π", fmt(row[target].rows[0].value, 9), fmt(row[target].rows[1].value, 9), row[target].status, fmt(check.independent.value, 9)]);
  }
}
const independentRows = independent.checks.map((row) => [
  String(row.strength), String(row.seed), row.kind === "disorder" ? "无序" : "均值", row.target === "zero" ? "0" : "π",
  `${row.production_status}/${row.production_nearest_integer ?? "—"}`,
  `${row.independent.status}/${row.independent.nearest_integer ?? "—"}`,
]);
const children = [
  para(run("Floquet-BdG TBC dynamical winding", { bold: true, size: 33, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 500, after: 190 } }),
  para(run("无序与均匀均值对照", { bold: true, size: 30, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 220 } }),
  para(run("N=80 · 12 个无序实现＋12 行配对均值控制", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 180 } }),
  para(run("2026-11-11　含双倍振幅勘误与独立行列式复核", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: index + 2 }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("TBC 只给 N→1 闭合键附加 exp(iθ)。静态和洁净基准要求端点单位元、unitary、0／π 半周期 chiral 块同时成立；任何失败均停止晋升。", 1),
  equation("Ustep(t)=F(t)H　(0<t<T),　Ustep(T)=H F(T)H,　Ustep(0)=I"),
  equation("φeff,val = 2ε−|φ|,　φeff,cond = |φ|−2π"),
  equation([new MathRun("Wε = |±"), new MathFraction({ numerator: [new MathRun("i")], denominator: [new MathRun("2π")] }), new MathRun(" ∫ Tr[(Uε±(θ))−1 ∂θUε±(θ)] dθ|")]),
  citedBody("无序 K 矩阵 onsite 参数为 rβ，半 kick 旋转角为 rβ，完整对称旋转角为 2rβ。双倍矩阵参数的早期检查点已归档为诊断，不参与结论。", 5),
  makeTable(["检查项", "失败或风险", "修正后的实测合同"], [
    ["kick 时间帧", "非对称形式对称误差约 0.34–0.56", "时间有序对称帧约 10⁻¹⁵–10⁻¹⁴"],
    ["近简并分解", "普通本征向量可破坏 unitary", "酉 Schur 谱函数保持 unitary"],
    ["无序振幅", "2rβ 矩阵参数差异约 9.76×10⁻²", "rβ 与旧半 kick 差约 1.39×10⁻¹⁷"],
    ["主积分收敛", "dθ=0.05/0.025 两格点可未收敛", "保留 NC；独立 det 相位只作复核"],
  ], [2100, 3900, 3506], 12),
  pageBreak(),

  heading(titles[1]),
  citedBody("静态拓扑、静态平凡、奇点拒绝及洁净 kicked 全部通过后，才允许无序计算。洁净 N=80 的 W0、Wπ 与既有 p0=pπ=1 一致。", 2),
  makeTable(["算例", "隙", "winding 原始值", "整数", "最小体隙"], baselineRows, [2500, 550, 3000, 750, 2706], 12),
  body("静态 μ0=2.5、ω=7 的 0 体隙关闭，状态为 gapless_or_undefined，未记为 0。独立静态／洁净行列式相位绕数分别精确为相应整数。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "disorder-winding.png")), transformation: { width: 475, height: Math.round(475 * 1715 / 1475) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　逐实现 winding；叉号未收敛，空心菱形为独立复核。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("三种强度共 12 个无序实现，每个均配一行均匀均值控制。均匀控制在同一强度内是同一均匀链，配对列出四次不等于四个独立随机样本。", 3),
  makeTable(["r", "类型", "隙", "有效/4", "整数频数", "最小体隙", "端点通过/4"], summaryRows, [550, 1150, 450, 950, 1600, 2000, 2806], 10),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "disorder-gaps.png")), transformation: { width: 455, height: Math.round(455 * 1715 / 1490) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 2　最小体隙与有限开链端点联合判据；纵轴为对数坐标。", { size: 16, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[3]),
  body("主积分器在 48 个能隙结果中给出 46 个有效结果，最近整数均为 1。下列两个 0 支保持 not_converged；独立行列式相位为 1，不 retroactively 修改主状态，也不记为 0。"),
  makeTable(["r", "seed", "隙", "dθ≈0.05", "dθ≈0.025", "主状态", "独立 det"], ncRows, [600, 650, 450, 1650, 1650, 2500, 2006], 11),
  citedBody("独立方法重建矢量无序传播、酉 Schur 周期化和 det(block) 相位展开。14 项代表与失败类别检查全部执行；所有主结果有效项的整数一致。", 6),
  makeTable(["r", "seed", "类型", "隙", "主状态/整数", "独立状态/整数"], independentRows, [550, 600, 950, 450, 3400, 3556], 10),
  pageBreak(),

  heading(titles[4]),
  makeTable(["判断层", "当前证据", "不得外推"], [
    ["体 winding", "46/48 主结果有效且为 1；2 个 NC 独立为 1", "不证明任意无序、尺寸或热力学极限"],
    ["无序端点", "0 模联合判据 0/12；π 模 2/12", "不宣称 N=80 端点模全部通过"],
    ["旧无序主检验", oldDisorder.assessment.status, "不因体 winding 改写为 supported"],
    ["全尺寸旧判据", oldDisorder.assessment.full_size_rule_status, "保留原未决状态"],
    ["材料与实验", "未计算", "不推导 Tc、相互作用、耗散、Meissner 或实验"],
  ], [2000, 4200, 3306], 11),
  citedBody("原有无序端点主检验和全尺寸未决状态均保留。体 winding 与端点候选回答不同问题，不能用其中一套判据覆盖另一套。", 7),
  body("复现命令：python research/floquet-bdg-tbc/run_verification.py。原始证据：disorder_results.json、disorder_results.csv、disorder_independent.json、results.json、run.log；双倍振幅诊断及 ERRATA.md 单独保留。"),
  body("Word 图件顺序：图 1 在基准后、汇总前；图 2 在汇总后、未收敛前。Markdown 版本在各插入处另有明确标注。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet-BdG TBC dynamical winding：无序与均匀均值对照",
  description: "N=80 无序与均匀均值 winding、双倍振幅勘误、端点对照和独立行列式复核。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("Mondal et al., arXiv:2207.11928v2, Eq. (7)–(16). Implementation time frame and branch conventions are selected by independent endpoint and chiral contracts.")] },
    2: { children: [footnote("Thakurathi et al., arXiv:1303.2300v2; results.json and independent_verification.json. Static and clean-kicked finite quadratic baselines only.")] },
    3: { children: [footnote("disorder_results.json and disorder_results.csv. Twelve disordered realizations plus twelve paired control rows; uniform controls are repeated pair references, not independent random samples.")] },
    5: { children: [footnote("ERRATA.md and probe_kick_amplitude.py. Double-parameter diagnostics are preserved separately and excluded from scientific conclusions.")] },
    6: { children: [footnote("disorder_independent.json. Fourteen independent vector-mu determinant-phase checks, including both production nonconvergence categories.")] },
    7: { children: [footnote("floquet-bdg-disorder/results.json. Earlier not_supported and inconclusive_preserved scopes remain unchanged; no thermodynamic or experimental claim.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 900, bottom: 900, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · TBC 无序对照", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
