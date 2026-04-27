/**
 * Build the Coastal Living Room Word doc — formal client deliverable.
 * Same shape as Home-Office-Spec.docx (cover, narrative, schedules,
 * lighting/power, modeling notes, embedded PNGs). US Letter, Arial,
 * brand colors, page numbers in footer.
 *
 * Run: node build_word_doc.js
 * Out: out/Living-Room-Spec.docx
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

const border = { style: BorderStyle.SINGLE, size: 4, color: "B0B0B0" };
const borders = { top: border, bottom: border, left: border, right: border };
const headerFill = { fill: "2C3E50", type: ShadingType.CLEAR };
const cellMargins = { top: 100, bottom: 100, left: 140, right: 140 };

function p(text, opts = {}) {
  return new Paragraph({
    children: [new TextRun({ text, ...opts })],
    spacing: { after: 80 },
    ...(opts.heading ? { heading: opts.heading } : {}),
    ...(opts.alignment ? { alignment: opts.alignment } : {}),
  });
}
function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, bold: true, color: "2C3E50" })],
  spacing: { before: 240, after: 120 } }); }
function h2(text) { return new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, bold: true, color: "2C3E50" })],
  spacing: { before: 200, after: 100 } }); }
function bullet(text) { return new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [new TextRun(text)],
  spacing: { after: 60 } }); }
function headerCell(text, width) {
  return new TableCell({ borders, width: { size: width, type: WidthType.DXA },
    shading: headerFill, margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 20 })] })] });
}
function dataCell(text, width, fill, opts = {}) {
  return new TableCell({ borders, width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text: String(text), size: 20, ...opts })] })] });
}
function buildTable(columns, rows) {
  const widths = columns.map(c => c.width);
  const total = widths.reduce((a, b) => a + b, 0);
  const tableRows = [new TableRow({
    children: columns.map(c => headerCell(c.header, c.width)), tableHeader: true })];
  rows.forEach((r, idx) => {
    const fill = idx % 2 === 0 ? null : "F5F2ED";
    tableRows.push(new TableRow({ children: r.map((cell, i) => dataCell(cell, widths[i], fill)) }));
  });
  return new Table({ width: { size: total, type: WidthType.DXA },
    columnWidths: widths, rows: tableRows });
}
function imagePage(imagePath, captionText, w = 624, hRatio = 1100/1600) {
  const data = fs.readFileSync(imagePath);
  const h = Math.round(w * hRatio);
  return [
    new Paragraph({
      children: [new ImageRun({ type: "png", data,
        transformation: { width: w, height: h },
        altText: { title: captionText, description: captionText, name: captionText } })],
      alignment: AlignmentType.CENTER, spacing: { before: 0, after: 120 } }),
    new Paragraph({
      children: [new TextRun({ text: captionText, italics: true, color: "555555", size: 20 })],
      alignment: AlignmentType.CENTER, spacing: { after: 120 } }),
  ];
}

// ---------- content ----------

const cover = [
  new Paragraph({ children: [new TextRun({ text: "CALLIE WELLS", bold: true, size: 56, color: "2C3E50" })],
    alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: "INTERIOR DESIGN", size: 28, color: "8C7853" })],
    alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({ text: "Coastal Living Room", bold: true, size: 44, color: "2C3E50" })],
    alignment: AlignmentType.CENTER, spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: "Project Specification · Sheet Set A-501", size: 24, color: "555555" })],
    alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({ text: "Client Location:  Rancho Santa Margarita, California", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Issue Date:  April 27, 2026", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Scale:  1/4\" = 1'-0\"  (1:48)", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Source File:  living-room.dwg  ·  AutoCAD 2027", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({
    text: "Real-estate staging-style presentation for a coastal-California living room — neutral envelope of white walls and coffered ceiling, warmed by walnut accents and an indigo wool rug. This document accompanies the dimensioned floor plan and 3D presentation render delivered in this package.",
    size: 18, italics: true, color: "777777" })],
    alignment: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
];

const narrative = [
  h1("1. Project Narrative"),
  p("A real-estate staging-style presentation for a coastal-California living room — the kind of room a buyer should walk into and immediately picture themselves on the sectional with a glass of wine. The space reads contemporary but warm: a neutral envelope of white walls and a coffered ceiling lets the wood floor, walnut accent furniture, and indigo rug do the heavy emotional lifting."),

  h2("Design Intent"),
  bullet("Lounge first, work second. The L-shape sectional anchors the south wall; two facing lounge chairs across the coffee table create a conversation triangle that doesn’t aim at a TV."),
  bullet("Reflect light, don’t block it. A 4'-0\" × 5'-0\" operable casement on the east wall is the room’s primary daylight source. Sheer linen drapery diffuses afternoon light without darkening the space; the 4'-0\" × 5'-0\" mirror over the console on the west wall bounces that light back across the room."),
  bullet("A coffered ceiling, lit gently. A 4×4 grid of 36\" × 42\" coffers hosts 16 recessed downlights — wash, not spotlights — at 2700K so the room reads warm at night."),
  bullet("Wide opening to a hallway on the north wall keeps the floor plan open to the rest of the house, signaling \"lounge for the whole family\" rather than a closed-off sitting room."),

  h1("2. Room Program"),
  buildTable(
    [{ header: "Element", width: 3120 }, { header: "Specification", width: 6240 }],
    [
      ["Room dimensions (interior)", "16'-0\" W × 18'-0\" L  (192\" × 216\")"],
      ["Floor area", "Approximately 288 SF"],
      ["Ceiling height", "10'-0\" AFF"],
      ["Coffered ceiling", "4×4 grid of 36\" × 42\" coffers, 6\" deep"],
      ["Hallway opening", "8'-0\" W × 8'-0\" tall on the north wall (no door)"],
      ["Window", "4'-0\" × 5'-0\" operable casement, east wall, sill at 30\" AFF"],
      ["Floor finish", "Engineered white-oak plank, semi-matte"],
      ["Wall finish", "Existing painted drywall, repaint warm white"],
      ["Trim & ceiling", "Crisp white, semi-gloss trim, flat ceiling"],
    ]
  ),
];

const ffe = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("3. FF&E Schedule"),
  p("Tag numbers correspond to the bubbles on the floor plan. All sizes are nominal width × depth × height in inches. Vendor names are placeholders / equivalents — final selections subject to client approval and current lead times."),
  buildTable(
    [
      { header: "Tag", width: 500 },
      { header: "Item", width: 1700 },
      { header: "Size", width: 1500 },
      { header: "Material / Finish", width: 2900 },
      { header: "Vendor (equiv.)", width: 2300 },
      { header: "Qty", width: 460 },
    ],
    [
      ["1",  "Sectional sofa (L)",       "120 × 84 × 30",      "Oatmeal performance linen, hardwood frame", "West Elm \"Harmony\"", "1"],
      ["2",  "Lounge chair, left",        "34 × 36 × 32",       "Lofted curved-shell, oatmeal linen, walnut leg", "Article \"Sven\"", "1"],
      ["3",  "Lounge chair, right",       "34 × 36 × 32",       "Same as #2, mirrored",                     "Article \"Sven\"", "1"],
      ["4",  "Coffee table",              "48 × 24 × 16",       "Walnut top, 1/2\" filleted edges, walnut legs", "Crate & Barrel \"Verge\"", "1"],
      ["5",  "Console table",             "60 × 18 × 30",       "Walnut top, brass tubular legs (Ø 1\")",      "West Elm \"Mid-Century\"", "1"],
      ["6",  "Wall mirror",               "48 × 60",            "Brass-frame mirror, 0.5\" frame reveal",     "CB2 \"Brushed Brass\"", "1"],
      ["7",  "Wall art (above sofa)",     "36 × 48",            "Custom giclée, coastal-blue palette",         "TBD by client", "1"],
      ["8",  "Drapery, left panel",       "24 × 84",            "Sheer white linen, swept profile",            "West Elm \"Linen Cotton\"", "1"],
      ["9",  "Drapery, right panel",      "24 × 84",            "Same as #8, mirrored",                      "West Elm \"Linen Cotton\"", "1"],
      ["10", "Area rug",                  "96 × 120 (8' × 10')", "Indigo wool/poly low-pile, ivory border",   "Loloi \"Layla\"", "1"],
      ["11", "Floor lamp",                "Ø 18 × 70 H",        "Revolved brass body, linen drum shade",       "Schoolhouse \"Isaac\"", "1"],
    ]
  ),
  p(""),
  p("Lead-time note: items 1, 2, 3, 5, and 11 typically ship 6–10 weeks. Order on contract signature to keep the critical path on schedule.", { italics: true, color: "555555" }),
];

const finish = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("4. Finish Schedule"),
  buildTable(
    [
      { header: "Surface", width: 1900 },
      { header: "Material", width: 2400 },
      { header: "Color / Finish", width: 2880 },
      { header: "Spec Note", width: 2180 },
    ],
    [
      ["Floor",                "Engineered white oak, 7\" plank", "Natural, semi-matte",                         "Site-finished, water-based poly"],
      ["Baseboard",            "Painted MDF, 5\" recessed-leg",   "Match trim (semi-gloss white)",               "Caulk + paint touch-up"],
      ["Walls",                "Existing drywall",                  "Benjamin Moore \"Simply White\" (OC-117), eggshell", "2 coats over primer"],
      ["Ceiling (field)",      "Existing drywall",                  "BM \"Decorator’s White\" (CC-20), flat",     "Match existing"],
      ["Coffer trim",          "Painted MDF",                       "Match trim (semi-gloss white)",               "Filleted inside corners"],
      ["Hallway opening trim", "Painted MDF",                       "Match trim (semi-gloss white)",               "No door; trim returns into hall"],
      ["Window casing & sill", "Painted MDF",                       "Match trim (semi-gloss white)",               "Sheer drape extends 6\" past trim"],
    ]
  ),
];

const lighting = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("5. Lighting Plan"),
  h2("Ambient (general)"),
  bullet("16 recessed LED downlights, one per ceiling coffer (4×4 grid). 4\" aperture, IC-rated, airtight, dimmable. 800 lm at 2700K, 90+ CRI."),
  bullet("Switch on a single dimmer with a master scene control at the hallway opening."),
  bullet("Sun via geographic location — drawing is sited at Rancho Santa Margarita (Lat 33.6404°N, Lon 117.6031°W). Preferred render time-of-day: April 10, 4:30 PM PDT."),

  h2("Task & accent"),
  bullet("Floor lamp (FF&E #11): 1200-lm point source inside the linen drum shade, 2700K, switched at the lamp socket. Provides reading light at the right lounge chair."),

  h2("Switching & control"),
  bullet("Single dimmer at hallway opening drives the 16 cans as a single zone."),
  bullet("Floor lamp switched independently."),
  bullet("Recommend smart switches (Lutron Caseta or equivalent) wired during the electrical refresh so the cans can drop to ~30% for evening ambiance."),

  h1("6. Power & Data"),
  bullet("Existing duplex outlets on south, east, and west walls — verify locations before purchasing the sectional and console."),
  bullet("Recommend adding one duplex outlet behind the console for a smart hub or future wall sconces."),
  bullet("No floor outlets called out; coordinate with electrician if a floor box behind the sectional becomes desirable."),

  h1("7. Door, Window & Opening Detail"),
  bullet("Hallway opening (north wall) — 8'-0\" wide × 8'-0\" tall, no door. Trim with the same profile as the rest of the room for visual continuity."),
  bullet("East window — 4'-0\" × 5'-0\" operable casement, sill at 30\" AFF. Glass is shown in the model with a thin pane for visual reference."),
  bullet("Drapery panels (FF&E #8 and #9) are modeled with a SWEEP along a wavy path to mimic linen draping; in production this would be replaced by an actual fabric simulation in the render pass."),
];

const modelingNotes = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("8. 3D Modeling Notes"),
  p("The .dwg uses commands from the curriculum brief:"),
  buildTable(
    [{ header: "Command", width: 2400 }, { header: "Use in this model", width: 6960 }],
    [
      ["BOX / CYLINDER",          "Walls, floor, ceiling slab, console legs, sofa frames, coffee-table base"],
      ["SUBTRACT",                "Window opening, hallway opening, 16 ceiling coffers, mirror frame inset"],
      ["LOFT (3 section curves)", "Both lounge chairs — base footprint → seat-top contour → back-only cap"],
      ["REVOLVE (lathe)",         "Floor lamp body — closed XZ silhouette revolved 360° about Z axis"],
      ["SWEEP",                   "Both drapery panels — thin rectangular profile along a wavy 3D path"],
      ["FILLETEDGE",              "Coffee-table top edges, 1/2\" radius"],
      ["CAMERA / -VIEW _S",        "Saved HERO and EDITORIAL named views for presentation"],
      ["doc.Materials.Add",       "12 custom materials defined and assigned by layer"],
      ["POINTLIGHT",              "16 recessed lights in coffers + 1 floor-lamp light"],
    ]
  ),
  p(""),
  p("Items reserved for a render pass / GUI follow-up: MATBROWSER library imports, SUNPROPERTIES palette confirmation, RENDER to file at Medium then High preset, ARCH-D layout with title block + IMAGEATTACH + 3 small viewports. The Conceptual visual style snapshot in presentation-iso.png substitutes as the visual deliverable for now.", { italics: true, color: "555555" }),

  h1("9. Scope Exclusions"),
  bullet("Structural changes (none anticipated)."),
  bullet("Permits — existing room only, no new circuits called for in this scope."),
  bullet("Furniture procurement (designer specs, client procures, or designer procures via separate purchase agreement)."),
  bullet("Built-ins (a future phase could swap the freestanding console for a full-wall built-in beneath the mirror)."),
  bullet("Electronics (TV mounting, audio system) — out of scope for this presentation room."),

  h1("10. Notes & Assumptions"),
  bullet("Existing electrical, HVAC, and structure assumed adequate without modification."),
  bullet("Vendor names are placeholders / equivalents; final selections to be confirmed against client budget and lead times."),
  bullet("All dimensions are nominal — confirm in field before placing orders."),
  bullet("Render in presentation-iso.png is AutoCAD’s Conceptual visual style, not a raytraced render. A photoreal pass with sun + artificial lights together can be produced on request."),
];

const drawings = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("11. Floor Plan — Sheet A-501"),
  p("Plan view at 1/4\" = 1'-0\". FF&E tags 1–11 keyed to the schedule on page 4. Hallway opening, window, and overall room dimensions called out; north arrow upper-right; designer stamp lower-left; recessed-can locations shown as crosshair markers in the coffered ceiling."),
  ...imagePage(path.join(OUT_DIR, "floor-plan.png"), "Sheet A-501 — Coastal Living Room Floor Plan & FF&E Tags"),

  new Paragraph({ children: [new PageBreak()] }),
  h1("12. 3D Presentation View"),
  p("Southwest isometric, AutoCAD Conceptual visual style. Ceiling layer frozen so the viewer can see into the room. Materials are shown as flat fills keyed to the finish schedule; a photoreal render can be produced on request."),
  ...imagePage(path.join(OUT_DIR, "presentation-iso.png"), "SW Isometric — Conceptual Render"),
];

// ---------- assemble ----------
const doc = new Document({
  creator: "Callie Wells, Interior Design",
  title: "Coastal Living Room — Project Specification",
  description: "Sheet set A-501 · Floor plan, FF&E and finish schedules, 3D presentation",
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
  numbering: { config: [{ reference: "bullets",
    levels: [{ level: 0, format: LevelFormat.BULLET, text: "•",
      alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] }] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } } },
    headers: { default: new Header({
      children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [
          new TextRun({ text: "Callie Wells · Interior Design   |   ", color: "777777", size: 18 }),
          new TextRun({ text: "Coastal Living Room · A-501", color: "777777", size: 18 }),
        ] })] }) },
    footers: { default: new Footer({
      children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", color: "777777", size: 18 }),
          new TextRun({ children: [PageNumber.CURRENT], color: "777777", size: 18 }),
          new TextRun({ text: " of ", color: "777777", size: 18 }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], color: "777777", size: 18 }),
          new TextRun({ text: "   ·   Issued 2026-04-27", color: "777777", size: 18 }),
        ] })] }) },
    children: [...cover, ...narrative, ...ffe, ...finish, ...lighting, ...modelingNotes, ...drawings],
  }],
});

const outPath = path.join(OUT_DIR, "Living-Room-Spec.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log(`wrote ${outPath} (${buf.length.toLocaleString()} bytes)`);
}).catch(err => { console.error(err); process.exit(1); });
