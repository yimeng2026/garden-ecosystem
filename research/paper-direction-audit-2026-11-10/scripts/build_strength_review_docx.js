import fs from "node:fs";
import path from "node:path";
import {
  AlignmentType,
  BorderStyle,
  Document,
  ExternalHyperlink,
  Footer,
  Header,
  HeadingLevel,
  ImageRun,
  ImportedXmlComponent,
  LevelFormat,
  Math as MathEquation,
  MathFraction,
  MathRun,
  MathSubScript,
  MathSuperScript,
  Packer,
  PageBreak,
  PageNumber,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} from "docx";

const outputPath = process.argv[2];
if (!outputPath) throw new Error("Usage: node build_strength_review_docx.js /absolute/path/candidate.docx");

const audit = path.dirname(outputPath);
const markdownPath = path.join(audit, "STRENGTH_SERIES_REVIEW.md");
const figurePath = path.join(audit, "strength-review-status.png");
const work = path.join(audit, "strength-word-sync-work");
fs.mkdirSync(work, { recursive: true });
fs.copyFileSync(path.join(audit, "STRENGTH_SERIES_REVIEW.docx"), path.join(work, "baseline.docx"));

const lines = fs.readFileSync(markdownPath, "utf8").split(/\r?\n/);
const font = {
  ascii: "Times New Roman",
  hAnsi: "Times New Roman",
  cs: "Times New Roman",
  eastAsia: "SimSun",
};
const codeFont = { ascii: "Consolas", hAnsi: "Consolas", cs: "Consolas", eastAsia: "Microsoft YaHei" };
const palette = { dark: "263238", primary: "455A64", light: "78909C", border: "D8E0E3", fill: "EEF3F6" };
const tableWidths = [420, 1350, 1250, 1700, 3506, 800];
const tableWidth = tableWidths.reduce((total, value) => total + value, 0);

const run = (text, options = {}) => new TextRun({ text, font, size: 21, ...options });
const para = (children, options = {}) => new Paragraph({
  spacing: { after: 120, line: 280 },
  ...options,
  children: Array.isArray(children) ? children : [children],
});

const mathText = (value) => String(value)
  .replace(/\\mathbb\{R\}/g, "ℝ")
  .replace(/\\mathrm\{([^{}]*)\}/g, "$1")
  .replace(/\\text\{([^{}]*)\}/g, "$1")
  .replace(/\\(?:Longrightarrow|Rightarrow)/g, "⇒")
  .replace(/\\(?:quad|qquad)/g, "  ")
  .replace(/\\(?:mu|psi|alpha|beta|lambda|rho|in|times|pm|infty|to|le|ge|neq|sqrt)/g, (command) => ({
    "\\mu": "μ", "\\psi": "ψ", "\\alpha": "α", "\\beta": "β", "\\lambda": "λ",
    "\\rho": "ρ", "\\in": "∈", "\\times": "×", "\\pm": "±", "\\infty": "∞",
    "\\to": "→", "\\le": "≤", "\\ge": "≥", "\\neq": "≠", "\\sqrt": "√",
  })[command])
  .replace(/\\([A-Za-z]+)/g, "$1")
  .replace(/[{}$]/g, "");

const normalizeLink = (target) => {
  if (/^[A-Za-z]:[\\/]/.test(target)) return `file:///${target.replace(/\\/g, "/")}`;
  return target;
};

