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
const data = JSON.parse(fs.readFileSync(path.join(root, "results.json"), "utf8"));
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
const cell = (text, index, widths, header, size = 14) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 195 } })],
  width: { size: widths[index], type: WidthType.DXA }, margins: { top: 25, bottom: 25, left: 65, right: 65 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 14) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }), ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) }))],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const titles = ["一、基无关方法与方法修正", "二、尾部、包络与尺寸证据", "三、独立验证与结论边界"];
const children = [
  para(run("Floquet–BdG 短链局域尺度", { bold: true, size: 37, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("0／π 边缘模的基无关证据", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  para(run("尾部亏损 · 镜像包络 · 子空间 IPR · 独立求解器", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 210 } }),
  para(run("2026-11-11　短链 regime 支持；全尺寸旧判据不变", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4][index] }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("有限尺寸边缘模需要联合本征值、能隙、波函数和 IPR。接近严格简并时，单个本征向量可任意旋转，单个 IPR 不再适合直接比较；本研究改用二维候选子空间的基无关指标。", 1),
  equation("ρ = QQ†,　I2 = Σ_m (ρ_mm)²,　w_j = [ρ_(a_j,a_j)+ρ_(b_j,b_j)]/2"),
  equation([new MathRun("ξ_tail = "), new MathFraction({ numerator: [new MathRun("−2f(N2−N1)")], denominator: [new MathRun("log(1−E_N2)−log(1−E_N1)")] })]),
  makeTable(["方法问题", "修正后的处理", "禁止的解释"], [
    ["严格简并", "QR 正交化后构造 ρ=QQ†；使用 Σρ_mm²", "不把任意本征向量 IPR 翻倍当成退局域"],
    ["延展第二对", "IPR 衰减，N×IPR 保持有限", "不写成 N×IPR 必须增长"],
    ["尾部长度", "亏损为正且递减时才估计 ξ_tail", "不对无效符号取绝对值"],
    ["包络拟合", "报告 ξ_env、R² 和残差", "不把单尺度拟合当成拓扑证明"],
  ], [2100, 4300, 3106], 13),
  body("方法修正记录保留在 METHOD.md。旧全尺寸 inconclusive 不改；本研究只回答短链局域 regime 是否有独立证据，不把方法修正当成结果导向的阈值调整。"),
  pageBreak(),

  heading(titles[1]),
  citedBody("尾部估计、包络拟合和子空间 IPR 均来自 Fock 修正后的同一组 N=40、80、160、320、640 开放链数据。所有原始格点分布和第二对谱均已保存。", 2),
  makeTable(["模", "40/80 ξ_tail", "80/160 ξ_tail", "160/320 ξ_tail", "320/640 ξ_tail"], [["zero", "0"], ["pi", "π"]].map(([target, label]) => [label, ...data.tail_estimates[target].map((row) => row.xi_tail.toFixed(6))]), [900, 2000, 2000, 2000, 2606], 13),
  makeTable(["N", "0 模 ξ_env / R²", "π 模 ξ_env / R²"], data.sizes.map((n, index) => {
    const zero = data.envelope_fits.zero[index];
    const pi = data.envelope_fits.pi[index];
    return [String(n), `${zero.xi_env.toFixed(6)} / ${zero.r_squared.toFixed(4)}`, `${pi.xi_env.toFixed(6)} / ${pi.r_squared.toFixed(4)}`];
  }), [1000, 4250, 4256], 13),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "localization.png")), transformation: { width: 520, height: Math.round(520 * 1496 / 2180) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　端点权重、尾部估计、基无关 IPR 与包络长度；均为实际数值。", { size: 17, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  makeTable(["模", "第一对 I₂ 相对变化", "第二对 I₂ 衰减因子", "第二对 N×I₂ 比值"], [["zero", "0"], ["pi", "π"]].map(([target, label]) => {
    const row = data.assessment.criteria[target].metrics;
    return [label, row.first_pair_subspace_ipr_relative_change.toExponential(3), row.second_pair_subspace_ipr_decay_factor.toFixed(6), row.second_pair_n_subspace_ipr_ratio.toFixed(6)];
  }), [1000, 3000, 2800, 2706], 13),
  citedBody("独立验证使用 scipy.linalg.eig 重算 N=640，重新构造子空间 ρ，并比较 IPR、逐格点权重和端点权重。6 项独立检查通过；基旋转合同、尾部公式、包络尺度和原始文件哈希也均通过。", 3),
  makeTable(["判断层", "当前状态", "边界"], [
    ["短链 regime", data.assessment.status, "当前参数下有尾部、包络和 IPR 联合支持"],
    ["全尺寸旧判据", data.assessment.full_size_rule_status, "N=40 的 0 模 0.495972、π 模 0.190995；不移动阈值"],
    ["最大尺寸", "N=640 的 0／π 候选满足原分离与局域阈值", "仍不是热力学极限证明"],
    ["材料与实验", "未涉及", "不推导 Tc、Meissner、耗散稳态或实验复现"],
  ], [1900, 4100, 3506], 13),
  citedBody("本结果仅说明当前二次型 Kitaev 模型的短链局域 regime。它不修改旧全尺寸判据，不构成材料超导增强、非平衡稳态或实验验证。", 4),
  body("复现命令：python research/floquet-bdg-localization/run_verification.py。原始数据见 results.json、localization.csv、profiles.npz；方法修正见 METHOD.md，验证退出码见 run.log。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet–BdG 短链局域尺度：0／π 边缘模的基无关证据",
  description: "尾部亏损、镜像包络、基无关子空间 IPR 和独立求解器验证。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("Thakurathi, Patel, Sen and Dutta, Phys. Rev. B 88, 155133 (2013), arXiv:1303.2300v2. Method metadata: sources/scholar-majorana.csv. Third-party citation counts are not used as physical evidence.")] },
    2: { children: [footnote("Source: results.json, localization.csv and profiles.npz. Current Fock-corrected model; tail, envelope and basis-invariant subspace metrics are computed from raw eigenvectors.")] },
    3: { children: [footnote("Source: verify_localization.py. Independent scipy.linalg.eig calculation at N=640, basis-rotation invariance and scaling checks; actual exit codes are recorded in run.log.")] },
    4: { children: [footnote("Source: METHOD.md and results.json scope. No interactions, dissipation, self-consistent pairing, material Tc, thermodynamic-limit proof or experimental validation.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 短链局域与基无关 IPR", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
