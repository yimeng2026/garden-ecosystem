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
const sensitivity = JSON.parse(fs.readFileSync(path.join(root, "sensitivity.json"), "utf8"));
const disorder = JSON.parse(fs.readFileSync(path.join(path.dirname(root), "floquet-bdg-disorder", "results.json"), "utf8"));
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
const titles = ["一、解析奇点与均匀模型", "二、有限尺寸参数图", "三、无序分解与验证边界"];
const islandRows = data.pass_islands.filter((row) => row.n !== 640).map((row) => [String(row.n), row.target === "zero" ? "0" : "π", `${row.start}–${row.end}`, "网格样本，不是精确相界"]);
const categoryRows = [];
for (const n of [160, 320]) {
  for (const target of ["zero", "pi"]) {
    const total = n === 160 ? 16 : 4;
    const count = (category) => sensitivity.summary.filter((row) => row.n === n && row.strength === 0.1 && row.target === target && row.category === category).reduce((sum, row) => sum + row.count, 0);
    categoryRows.push([String(n), "0.1", target === "zero" ? "0" : "π", `${count("both_pass")}/${total}`, `${count("fluctuation_sensitive")}/${total}`, `${count("uniform_fails")}/${total}`, `${count("fluctuation_assisted")}/${total}`]);
  }
}
const children = [
  para(run("均匀 kick 参数图与无序涨落分解", { bold: true, size: 35, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 600, after: 220 } }),
  para(run("解析奇点 · 有限尺寸网格 · 均值与涨落对照", { bold: true, size: 27, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  para(run("45 个均匀参数点＋216 行无序分解", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 210 } }),
  para(run("2026-11-11　边界明确；原 not_supported 不变", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 300 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4][index] }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("固定 γ=Δ=1、μ0=2.5、ω=7。均匀 kick 只改变化学势脉冲振幅，复用 Fock 校验模型。端点整数计数只在非奇点参数域内使用。", 1),
  equation("b0 = 4(μ0−γ)/ω + 2a/π,　bπ = 4(μ0+γ)/ω + 2a/π"),
  equation([new MathRun("a_c = "), new MathFraction({ numerator: [new MathRun("π")], denominator: [new MathRun("14")] }), new MathRun(",　U(0)=+I,　U(π)=−I")]),
  makeTable(["参数点", "负 hopping 映射与实际矩阵", "端点计数"], [
    ["a=0", "k=0 → bπ=2；U(0)=+I", "gapless_or_undefined"],
    ["a_c=π/14≈0.2243994753", "k=π → b0=1；U(π)=−I", "gapless_or_undefined"],
    ["a=0.22<a_c", "pπ=1；N=320 π 候选通过", "与解析转变一致"],
    ["a=0.24>a_c", "pπ=0；N=320 π 候选未通过", "与解析转变一致"],
  ], [2400, 4600, 2506], 13),
  body("两个唯一奇异振幅在 N=80、160、320 各出现一次，共 6 条奇点记录。N=640 只取 0.05、0.1、0.2 三个复核点，不把稀疏点解释为连续区间。"),
  pageBreak(),

  heading(titles[1]),
  citedBody("45 个均匀参数点全部保留。通过区间只表示当前网格与候选联合判据，不能替代解析相界或独立的拓扑证明。", 2),
  makeTable(["N", "模", "网格通过区间", "区间语义"], islandRows, [900, 700, 2300, 5606], 13),
  body("N=640 的三个选定振幅 0.05、0.1、0.2 均满足当前候选联合判据，但不外推为连续区间，也不构成热力学极限证明。"),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "kick-map.png")), transformation: { width: 500, height: Math.round(500 * 1496 / 2178) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　均匀 0／π 通过图、无序与均匀均值、机械类别分解。", { size: 17, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[2]),
  citedBody("逐实现严格分解 rβ_n = r·mean(β) + r(β_n−mean(β))，并保存涨落 RMS、谱距离差、端点权重差和子空间 IPR 差。机械类别不表示拓扑生灭。", 3),
  makeTable(["N", "r", "模", "均通过", "涨落敏感", "均匀失败", "涨落助通过"], categoryRows, [550, 550, 500, 1750, 1900, 1900, 2356], 11),
  body("N=160、r=0.1 的 0 模有 15/16 为 fluctuation_sensitive、1/16 为 both_pass；π 模 16/16 均为 both_pass。N=320 的 0 模为 3/4 敏感、1/4 均通过，π 模 4/4 均通过。结果与此前均值匹配一致，但不构成无序 winding。"),
  makeTable(["判断层", "当前结果", "保留边界"], [
    ["原无序主检验", disorder.assessment.status, "不因参数图改写"],
    ["全尺寸旧判据", data.scope.full_size_rule_status, "仍不宣称全尺寸通过"],
    ["无序拓扑", "未计算无序 winding", "不宣称无序拓扑不变量"],
    ["材料与实验", "未涉及", "不推导材料 Tc、耗散稳态或实验复现"],
  ], [2000, 3800, 3706], 13),
  citedBody("独立复核重建均匀链，检查奇点动量和符号、临界前后计数、无序均值恒等式及子空间旋转不变性。45 个参数点、216 行分解和全部 CSV 均与当前报告一致。", 4),
  body("复现命令：python research/floquet-kick-map/run_verification.py。原始数据见 results.json、sensitivity.json、uniform_grid.csv、sensitivity.csv 和 profiles.npz；验证退出码见 run.log。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "均匀 kick 参数图与无序涨落分解",
  description: "45 点均匀参数图、216 行无序分解、奇点和有限尺寸边界。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("Thakurathi et al., Phys. Rev. B 88, 155133 (2013), arXiv:1303.2300v2. Endpoint quantities and the negative-hopping adaptation are independently checked.")] },
    2: { children: [footnote("Source: results.json and uniform_grid.csv. Forty-five homogeneous parameter records; singular points and finite-size grid semantics are preserved.")] },
    3: { children: [footnote("Mondal et al., arXiv:2203.16353v3 Eq. (7); sensitivity.json and sensitivity.csv. Mechanical categories only, not topological creation or destruction.")] },
    4: { children: [footnote("Source: verify_kick_map.py and run.log. Independent reconstruction, singularity, transition, decomposition and basis-rotation checks. No disorder winding, material Tc or experimental validation.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · 均匀 kick 参数图", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
