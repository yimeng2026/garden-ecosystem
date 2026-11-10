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
const sci = (value) => Number(value).toExponential(6).replace(/e([+-])(\d)$/, "e$10$2");
const titles = ["一、旧因子错误与 Fock 修复", "二、周期链联合拓扑诊断", "三、修正后的开放链证据", "四、勘误、验证与未竟边界"];
const n160 = data.size_studies.at(-1);
const resultRows = [];
for (const study of data.size_studies) {
  for (const [target, label] of [["zero", "0"], ["pi", "π"]]) {
    const row = study[target];
    resultRows.push([String(study.n), label, sci(Math.max(...row.distances)), sci(Math.max(...row.separation_ratios)), Math.min(...row.edge_weights).toFixed(6), data.convergence[target].finite_size_status]);
  }
}
const pairRows = [["zero", "0"], ["pi", "π"]].map(([target, label]) => {
  const [first, second] = n160[`${target}_nearest_pairs`];
  return [label, sci(first.max_distance), Math.min(...first.edge_weights).toFixed(6), sci(second.max_distance), Math.max(...second.edge_weights).toFixed(6)];
});
const children = [
  para(run("Floquet–BdG 约定修复与拓扑诊断", { bold: true, size: 36, color: palette.dark }), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, spacing: { before: 560, after: 220 } }),
  para(run("Fock 校验 · Bloch winding · 开放链最近四对谱", { bold: true, size: 27, color: palette.primary }), { alignment: AlignmentType.CENTER, spacing: { after: 240 } }),
  para(run("先修正模型，再判断 0／π 模；旧结果保留并勘误", { size: 21, color: palette.light }), { alignment: AlignmentType.CENTER, spacing: { after: 210 } }),
  para(run("2026-11-11　体拓扑与大尺寸候选一致；短链仍受局域限制", { size: 19, color: palette.accent }), { alignment: AlignmentType.CENTER, spacing: { after: 280 } }),
  heading("目录"),
  para(run("以下页码为可见缓存；在 Word/WPS 中更新域可刷新。", { size: 17, italics: true, color: palette.light })),
  toc(titles.map((title, index) => ({ title, level: 1, page: [2, 3, 4, 5][index] }))),
  pageBreak(),

  heading(titles[0]),
  citedBody("旧实现在 H=iΣKΓΓ 的完整反对称求和中漏除了 2，使目标参数的时间演化放大两倍。静态零空间和正交性测试对全局因子不敏感，旧 π 通过与 0 未决均暂停适用于目标参数。", 1),
  equation([new MathRun("K[a,b] = −"), new MathFraction({ numerator: [new MathRun("μ")], denominator: [new MathRun("2")] }), new MathRun(",　K[a_j,b_(j+1)] = "), new MathFraction({ numerator: [new MathRun("Δ−γ")], denominator: [new MathRun("4")] })]),
  makeTable(["独立检查", "旧实现实测", "Fock 参考／裁决"], [
    ["单格点 U[0,1]", "0.5702416578408517", "0.2987666363611303；不一致"],
    ["双格点最大矩阵元差", "0.81", "逐元素 Fock 对照不一致"],
    ["单格点 Heisenberg 最大差", "0.30223765311680495", "旧演化不一致"],
    ["修正后", "一／双格点 Fock 与演化合同", "4 项测试通过"],
  ], [2600, 3100, 3806], 13),
  body("修正后的直接矩阵元为 K[a_j,b_j]=−μ/2、K[a_j,b_(j+1)]=(Δ−γ)/4、K[a_(j+1),b_j]=−(Δ+γ)/4。独立 Fock 参考不调用旧矩阵生成答案，避免同一错误自证。"),
  makeTable(["旧资产处置", "当前规则"], [
    ["旧 results.json、图件和 Word", "保留原始字节，不删除、不静默改写"],
    ["旧 π 通过与 0 未决", "不继承；只作为错误实现的历史输出"],
    ["旧静态零空间与正交性", "代码性质可保留，但不证明目标物理参数"],
    ["新交付", "独立目录 floquet-bdg-convention，全部重算"],
  ], [3300, 6206], 13),
  pageBreak(),

  heading(titles[1]),
  citedBody("采用负 hopping 约定的 h(k)=2(−γcosk−μ0)τ_z+2Δsinkτ_y 和对称化 δ 脉冲。用 0<φ<π 的 SU(2) 表示提取 n_y、n_z，避免主对数分支切割；另以抽样 logm 复核方向。", 2),
  equation([new MathRun("W = "), new MathFraction({ numerator: [new MathRun("α_unwrap(π)−α_unwrap(−π)")], denominator: [new MathRun("2π")] })]),
  makeTable(["Nk", "winding", "最近整数", "min sinφ"], data.winding.rows.map((row) => [String(row.nk), row.winding.toFixed(12), String(row.nearest_integer), row.min_sin_phi.toFixed(9)]), [1400, 3000, 2100, 3006], 13),
  makeTable(["独立检查", "实际结果", "含义"], [
    ["端点计数", `b0=${data.endpoint_invariants.b0.toFixed(9)}；bπ=${data.endpoint_invariants.b_pi.toFixed(9)}`, "限定域内每端 p0=1、pπ=1"],
    ["静态平凡控制 ω=17", `W=${data.winding.controls.static_trivial_omega17.winding.toFixed(1)}`, "有能隙的平凡对照"],
    ["静态拓扑控制", `W=${data.winding.controls.static_topological_mu0.winding.toFixed(1)}`, "绝对值为 1 的拓扑对照"],
    ["logm 抽样方向", "三个动量点点积均为 1（数值误差内）", "分支无关方向与主对数一致"],
  ], [2400, 3600, 3506], 13),
  body("负 hopping 下 k=0 对应 bπ、k=π 对应 b0，已显式核对。winding 只给出 0／π 总数，端点量分别给出每端 0 与 π 模数；二者不能互相替代。"),
  pageBreak(),

  heading(titles[2]),
  citedBody("在 N=160，0 和 π 最近候选都满足分离比<0.1、端点权重>0.5。第二近候选对距离更远且端点权重低，不再误标为体模。", 3),
  makeTable(["N", "模", "最大距离", "最大分离比", "最小边缘权重", "全尺寸裁决"], resultRows, [520, 430, 1600, 1600, 1550, 3806], 11),
  makeTable(["模", "第一对最大距离", "第一对最小边缘权重", "第二对最大距离", "第二对最大边缘权重"], pairRows, [550, 2000, 2300, 2000, 2656], 11),
  body(`但 N=40 的 0 模最小端点权重为 ${Math.min(...data.size_studies[0].zero.edge_weights).toFixed(6)}，略低于 0.5；π 模为 ${Math.min(...data.size_studies[0].pi.edge_weights).toFixed(6)}。因此不调整旧阈值，全尺寸序列保持 inconclusive。`),
  para(new ImageRun({ type: "png", data: fs.readFileSync(path.join(root, "topology.png")), transformation: { width: 460, height: Math.round(460 * 1496 / 2180) } }), { alignment: AlignmentType.CENTER, keepNext: true }),
  para(run("图 1　修正后的 Bloch 轨迹、winding 收敛、候选距离和端点权重。", { size: 17, italics: true }), { alignment: AlignmentType.CENTER }),
  pageBreak(),

  heading(titles[3]),
  makeTable(["层次", "当前结论", "不能推出"], [
    ["旧报告", "因子错误已登记 ERRATA.md，旧文件保留", "旧 π／0 结论不能沿用到目标参数"],
    ["周期链", "W=2，p0=1、pπ=1，控制组一致", "不自动给出有限开放链候选分离"],
    ["N=160 开放链", "0／π 候选均有分离和端点局域证据", "不是热力学极限证明"],
    ["全尺寸旧判据", "inconclusive；N=40 局域阈值未全部满足", "不改阈值、不宣称全尺寸通过"],
  ], [2000, 4200, 3306], 13),
  citedBody("本研究只覆盖无相互作用、无耗散的二次型 Kitaev 链。没有自洽配对、材料 Tc、Meissner、非平衡占据、热管理或实验复现；连续驱动的 Fourier／时间步收敛仍需另行研究。", 4),
  makeTable(["验证层", "实际命令／结果"], [
    ["Fock 约定", "python research/floquet-bdg-convention/test_convention.py -v；4 项"],
    ["Bloch 拓扑", "python research/floquet-bdg-convention/test_topology.py -v；4 项"],
    ["独立复核", "python research/floquet-bdg-convention/verify_topology.py -v；7 项"],
    ["全流程", "python research/floquet-bdg-convention/run_verification.py；真实退出码见 run.log"],
  ], [2300, 7206], 13),
  body("原始数据见 results.json、candidates.csv、spectra.npz、bloch_curve.npz；旧资产影响范围和哈希见 research/floquet-bdg/ERRATA.md。下一未竟项是短链局域尺度与热力学极限之间的关系，而不是把本报告升级为材料超导结论。"),
];

