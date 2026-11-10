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
const body = (text, options = {}) => para(run(text), { indent: { firstLine: 400 }, ...options });
const citedBody = (text, id) => para([run(text), new FootnoteReferenceRun(id)], { indent: { firstLine: 400 } });
const heading = (text, level = 1) => para(run(text, { bold: true, size: level === 1 ? 29 : 24, color: palette.dark }), {
  heading: level === 1 ? HeadingLevel.HEADING_1 : HeadingLevel.HEADING_2,
  spacing: { before: 200, after: 110 }, keepNext: true,
});
const pageBreak = () => new Paragraph({ children: [new PageBreak()] });
const xmlEscape = (value) => String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
const toc = (entries) => {
  const cached = entries.map(({ title, level, page }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
    <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs>
    <w:ind w:left="${Math.max(0, level - 1) * 360}"/></w:pPr>
    <w:r><w:t>${xmlEscape(title)}</w:t></w:r><w:r><w:tab/></w:r><w:r><w:t>${page}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent></w:sdt>`).root[0];
};
const cell = (text, index, widths, header, size = 14) => new TableCell({
  children: [para(run(text, { size, bold: header }), { spacing: { after: 0, line: 195 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 25, bottom: 25, left: 65, right: 65 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const makeTable = (headers, rows, widths, size = 14) => new Table({
  width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA }, columnWidths: widths,
  rows: [
    new TableRow({ tableHeader: true, cantSplit: true, children: headers.map((text, index) => cell(text, index, widths, true, size)) }),
    ...rows.map((row) => new TableRow({ cantSplit: true, children: row.map((text, index) => cell(text, index, widths, false, size)) })),
  ],
});
const equation = (children) => para(new MathEquation({ children: Array.isArray(children) ? children : [new MathRun(children)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const sci = (value) => Number(value).toExponential(6);
const titles = ["一、模型与解析基准", "二、有限尺寸数值结果", "三、控制、独立验证与边界"];
const resultRows = [];
for (const study of data.size_studies) {
  for (const [target, label] of [["zero", "0"], ["pi", "π"]]) {
    const row = study[target];
    resultRows.push([
      String(study.n), label, sci(Math.max(...row.distances)), sci(row.bulk_distance),
      Math.max(...row.separation_ratios).toFixed(6), Math.min(...row.edge_weights).toFixed(6),
      data.convergence[target].finite_size_status,
    ]);
  }
}
const children = [
  para(run("有限 Floquet–BdG 数值切片", { bold: true, size: 38, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("开放 Kitaev 链的 0／π 模", { bold: true, size: 30, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  para(run("精确分段传播 · 解析端点计数 · 有限尺寸与独立谱检验", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 210 } }),
  para(run("2026-11-11　π 模通过当前判据；0 模分离仍未闭合", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4][index] }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("模型采用无相互作用开放 Kitaev 链和化学势周期 δ 脉冲。参数 γ=Δ=1、μ0=2.5、μ1=0.2、ω=7；ℏ=1。Majorana 基为 (a1,b1,...,aN,bN)，H=iΣKrsΓrΓs。", 1),
  equation([new MathRun("T = "), new MathFraction({ numerator: [new MathRun("2π")], denominator: [new MathRun("ω")] })]),
  equation("F = exp[−4K(μ₀)T],　S = exp[−2K(μ₁)],　U = SFS"),
  equation([
    new MathRun("b₀ = "), new MathFraction({ numerator: [new MathRun("4(μ₀−γ)")], denominator: [new MathRun("ω")] }),
    new MathRun(" + "), new MathFraction({ numerator: [new MathRun("2μ₁")], denominator: [new MathRun("π")] }),
    new MathRun(",　bπ = "), new MathFraction({ numerator: [new MathRun("4(μ₀+γ)")], denominator: [new MathRun("ω")] }),
    new MathRun(" + "), new MathFraction({ numerator: [new MathRun("2μ₁")], denominator: [new MathRun("π")] }),
  ]),
  makeTable(["项目", "实现", "边界"], [
    ["Onsite", "K[a_j,b_j]=−μ", "δ 脉冲只改化学势"],
    ["Hopping／pairing", "K[a_j,b_(j+1)]=(Δ−γ)/2；K[a_(j+1),b_j]=−(Δ+γ)/2", "实反对称矩阵"],
    ["Floquet", "自由—半脉冲—自由，矩阵指数", "无 Fourier 截断，不伪报截断收敛"],
    ["静态解析基准", "μ=0、γ=Δ 时 a1 和 bN 属于精确零空间", "检查 Majorana 符号与矩阵构造"],
  ], [1700, 5000, 2806], 13),
  heading("解析端点计数不等于有限尺寸证明", 2),
  body(`b0=${data.endpoint_invariants.b0.toFixed(9)}，bπ=${data.endpoint_invariants.b_pi.toFixed(9)}；区间内的偶整数为 ${data.endpoint_invariants.even_integers.join(",")}，奇整数为 ${data.endpoint_invariants.odd_integers.join(",")}。在限定参数域内，解析预期为每端 p0=1、pπ=1。开放链数值另行计算，不以预期覆盖本征值。`),
  pageBreak(),

  heading(titles[1]),
  citedBody(`π 模为 ${data.convergence.pi.finite_size_status}：距离随尺寸下降且分离、局域判据均通过。0 模为 ${data.convergence.zero.finite_size_status}：虽趋近 +1 并增强局域，但 N=160 最大分离比为 ${Math.max(...data.size_studies.at(-1).zero.separation_ratios).toFixed(6)}，不能登记为通过。`, 2),
  makeTable(["N", "模", "最大距离", "体模距离", "最大分离比", "最小边缘权重", "裁决"], resultRows, [500, 400, 1330, 1300, 1150, 1350, 3476], 11),
  body("候选取距 λ=+1 或 −1 最近的两个本征值；边缘权重为两端各 10% 格点概率之和。联合判据预注册为分离比<0.1、边缘权重>0.5，且距离随尺寸严格下降、首尾至少缩小 2 倍。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "quasienergy.png")), transformation: { width: 560, height: Math.round(560 * 1496 / 2180) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　实际相位谱、候选距离、端点权重及 N=160 空间分布；所有点来自数值结果。", { size: 17, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  makeTable(["检查", "实际结果", "裁决"], [
    ["静态平凡 0 候选", `最大边缘权重 ${Math.max(...data.static_trivial_control.zero.edge_weights).toFixed(6)}；最大分离比 ${Math.max(...data.static_trivial_control.zero.separation_ratios).toFixed(6)}`, "联合判据不通过"],
    ["静态平凡 π 候选", `最大边缘权重 ${Math.max(...data.static_trivial_control.pi.edge_weights).toFixed(6)}；最大分离比 ${Math.max(...data.static_trivial_control.pi.separation_ratios).toFixed(6)}`, "有分离但局域不足，不通过"],
    ["静态解析零空间", "a1、bN 与 K 的乘积在数值精度内为零", "矩阵约定基准通过"],
  ], [1900, 4900, 2706], 13),
  citedBody(`N=160 的独立稀疏 shift-invert 对照中，0 与 π 附近谱对稠密谱的最大差分别为 ${sci(data.dense_sparse_comparison.zero.max_absolute_difference)} 和 ${sci(data.dense_sparse_comparison.pi.max_absolute_difference)}，均小于 10⁻¹²。`, 3),
  makeTable(["仍未完成", "当前边界"], [
    ["0 模拓扑确认", "最近体模分离不足；需体隙／拓扑指标或更长链，不修改阈值"],
    ["π 模进一步验证", "需 Floquet 拓扑不变量、微扰稳健性和独立实现"],
    ["连续驱动收敛", "δ 脉冲无 Fourier 截断；连续驱动需另做时间步或截断研究"],
    ["材料与实验", "无相互作用、耗散、自洽配对、占据、Tc、Meissner 或实验验证"],
    ["热力学极限", "有限尺寸证据不是极限证明"],
  ], [2500, 7006], 13),
  citedBody("本报告只验证有限二次型模型的数值谱和边缘候选。它不推导 Floquet 超导增强，不计算材料 Tc，不验证非平衡稳态，也不构成独立实验复现。", 4),
  body("复现命令：python research/floquet-bdg/run_verification.py。原始数据见 results.json、candidates.csv、spectra.npz 和 run.log；Markdown 说明见 README.md。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "有限 Floquet–BdG：开放 Kitaev 链的 0／π 模",
  description: "精确分段传播、解析基准、有限尺寸结果、静态控制与独立稀疏谱验证。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({
    id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true,
    run: { font, size: 19, color: palette.dark },
    paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } },
  })) },
  footnotes: {
    1: { children: [footnote("Thakurathi et al., Phys. Rev. B 88, 155133 (2013), arXiv:1303.2300; Mondal et al., arXiv:2203.16353v3, Eqs. (4)–(6). Matrix convention independently checked against static null vectors.")] },
    2: { children: [footnote("Source: results.json, candidates.csv and spectra.npz. Raw eigenvalues and preregistered candidate/separation/localization criteria; no candidate label is substituted for numerical evidence.")] },
    3: { children: [footnote("Source: results.json dense_sparse_comparison; scipy.sparse.linalg.eigs, k=6, sigma=±1, tol=1e-12, ncv=40, N=160.")] },
    4: { children: [footnote("Source: floquet_bdg.py and results.json scope. No interactions, dissipation, self-consistent pairing, material Tc prediction, thermodynamic-limit proof or experimental validation.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · π 通过／0 未决", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
