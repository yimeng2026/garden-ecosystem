import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType, Document, Footer, FootnoteReferenceRun, Header, HeadingLevel,
  ImageRun, ImportedXmlComponent, Math as MathEquation, MathRun, Packer,
  PageBreak, PageNumber, Paragraph, ShadingType, Table, TableCell, TableRow,
  TextRun, WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_report.js /absolute/path/REPORT.docx");
const root = path.dirname(outputPath);
const data = JSON.parse(fs.readFileSync(path.join(root, "results.json"), "utf8"));
const comparisons = Object.fromEntries(data.comparisons.map((row) => [`${row.n}-${row.strength}-${row.target}`, row]));
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
const equation = (text) => para(new MathEquation({ children: [new MathRun(text)] }), { alignment: AlignmentType.CENTER, spacing: { before: 65, after: 80 } });
const footnote = (text) => para(run(text, { size: 15 }), { spacing: { after: 30, line: 190 } });
const titles = ["一、无序模型与均值匹配", "二、全部实现与参数相关结果", "三、独立验证与结论边界"];
const selected = [[160, 0.1], [320, 0.1], [160, 0.2], [320, 0.2]];
const selectedRows = [];
for (const [n, strength] of selected) {
  for (const target of ["zero", "pi"]) {
    const row = comparisons[`${n}-${strength}-${target}`];
    selectedRows.push([String(n), String(strength), target === "zero" ? "0" : "π", `${row.disorder_pass_count}/${row.total}`, `${row.uniform_mean_pass_count}/${row.total}`, `${row.outcome_agreement_count}/${row.total}`]);
  }
}
const children = [
  para(run("弱化学势无序下 Floquet 0／π 候选", { bold: true, size: 34, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("无序与平均 kick 匹配对照", { bold: true, size: 29, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  para(run("108 个无序实现＋108 个均匀对照 · 不筛选种子", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 210 } }),
  para(run("2026-11-11　主检验不支持；不能归因于无序单独破坏", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4][index] }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("无序只改变化学势 δ 脉冲，采用 a_n=rβ_n；自由演化、周期、 hopping 和 pairing 均不变。均匀均值匹配对照使用 a_n=r·mean(β)，因此可区分平均驱动条件与空间涨落。", 1),
  equation("a_n = r β_n,　a_uniform,n = r mean(β),　U = K(β) F K(β)"),
  makeTable(["项目", "固定协议"], [
    ["尺寸与实现", "N=80、160 各 16 个；N=320 前 4 个"],
    ["强度", "r=0.05、0.1 为主检验；r=0.2 为压力测试"],
    ["随机序列", "default_rng(20261111+seed).random(320)[:N]，跨强度和尺寸复用"],
    ["观测量", "谱分离、端点权重、基无关子空间 IPR、第二对诊断"],
    ["附加控制", "逐实现均值匹配与零 kick 参照"],
  ], [2200, 7306], 13),
  body("不把不同实现的本征值平均成单一真实样品。平移不变 Bloch winding 不用于无序链；本轮只评估有限实现的数值候选稳健性。"),
  makeTable(["判据层级", "规则", "本轮结果"], [
    ["主检验", "全部或多数实现满足 separation<0.1、edge_weight>0.5", data.assessment.status],
    ["压力测试", "r=0.2 单独报告，不抵消主检验", "部分组合通过"],
    ["全尺寸旧判据", data.assessment.full_size_rule_status, "不改阈值、不改旧记录"],
  ], [1900, 4800, 2806], 13),
  pageBreak(),

  heading(titles[1]),
  citedBody("主检验不支持，但弱强度失败常与均匀平均 kick 对照重合，不能归因于无序单独破坏。部分模态在特定强度和尺寸下仍表现稳健。全部实现和失败记录均保存在原始数据中。", 2),
  makeTable(["N", "r", "模", "无序通过", "均匀均值通过", "判定一致"], selectedRows, [650, 650, 550, 2000, 2500, 3156], 12),
  body("N=160、r=0.1 的 0 模无序为 1/16，而均匀均值为 16/16；π 模两者均为 16/16。N=320 同强度的 0 模分别为 1/4 和 4/4，π 模均为 4/4。这里显示模态与参数相关的无序敏感性，不能推广为所有弱无序均破坏拓扑。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "disorder.png")), transformation: { width: 480, height: Math.round(480 * 1496 / 2180) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　全部无序通过数、均匀均值对照和全部种子端点权重。", { size: 17, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("独立复核重新构造选定无序实现的自由部分和解析 kick，检查正交性、子空间旋转不变性、均值匹配、原始通过数及全部 CSV。5 项模型合同和 6 项独立检查均通过。", 3),
  makeTable(["证据层", "实际结果", "不能推出"], [
    ["主检验", data.assessment.status, "不能宣称所有弱无序实现均稳健"],
    ["弱强度失败", "常与均匀平均 kick 对照重合", "不能归因于无序单独破坏"],
    ["N=160、r=0.1", "0 模 1/16 对 16/16；π 模 16/16 对 16/16", "模态与参数相关，不能泛化"],
    ["r=0.2 压力测试", "N=160 各 15/16；N=320 各 4/4", "不抵消主检验失败"],
    ["无序拓扑", "未计算无序 winding", "不宣称拓扑不变量、热力学极限或材料 Tc"],
  ], [1900, 4300, 3306], 13),
  citedBody("本研究不含相互作用、耗散、自洽配对、材料 Tc 或实验复现。有限实现的通过与否必须与平均 kick、尺寸和模态共同解释。", 4),
  body("复现命令：python research/floquet-bdg-disorder/run_verification.py。原始数据见 results.json、realizations.csv、mean_matched.csv、disorder_sequences.npz 和 profiles.npz；均值对照说明见 MEAN_CONTROL.md。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "弱化学势无序下 Floquet 0／π 候选：无序与平均 kick 匹配对照",
  description: "108 个无序实现、108 个均匀均值对照及有限实现边界。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("Mondal, Sen and Dutta, arXiv:2203.16353v3, Eq. (7). Chemical-potential kick-only spatial disorder; no hopping disorder, temporal noise, interactions or dissipation.")] },
    2: { children: [footnote("Source: results.json, realizations.csv, mean_matched.csv, disorder_sequences.npz and profiles.npz. All realizations and failures are retained; no eigenvalue averaging is used as a single sample.")] },
    3: { children: [footnote("Source: verify_disorder.py and run.log. Independent reconstruction, analytic kick, mean matching, subspace rotation invariance and raw pass-count checks.")] },
    4: { children: [footnote("Source: MEAN_CONTROL.md and results.json scope. No disorder winding, thermodynamic-limit proof, material Tc prediction, non-equilibrium steady-state proof or experimental validation.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 无序与均值匹配", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