const document = new Document({
  creator: "TOE-SYLVA",
  title: "Floquet–BdG 约定修复与联合拓扑诊断",
  description: "Fock 约定修复、Bloch winding、开放链最近四对谱与旧结果勘误。",
  features: { updateFields: true },
  styles: { paragraphStyles: [1, 2].map((level) => ({ id: `TOC${level}`, name: `TOC ${level}`, basedOn: "Normal", next: "Normal", quickFormat: true, run: { font, size: 19, color: palette.dark }, paragraph: { spacing: { after: 70, line: 240 }, indent: { left: (level - 1) * 360 } } })) },
  footnotes: {
    1: { children: [footnote("Source: research/floquet-bdg-convention/convention-red.log and research/floquet-bdg/ERRATA.md. Independent one-/two-site Fock comparison; legacy artifacts retained byte-for-byte.")] },
    2: { children: [footnote("Thakurathi et al., Phys. Rev. B 88, 155133 (2013), arXiv:1303.2300v2, Eqs. (17)–(27). Negative-hopping adaptation and branch-free direction checks are implemented independently in this package.")] },
    3: { children: [footnote("Source: results.json, candidates.csv, spectra.npz and bloch_curve.npz. Current corrected model, not legacy results. Full preregistered size-series status remains inconclusive because short-chain localization is below threshold.")] },
    4: { children: [footnote("Source: convention_model.py, bloch_topology.py, results.json scope and verify_topology.py. No interactions, dissipation, self-consistent pairing, material Tc prediction, thermodynamic-limit proof or experimental validation.")] },
  },
  sections: [{
    properties: { page: { margin: { top: 1000, bottom: 1000, left: 1000, right: 1000 } } },
    headers: { default: new Header({ children: [para(run("TOE-SYLVA · Floquet-BdG · Fock 修正与拓扑复核", { size: 17, color: palette.primary }), { alignment: AlignmentType.CENTER })] }) },
    footers: { default: new Footer({ children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 17 }), { alignment: AlignmentType.CENTER })] }) },
    children,
  }],
});
fs.writeFileSync(outputPath, await Packer.toBuffer(document));