const inline = (text, size = 21) => {
  const tokens = String(text).split(/(\[[^\]]+\]\([^)]+\)|\*\*[^*]+\*\*|`[^`]+`|\$[^$]+\$)/g);
  return tokens.filter((token) => token.length > 0).map((token) => {
    const link = token.match(/^\[([^\]]+)\]\((.+)\)$/);
    if (link) {
      return new ExternalHyperlink({
        link: normalizeLink(link[2]),
        children: [run(link[1], { size, style: "Hyperlink", color: "0563C1" })],
      });
    }
    if (token.startsWith("**") && token.endsWith("**")) return run(token.slice(2, -2), { size, bold: true });
    if (token.startsWith("`") && token.endsWith("`")) return new TextRun({ text: token.slice(1, -1), font: codeFont, size });
    if (token.startsWith("$") && token.endsWith("$")) return run(mathText(token), { size });
    return run(mathText(token), { size });
  });
};

const heading = (text, level) => {
  const properties = {
    1: { heading: HeadingLevel.HEADING_1, size: 30 },
    2: { heading: HeadingLevel.HEADING_2, size: 26 },
    3: { heading: HeadingLevel.HEADING_3, size: 23 },
  }[level];
  return para(inline(text, properties.size), {
    heading: properties.heading,
    spacing: { before: 260, after: 140 },
  });
};

const psiToyPrime = () => new MathSuperScript({
  children: [new MathSubScript({ children: [new MathRun("ψ")], subScript: [new MathRun("toy")] })],
  superScript: [new MathRun("′′")],
});
const nativeFormula = () => para(new MathEquation({ children: [
  psiToyPrime(),
  new MathRun("(μ) = 1   ⇒   "),
  new MathFraction({
    numerator: [new MathRun("1")],
    denominator: [psiToyPrime(), new MathRun("(μ)")],
  }),
  new MathRun(" = 1,   μ ∈ ℝ"),
] }), { alignment: AlignmentType.CENTER, spacing: { before: 120, after: 180 } });

const xmlEscape = (value) => String(value)
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;");
const tocEntries = lines.filter((line) => /^#{2,3} /.test(line)).map((line) => {
  const level = line.startsWith("###") ? 2 : 1;
  return { title: line.replace(/^#{2,3} /, ""), level };
});
const toc = (entries) => {
  const cached = entries.map(({ title, level }) => `<w:p><w:pPr><w:pStyle w:val="TOC${level}"/>
    <w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9000"/></w:tabs></w:pPr>
    <w:r><w:t>${xmlEscape(title)}</w:t></w:r></w:p>`).join("");
  return ImportedXmlComponent.fromXmlString(`<w:sdt xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
    <w:sdtPr><w:alias w:val="目录"/></w:sdtPr><w:sdtContent>
      <w:p><w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/>
        <w:instrText xml:space="preserve"> TOC \\o &quot;1-2&quot; \\h \\z \\u </w:instrText>
        <w:fldChar w:fldCharType="separate"/></w:r></w:p>
      ${cached}<w:p><w:r><w:fldChar w:fldCharType="end"/></w:r></w:p>
    </w:sdtContent></w:sdt>`).root[0];
};

const cell = (text, index, widths, header = false) => new TableCell({
  children: [para(inline(text, 14), { spacing: { after: 0, line: 220 } })],
  width: { size: widths[index], type: WidthType.DXA },
  margins: { top: 60, bottom: 60, left: 60, right: 60 },
  shading: header ? { type: ShadingType.CLEAR, fill: palette.fill } : undefined,
});
const parseCells = (line) => line.trim().replace(/^\|/, "").replace(/\|$/, "").split("|").map((value) => value.trim());
const renderTable = (block) => {
  const rows = block.filter((_, index) => index !== 1).map(parseCells);
  const columns = rows[0].length;
  const widths = columns === 6
    ? tableWidths
    : Array.from({ length: columns }, (_, index) => index === columns - 1
      ? tableWidth - Math.floor(tableWidth / columns) * (columns - 1)
      : Math.floor(tableWidth / columns));
  return new Table({
    width: { size: tableWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: rows.map((cells, rowIndex) => new TableRow({
      tableHeader: rowIndex === 0,
      children: cells.map((text, index) => cell(text, index, widths, rowIndex === 0)),
    })),
  });
};

const imageParagraph = (target) => {
  const data = fs.readFileSync(path.join(audit, target));
  const naturalWidth = data.readUInt32BE(16);
  const naturalHeight = data.readUInt32BE(20);
  const width = 600;
  return para(new ImageRun({
    type: "png",
    data,
    transformation: { width, height: Math.round(width * naturalHeight / naturalWidth) },
  }), { alignment: AlignmentType.CENTER, keepNext: true });
};

const children = [
  para(run("数学基础与模块强化：55 篇逐篇方向及未竟工作初审", { bold: true, size: 36, color: palette.dark }), {
    heading: HeadingLevel.TITLE,
    alignment: AlignmentType.CENTER,
    spacing: { before: 300, after: 240 },
  }),
  para(run("证据边界、K1a/K1b 与 K2 补记同步", { size: 24, color: palette.primary }), {
    alignment: AlignmentType.CENTER,
    spacing: { after: 260 },
  }),
  heading("目录", 1),
  toc(tocEntries),
  new Paragraph({ children: [new PageBreak()] }),
];

for (let index = 1; index < lines.length; index += 1) {
  const line = lines[index];
  const trimmed = line.trim();
  if (!trimmed) continue;
  if (trimmed === "---") {
    children.push(para("", { border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: palette.border, space: 1 } } }));
    continue;
  }
  if (trimmed.startsWith("$$") && trimmed.endsWith("$$")) {
    children.push(nativeFormula());
    continue;
  }
  if (trimmed.startsWith("|")) {
    const block = [];
    let cursor = index;
    while (cursor < lines.length && lines[cursor].trim().startsWith("|")) {
      block.push(lines[cursor]);
      cursor += 1;
    }
    children.push(renderTable(block));
    index = cursor - 1;
    continue;
  }
  const image = trimmed.match(/^!\[[^\]]*\]\(([^)]+)\)$/);
  if (image) {
    children.push(imageParagraph(image[1]));
    continue;
  }
  const headingMatch = trimmed.match(/^(#{1,4}) (.+)$/);
  if (headingMatch) {
    children.push(heading(headingMatch[2], headingMatch[1].length));
    continue;
  }
  if (trimmed.startsWith(">")) {
    children.push(para(inline(trimmed.replace(/^>\s?/, "")), {
      indent: { left: 360 },
      shading: { type: ShadingType.CLEAR, fill: "F4F7F8" },
    }));
    continue;
  }
  const numbered = trimmed.match(/^\d+\.\s+(.+)$/);
  if (numbered) {
    children.push(para(inline(numbered[1]), { numbering: { reference: "ordered", level: 0 } }));
    continue;
  }
  const bullet = trimmed.match(/^-\s+(.+)$/);
  if (bullet) {
    children.push(para(inline(bullet[1]), { numbering: { reference: "bullets", level: 0 } }));
    continue;
  }
  children.push(para(inline(trimmed), { indent: { firstLine: 360 } }));
}

const document = new Document({
  creator: "TOE-SYLVA",
  title: "数学基础与模块强化：55 篇逐篇方向及未竟工作初审",
  description: "55 篇初审与全部 K1a/K1b/K2 补记；不是全库终审或外部查新。",
  features: { updateFields: true },
  styles: {
    paragraphStyles: [1, 2].map((level) => ({
      id: `TOC${level}`,
      name: `TOC ${level}`,
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { font, size: 20, color: palette.dark },
      paragraph: { spacing: { after: 80, line: 250 }, indent: { left: (level - 1) * 360 } },
    })),
  },
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }],
      },
      {
        reference: "ordered",
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 480, hanging: 240 } } } }],
      },
    ],
  },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
    headers: {
      default: new Header({
        children: [para(run("TOE-SYLVA · 55篇逐篇初审 · 证据边界与补记", { size: 18, color: palette.primary }), {
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [para(new TextRun({ children: [PageNumber.CURRENT], font, size: 18 }), {
          alignment: AlignmentType.CENTER,
        })],
      }),
    },
    children,
  }],
});

fs.writeFileSync(outputPath, await Packer.toBuffer(document));
