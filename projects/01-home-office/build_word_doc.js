/**
 * Build the Home Office Conversion Word doc — what a remote interior
 * designer would email to a client. Embeds the two PNG renders, the FF&E
 * and finish schedules as tables, and the project narrative.
 *
 * Run: node build_word_doc.js
 * Out: out/Home-Office-Spec.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell, ImageRun,
  Header, Footer, AlignmentType, LevelFormat, HeadingLevel, BorderStyle,
  WidthType, ShadingType, PageNumber, PageBreak,
} = require("docx");

const HERE = __dirname;
const OUT_DIR = path.join(HERE, "out");

// ---------- helpers ----------
const border = { style: BorderStyle.SINGLE, size: 4, color: "B0B0B0" };
const borders = { top: border, bottom: border, left: border, right: border };
const headerFill = { fill: "2C3E50", type: ShadingType.CLEAR };
const stripeFill = { fill: "F5F2ED", type: ShadingType.CLEAR };
const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 80 },
    ...(opts.heading ? { heading: opts.heading } : {}),
    ...(opts.alignment ? { alignment: opts.alignment } : {}),
  });
}

function h1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text, bold: true, color: "2C3E50" })],
    spacing: { before: 240, after: 120 },
  });
}

function h2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text, bold: true, color: "2C3E50" })],
    spacing: { before: 200, after: 100 },
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "bullets", level: 0 },
    children: [new TextRun(text)],
    spacing: { after: 60 },
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: headerFill,
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 20 })],
    })],
  });
}

function dataCell(text, width, fill, opts = {}) {
  return new TableCell({
    borders,
    width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({
      children: [new TextRun({ text: String(text), size: 20, ...opts })],
    })],
  });
}

function buildTable(columns, rows) {
  // columns: [{ header, width }]
  // rows: array of arrays, each row is array of cell texts (or {text, bold})
  const totalWidth = columns.reduce((s, c) => s + c.width, 0);
  const widths = columns.map(c => c.width);

  const tableRows = [];
  // header row
  tableRows.push(new TableRow({
    children: columns.map(c => headerCell(c.header, c.width)),
    tableHeader: true,
  }));
  // body rows w/ alternating stripes
  rows.forEach((r, idx) => {
    const fill = idx % 2 === 0 ? null : "F5F2ED";
    tableRows.push(new TableRow({
      children: r.map((cell, i) => {
        if (typeof cell === "object" && cell !== null) {
          return dataCell(cell.text, widths[i], fill, { bold: cell.bold });
        }
        return dataCell(cell, widths[i], fill);
      }),
    }));
  });

  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: tableRows,
  });
}

function imagePage(imagePath, captionText) {
  const data = fs.readFileSync(imagePath);
  // 6.5" content width at 96 DPI = 624 px. PNG is 1600x1100.
  const w = 624;
  const h = Math.round(w * (1100 / 1600)); // 429
  return [
    new Paragraph({
      children: [new ImageRun({
        type: "png",
        data,
        transformation: { width: w, height: h },
        altText: { title: captionText, description: captionText, name: captionText },
      })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 0, after: 120 },
    }),
    new Paragraph({
      children: [new TextRun({ text: captionText, italics: true, color: "555555", size: 20 })],
      alignment: AlignmentType.CENTER,
      spacing: { after: 120 },
    }),
  ];
}

// ---------- content ----------

const coverContent = [
  new Paragraph({
    children: [new TextRun({ text: "CALLIE WELLS", bold: true, size: 56, color: "2C3E50" })],
    alignment: AlignmentType.CENTER,
    spacing: { before: 2400, after: 80 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "INTERIOR DESIGN", size: 28, color: "8C7853" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Home Office Conversion", bold: true, size: 44, color: "2C3E50" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 80 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Project Specification · Sheet Set A-101", size: 24, color: "555555" })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Client Location:  Rancho Santa Margarita, California", size: 22 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Issue Date:  April 25, 2026", size: 22 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Scale:  1/2\" = 1'-0\"  (1:24)", size: 22 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 60 },
  }),
  new Paragraph({
    children: [new TextRun({ text: "Source File:  home-office.dwg  ·  AutoCAD 2027", size: 22 })],
    alignment: AlignmentType.CENTER,
    spacing: { after: 1200 },
  }),
  new Paragraph({
    children: [new TextRun({
      text: "This document accompanies the dimensioned floor plan and 3D presentation render delivered in this package. All vendor names listed are equivalents; final selections are subject to client approval and current lead times.",
      size: 18, italics: true, color: "777777",
    })],
    alignment: AlignmentType.CENTER,
  }),
  new Paragraph({ children: [new PageBreak()] }),
];

const narrativeContent = [
  h1("1. Project Narrative"),
  p("The client converted a 11'-6\" × 10'-0\" spare bedroom into a dedicated home office. The brief called for a focused work zone for video calls and writing, plus a separate reading nook for end-of-day decompression. Carpet was pulled and replaced with luxury vinyl plank so the chair rolls cleanly and the material is easy to vacuum on a daily basis."),

  h2("Design Intent"),
  bullet("Daylight as side light, not backlight. The desk faces into the room rather than toward the window so the operable casement on the east wall delivers diffuse side light to the writing surface and avoids glare on the monitor and on the client’s face during video calls."),
  bullet("Two zones, one room. Work zone occupies the west half of the room; the reading nook anchors the NE corner with an upholstered armchair, side table, and floor lamp grouped on a 6'×4' area rug to visually separate it from the work desk."),
  bullet("A neutral envelope, warm accents. Walls, ceiling and trim stay light and quiet so the wood-tone desk, walnut bookcase, and blue-gray armchair read as the personality of the room without competing with each other."),

  h1("2. Room Program"),
  buildTable(
    [
      { header: "Element", width: 3120 },
      { header: "Specification", width: 6240 },
    ],
    [
      ["Room dimensions (interior)", "11'-6\" W × 10'-0\" L  (138\" × 120\")"],
      ["Floor area", "Approximately 115 SF"],
      ["Ceiling height", "9'-0\" AFF"],
      ["Door", "2'-8\" × 6'-8\" single swing, hinged east, swings inward"],
      ["Window", "4'-0\" × 4'-0\" operable casement, east wall, sill at 36\" AFF"],
      ["Floor finish", "Luxury vinyl plank, warm walnut tone"],
      ["Wall finish", "Existing painted drywall; recommend repaint in warm white"],
      ["Ceiling finish", "Existing flat white"],
    ]
  ),
];

const ffeContent = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("3. FF&E Schedule"),
  p("Tag numbers correspond to the bubbles on the floor plan. All sizes are nominal width × depth × height in inches. Vendor names are placeholders / equivalents — final selections subject to client approval and current lead times."),
  buildTable(
    [
      { header: "Tag", width: 600 },
      { header: "Item", width: 1500 },
      { header: "Size W × D × H", width: 1700 },
      { header: "Material / Finish", width: 2700 },
      { header: "Vendor (equiv.)", width: 2400 },
      { header: "Qty", width: 460 },
    ],
    [
      ["1", "Writing desk",            "60 × 30 × 30",       "Solid white oak, walnut stain, satin lacquer", "West Elm “Mid-Century”",        "1"],
      ["2", "Task chair",               "Ø 20 × 18 swivel",  "Charcoal performance fabric, polished alum. base", "Herman Miller Sayl",                "1"],
      ["3", "Bookcase",                 "36 × 12 × 72",       "Walnut veneer, open-shelf, 5 shelves",         "Crate & Barrel “Aspect”",       "1"],
      ["4", "Armchair (reading)",       "34 × 34 × 32",       "Upholstered, blue-gray performance linen",     "Article “Sven”",                "1"],
      ["5", "Side table",               "Ø 18 × 22",         "Cream lacquer top, brass tubular base",         "CB2 “Mill”",                    "1"],
      ["6", "Floor lamp",               "Ø 12 base × 60 H",  "Matte dark-gray steel, linen drum shade, 3-way", "Schoolhouse “Isaac”",        "1"],
      ["7", "Area rug (under nook)",    "72 × 48 × 0.5",     "Wool/poly blend, low pile, indigo / cream",     "Loloi “Layla”",                "1"],
    ]
  ),
  p(""),
  p("Lead-time note: items 1, 3, and 4 typically ship 4–8 weeks. Order on contract signature to keep the critical path on schedule.", { italics: true, color: "555555" }),
];

const finishContent = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("4. Finish Schedule"),
  buildTable(
    [
      { header: "Surface", width: 1800 },
      { header: "Material", width: 2400 },
      { header: "Color / Finish", width: 2880 },
      { header: "Spec Note", width: 2280 },
    ],
    [
      ["Floor",            "LVP, 7\" plank",                 "Warm walnut, semi-matte",                                "8 mil wear layer min., underlayment incl."],
      ["Baseboard",        "Painted MDF, 4\" colonial",      "Match wall trim (semi-gloss white)",                     "Caulk + paint touch-up after install"],
      ["Walls",            "Existing drywall",                "Benjamin Moore “Swiss Coffee” (OC-45), eggshell", "2 coats over primer where patched"],
      ["Ceiling",          "Existing drywall",                "Benjamin Moore “Decorator’s White” (CC-20), flat", "Match existing"],
      ["Door & casing",    "Painted MDF",                     "Match trim (semi-gloss white)",                          "New hardware: matte black lever"],
      ["Window casing & sill", "Painted MDF",                 "Match trim (semi-gloss white)",                          "Roller shade in tan linen, top-mount"],
    ]
  ),
];

const notesContent = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("5. Lighting Plan (Notes)"),
  p("The rendered drawing set does not yet include a reflected-ceiling plan. For this room the recommendation is:"),
  bullet("1× recessed 6\" LED downlight, centered over desk; 3000K, 800 lm, dimmable."),
  bullet("1× recessed 6\" LED downlight, centered over reading nook; same spec."),
  bullet("Floor lamp (FF&E #6) provides task light at the armchair; switched at the socket."),
  bullet("Window provides primary daylight; recommend matching solar shade if the client experiences afternoon glare."),
  p("Switch the two recessed cans on a single dimmer at the door."),

  h1("6. Power & Data (Notes)"),
  bullet("Existing duplex outlets at the south and west walls — verify before move-in."),
  bullet("Recommend adding a quad outlet at the desk (west wall) for monitor, lamp, laptop, and phone charger."),
  bullet("Cat-6 drop at desk if Wi-Fi proves unreliable for video calls."),
  bullet("No outlet relocations called out on the floor plan; coordinate with electrician if added."),

  h1("7. Door & Window Detail"),
  bullet("Door is shown swung 90° inward in the 3D presentation as a diagrammatic shortcut; the 2D plan shows the opening only. For a final construction set, the door leaf would be drawn closed with a 2D swing arc on the plan view."),
  bullet("Window is a 48\" × 48\" operable casement, centered vertically on the east wall (sill at y=36\" interior, head at y=84\"). The 3D model shows glass with simple muntins, sill, apron, and a 24\"-drop tan roller shade."),

  h1("8. Scope Exclusions"),
  bullet("Structural / load-bearing changes (none needed)."),
  bullet("HVAC, plumbing, electrical permits (existing room only — no new circuits)."),
  bullet("Furniture procurement (designer specs the items; client procures or designer procures via a separate purchase agreement)."),
  bullet("Soft goods beyond the rug and roller shade."),
  bullet("Art and accessories (left to a future styling pass)."),

  h1("9. Notes & Assumptions"),
  bullet("Existing electrical, HVAC, and structure assumed adequate for a home office without modification."),
  bullet("Vendor names listed are placeholders / equivalents; final selections to be confirmed against client budget and lead times before issuing a PO."),
  bullet("All dimensions are approximate — confirm in field before placing orders."),
];

const drawingsContent = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("10. Floor Plan — Sheet A-101"),
  p("Plan view at 1/2\" = 1'-0\". FF&E tags 1–7 keyed to the schedule on page 3. Door, window, and overall room dimensions called out; north arrow upper-right; designer stamp lower-left."),
  ...imagePage(path.join(OUT_DIR, "floor-plan.png"), "Sheet A-101 — Home Office Floor Plan & FF&E Tags"),

  new Paragraph({ children: [new PageBreak()] }),
  h1("11. 3D Presentation View"),
  p("Southwest isometric, AutoCAD Conceptual visual style. Ceiling layer frozen so the viewer can see into the room. Materials are shown as flat colors keyed to the finish schedule — final renders with full materials and lighting can be produced on request."),
  ...imagePage(path.join(OUT_DIR, "presentation-iso.png"), "SW Isometric — Conceptual Render"),
];

// ---------- assemble document ----------
const doc = new Document({
  creator: "Callie Wells, Interior Design",
  title: "Home Office Conversion — Project Specification",
  description: "Sheet set A-101 · Floor plan, FF&E and finish schedules, 3D presentation",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: "2C3E50" },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 24, bold: true, font: "Arial", color: "2C3E50" },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [
        { level: 0, format: LevelFormat.BULLET, text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } },
      ]},
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 }, // US Letter
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    headers: {
      default: new Header({
        children: [new Paragraph({
          alignment: AlignmentType.RIGHT,
          children: [
            new TextRun({ text: "Callie Wells · Interior Design   |   ", color: "777777", size: 18 }),
            new TextRun({ text: "Home Office Conversion · A-101", color: "777777", size: 18 }),
          ],
        })],
      }),
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: "Page ", color: "777777", size: 18 }),
            new TextRun({ children: [PageNumber.CURRENT], color: "777777", size: 18 }),
            new TextRun({ text: " of ", color: "777777", size: 18 }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], color: "777777", size: 18 }),
            new TextRun({ text: "   ·   Issued 2026-04-25", color: "777777", size: 18 }),
          ],
        })],
      }),
    },
    children: [
      ...coverContent,
      ...narrativeContent,
      ...ffeContent,
      ...finishContent,
      ...notesContent,
      ...drawingsContent,
    ],
  }],
});

const outPath = path.join(OUT_DIR, "Home-Office-Spec.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log(`wrote ${outPath} (${buf.length.toLocaleString()} bytes)`);
}).catch(err => {
  console.error(err);
  process.exit(1);
});
