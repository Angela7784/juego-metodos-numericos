const {
  Document, Packer, Paragraph, TextRun, HeadingLevel,
  AlignmentType, PageBreak, TableOfContents, Header, Footer, PageNumber
} = require('docx');
const fs = require('fs');

// ── Parse problemas_salida.txt ──────────────────────────────────
const raw = fs.readFileSync('/Users/marcomendezsanchez/Downloads/metronumE-main/problemas_salida.txt', 'utf8');
const pattern = /===METODO:(.+?)===PROBLEMA:(\d+)===/g;
const data = {};
const metodosOrden = [];
let match;
const splits = raw.split(/===METODO:(.+?)===PROBLEMA:(\d+)===/);
// splits: [pre, metodo, num, text, metodo, num, text, ...]
for (let i = 1; i < splits.length - 2; i += 3) {
  const metodo = splits[i];
  const num = parseInt(splits[i+1]);
  const text = splits[i+2].trim();
  if (!data[metodo]) { data[metodo] = {}; metodosOrden.push(metodo); }
  data[metodo][num] = text;
}

// ── Build paragraphs ────────────────────────────────────────────
function textToParas(text) {
  return text.split('\n').map(line =>
    new Paragraph({
      children: [new TextRun({ text: line, font: 'Courier New', size: 18 })],
      spacing: { before: 0, after: 0, line: 240 },
    })
  );
}

const children = [];

// Cover page
children.push(
  new Paragraph({
    children: [new TextRun({ text: '', size: 24 })],
    spacing: { before: 2880, after: 0 },
  }),
  new Paragraph({
    children: [new TextRun({ text: 'Métodos Numéricos', bold: true, size: 56, font: 'Arial' })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 },
  }),
  new Paragraph({
    children: [new TextRun({ text: 'Problemas Resueltos', bold: true, size: 40, font: 'Arial', color: '2E75B6' })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 480 },
  }),
  new Paragraph({
    children: [new TextRun({ text: '25 métodos — 3 problemas por método', size: 28, font: 'Arial', italics: true, color: '595959' })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 2880 },
  }),
  new Paragraph({
    children: [new TextRun({ text: 'Mayo 2026', size: 24, font: 'Arial', color: '595959' })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0 },
  }),
  new Paragraph({ children: [new PageBreak()] }),
);

// Table of Contents
children.push(
  new TableOfContents('Tabla de Contenidos', { hyperlink: true, headingStyleRange: '1-2' }),
  new Paragraph({ children: [new PageBreak()] }),
);

// Content: one section per method
for (const metodo of metodosOrden) {
  // Heading 1 – method name
  children.push(
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun({ text: metodo, font: 'Arial', size: 32, bold: true })],
      spacing: { before: 360, after: 240 },
    })
  );

  for (let n = 1; n <= 3; n++) {
    // Heading 2 – Problema N
    children.push(
      new Paragraph({
        heading: HeadingLevel.HEADING_2,
        children: [new TextRun({ text: `Problema ${n}`, font: 'Arial', size: 26, bold: true })],
        spacing: { before: 240, after: 120 },
      })
    );
    // Monospace content
    const text = data[metodo][n] || '(sin datos)';
    children.push(...textToParas(text));
    children.push(new Paragraph({ children: [new TextRun({ text: '' })], spacing: { before: 120 } }));
  }

  // Page break between methods
  children.push(new Paragraph({ children: [new PageBreak()] }));
}

// ── Build Document ──────────────────────────────────────────────
const doc = new Document({
  styles: {
    default: { document: { run: { font: 'Arial', size: 24 } } },
    paragraphStyles: [
      {
        id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 32, bold: true, font: 'Arial', color: '1F3864' },
        paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0,
          border: { bottom: { style: 'single', size: 6, color: '2E75B6', space: 1 } } }
      },
      {
        id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 26, bold: true, font: 'Arial', color: '2E75B6' },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 }
      },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
      }
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Página ', font: 'Arial', size: 18, color: '595959' }),
            new TextRun({ children: [PageNumber.CURRENT], font: 'Arial', size: 18, color: '595959' }),
            new TextRun({ text: ' de ', font: 'Arial', size: 18, color: '595959' }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: 'Arial', size: 18, color: '595959' }),
          ]
        })]
      })
    },
    children,
  }]
});

Packer.toBuffer(doc).then(buf => {
  const out = '/Users/marcomendezsanchez/Downloads/metronumE-main/Problemas_Metodos_Numericos.docx';
  fs.writeFileSync(out, buf);
  console.log('Creado:', out);
});
