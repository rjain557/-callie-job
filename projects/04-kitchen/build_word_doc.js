/**
 * Build the Kitchen Casework Word doc — formal client deliverable.
 * Same shape as Living-Room-Spec.docx (cover, narrative, schedules,
 * lighting/power, modeling notes, embedded PNGs).
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
    ...(opts.alignment ? { alignment: opts.alignment } : {}),
  });
}
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text: t, bold: true, color: "2C3E50" })],
  spacing: { before: 240, after: 120 } });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text: t, bold: true, color: "2C3E50" })],
  spacing: { before: 200, after: 100 } });
const bullet = (t) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  children: [new TextRun(t)],
  spacing: { after: 60 } });

function headerCell(text, width) {
  return new TableCell({ borders, width: { size: width, type: WidthType.DXA },
    shading: headerFill, margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, bold: true, color: "FFFFFF", size: 20 })] })] });
}
function dataCell(text, width, fill) {
  return new TableCell({ borders, width: { size: width, type: WidthType.DXA },
    shading: fill ? { fill, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text: String(text), size: 20 })] })] });
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

const cover = [
  new Paragraph({ children: [new TextRun({ text: "CALLIE WELLS", bold: true, size: 56, color: "2C3E50" })],
    alignment: AlignmentType.CENTER, spacing: { before: 2400, after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: "INTERIOR DESIGN", size: 28, color: "8C7853" })],
    alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({ text: "Kitchen Casework", bold: true, size: 44, color: "2C3E50" })],
    alignment: AlignmentType.CENTER, spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: "Single-Wall Layout with Island · Sheet Set A-201", size: 24, color: "555555" })],
    alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({ text: "Client Location:  Rancho Santa Margarita, California", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Issue Date:  April 27, 2026", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Scale:  1/2\" = 1'-0\"  (1:24)", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 60 } }),
  new Paragraph({ children: [new TextRun({ text: "Source File:  kitchen.dwg  ·  AutoCAD 2027", size: 22 })],
    alignment: AlignmentType.CENTER, spacing: { after: 1200 } }),
  new Paragraph({ children: [new TextRun({
    text: "Single-wall cabinet run with a freestanding island, totaling 14'-0\" of base + wall casework. Painted Shaker doors over a quartz counter, with a stainless hood, panel-ready dishwasher, and full-height pantry. Issued for client review and budget alignment.",
    size: 18, italics: true, color: "777777" })],
    alignment: AlignmentType.CENTER }),
  new Paragraph({ children: [new PageBreak()] }),
];

const narrative = [
  h1("1. Project Narrative"),
  p("A clean single-wall kitchen for a coastal-California home — long-wall casework for everyday cooking, anchored by a freestanding island that doubles as the breakfast bar and the prep zone. Painted Shaker doors in a warm white over a quartz counter keep the room bright; a tall pantry on the east end disguises the dry-goods storage so the line of upper cabinets reads continuous from the dining room (visible through the west-wall opening)."),
  h2("Design Intent"),
  bullet("One wall, full work triangle. Range, sink, and the dishwasher slot all live along the south wall in a 14'-0\" run. Total prep travel is under 6'-0\" between work zones."),
  bullet("Island as second counter. The island carries the seating overhang (12\" on the north side) and provides 96\" of clear counter for prep — enough for a sheet pan and two cutting boards laid out at once."),
  bullet("Pantry over wall cabinets. The east-end pantry runs full 84\" so it reads as architecture, not as cabinetry. Wall cabinets stop short of it for visual rhythm."),
  bullet("Hood over the range. No wall cabinet over the cooktop — a 30\" ducted hood vented up through the soffit. Code-compliant, and visually it gives the cooktop \"breathing room.\""),

  h1("2. Room Program"),
  buildTable(
    [{ header: "Element", width: 3120 }, { header: "Specification", width: 6240 }],
    [
      ["Room dimensions (interior)", "14'-0\" W × 10'-0\" L  (168\" × 120\")"],
      ["Floor area", "Approximately 140 SF"],
      ["Ceiling height", "10'-0\" AFF"],
      ["Wall openings", "6'-0\" wide × 8'-0\" tall opening on west wall to dining room"],
      ["Floor finish", "Engineered white-oak plank, semi-matte"],
      ["Wall finish", "Painted drywall, semi-gloss white at backsplash zone"],
      ["Ceiling", "Painted drywall, flat white"],
    ]
  ),
];

const ffe = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("3. FF&E + Casework Schedule"),
  p("Tag numbers correspond to the bubbles on the floor plan. All sizes are nominal width × depth × height in inches."),
  buildTable(
    [
      { header: "Tag", width: 500 },
      { header: "Item", width: 1900 },
      { header: "Size", width: 1500 },
      { header: "Material / Finish", width: 2700 },
      { header: "Notes", width: 2300 },
      { header: "Qty", width: 460 },
    ],
    [
      ["1",  "Base cabinet B36",      "36 × 24 × 34.5", "Painted Shaker, soft-close",        "Toe kick 4×3",                "1"],
      ["2",  "Slide-in range R30",    "30 × 27 × 36",   "Stainless / black, 5-burner gas",   "Anti-tip required",            "1"],
      ["3",  "Dishwasher DW24",       "24 × 24 × 34.5", "Stainless, panel-ready front",       "Hidden in plan",               "1"],
      ["4",  "Sink base SB36",        "36 × 24 × 34.5", "Painted Shaker, false drawer",       "Pull-out trash optional",       "1"],
      ["5",  "Base cabinet B30",      "30 × 24 × 34.5", "Painted Shaker, drawer stack",       "3 drawers",                     "1"],
      ["6",  "Pantry P12 (full ht)",  "12 × 24 × 84",   "Painted Shaker, 5 fixed shelves",     "Slim — canned goods",            "1"],
      ["7",  "Range hood",            "30 × 18 × 30",   "Stainless, ducted, 600 CFM",         "Vents up through soffit",       "1"],
      ["8",  "Island",                "96 × 42 × 34.5", "Painted Shaker + quartz",           "12\" overhang seating side",       "1"],
      ["9",  "Sink basin",            "25 × 19 × 9",    "Stainless under-mount, 18 ga",       "Single-bowl",                    "1"],
      ["10", "Counter, long-wall",     "156 × 25.5 × 1.5","Quartz, eased edge",                 "Single seamed slab",            "1"],
      ["11", "Faucet",                 "Ø 1.2 × 13 H",  "Brushed nickel, single-handle",       "Pull-down spray",                "1"],
      ["—",  "Wall cabinets",         "12 deep × 42 tall", "Painted Shaker, frameless",      "Bottoms at 54\" AFF",            "4"],
    ]
  ),
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
      ["Floor",            "Engineered white oak, 7\" plank",  "Natural, semi-matte",                          "Continue from living room"],
      ["Cabinet doors",    "Painted MDF, Shaker style",        "BM \"Simply White\" (OC-117), satin",          "Soft-close hinges + slides"],
      ["Cabinet boxes",    "Plywood, painted to match doors",   "Same as doors",                                "Edge-banded"],
      ["Counter",          "Quartz, 1.5\" eased edge",          "\"Calacatta Lyon\" (light gray vein)",         "Single 8' island slab; long-wall seamed"],
      ["Backsplash",       "Field tile (TBD)",                  "Recommend 3×12 white matte subway",           "Field above counter under wall cabs"],
      ["Toe kick",         "Painted MDF",                       "Match cabinets",                               "4×3 recessed"],
      ["Hood",             "Stainless steel, brushed",          "Manufacturer finish",                          "600 CFM minimum"],
      ["Sink",             "Stainless, 18 ga, brushed",         "Under-mount",                                  "Single-bowl 25×19"],
      ["Faucet",           "Brushed nickel",                    "Single-handle pull-down",                       "360° swivel, 18\" reach"],
      ["Range",            "Stainless / black",                 "Manufacturer finish",                           "30\" 5-burner gas"],
      ["Dishwasher",       "Stainless, panel-ready",            "Match cabinet doors",                            "Hidden front"],
    ]
  ),
];

const services = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("5. Lighting Recommendations"),
  bullet("4× recessed 4\" LED downlights in a staggered grid over the island and prep run (3000K, 800 lm, dimmable)."),
  bullet("Under-cabinet LED strip below all wall cabinets (2700K), switched at the island."),
  bullet("Pendant-light cluster (3 pendants) over the island, hung at 36\" above the counter."),
  bullet("All zones on Lutron Caseta dimmers, scene control by the dining-room doorway."),

  h1("6. Power & Data"),
  bullet("Code-required GFCI outlets every 4'-0\" along the counter run."),
  bullet("Dedicated 240V circuit for the range."),
  bullet("120V outlet under the sink for the dishwasher."),
  bullet("Recommend a duplex outlet on the island (pop-up or end-cap) for countertop appliances."),

  h1("7. Plumbing & Venting"),
  bullet("Sink rough-in centered at x = 7'-0\" from the west wall (under SB36)."),
  bullet("Dishwasher supply + drain shared with sink supply lines."),
  bullet("Range vent: 6\" round duct rises through the soffit above the hood and exits through the roof or sidewall."),
];

const modeling = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("8. 3D Modeling Notes"),
  p("The .dwg uses Project 4 curriculum commands:"),
  buildTable(
    [{ header: "Command", width: 2400 }, { header: "Use in this model", width: 6960 }],
    [
      ["BOX",                   "All cabinet boxes, counter, hood, range, dishwasher, sink basin, pantry"],
      ["CYLINDER",              "Cooktop grates, faucet body and spout"],
      ["SUBTRACT",              "Hallway opening, sink cutout, toe-kick voids (PRESSPULL substitute)"],
      ["TOP / NEISO / FRONT / BACK", "Plan view, presentation iso, two elevations"],
      ["2DWireframe / Conceptual",   "Switching visual style per snapshot"],
    ]
  ),
  p(""),
  p("Items reserved for a future GUI pass: named UCS for elevation drafting, PRESSPULL on toe kicks (replaced by SUBTRACT here), FILLETEDGE 0.25\" on counter edges, FLATSHOT projection from the 3D model onto a 2D elevation, and the ARCH-D layout sheet with title block + 4 viewports. The Word doc substitutes for the plotted board.", { italics: true, color: "555555" }),
  p(""),
  p("Run-length adjustment: brief calls a long-wall run summing to 192\" but the wall is 168\". This package reduces to B36 + R30 + DW24 + SB36 + B30 + P12 = 168\" by reassigning one base slot to the dishwasher and reducing pantry from 24\" to 12\". Documented in SPEC §8.", { italics: true, color: "555555" }),

  h1("9. Scope Exclusions"),
  bullet("HVAC and venting design (architect/engineer scope)."),
  bullet("Permits (range circuit, plumbing rough-in)."),
  bullet("Backsplash tile selection (recommendation only)."),
  bullet("Refrigerator and freezer — verify location with architect."),
  bullet("Pendant fixtures over the island (lighting designer scope)."),

  h1("10. Notes & Assumptions"),
  bullet("Existing electrical, gas, plumbing, and structure assumed adequate."),
  bullet("Vendor names where listed are equivalents; final selections subject to client budget and lead times."),
  bullet("All dimensions are nominal — confirm in field before fabricating cabinet boxes."),
  bullet("This package is for client review; final fabrication drawings will be issued by the cabinet shop."),
];

const drawings = [
  new Paragraph({ children: [new PageBreak()] }),
  h1("11. Floor Plan — Sheet A-201"),
  p("Plan view at 1/2\" = 1'-0\". FF&E + casework tags 1–11 keyed to schedule on page 4. Cabinet-run chain dims along the south wall; island callouts; hallway opening on west wall."),
  ...imagePage(path.join(OUT_DIR, "floor-plan.png"), "Sheet A-201 — Kitchen Plan"),

  new Paragraph({ children: [new PageBreak()] }),
  h1("12. Photoreal Render — Cycles"),
  p("Raytraced render produced by Blender 4.5 LTS / Cycles, 256 samples at 1920×1200. The .dwg model was exported per layer to STL, imported to Blender, mapped to PBR materials (procedural wood grain on the floor and walnut elements, marble veining on the quartz counter, brushed-metal noise on stainless and brushed-nickel hardware), lit with a soft sun + 16 ceiling cans + 3 pendant lights over the island."),
  ...imagePage(path.join(OUT_DIR, "render-photoreal.png"), "Photoreal Render — Cycles raytrace"),

  new Paragraph({ children: [new PageBreak()] }),
  h1("13. 3D Presentation View — Northwest (AutoCAD)"),
  p("Northwest isometric, AutoCAD Realistic visual style — the same model rendered inside AutoCAD as a real-time preview. Detail pass included: cabinet door reveals + pulls, drawer dividers, range knobs, faucet swing arm, full-height tile backsplash, crown molding on wall cabinets, three pendant cluster over the island, three counter-height bar stools at the seating side."),
  ...imagePage(path.join(OUT_DIR, "presentation-iso.png"), "NW Isometric — AutoCAD Realistic style"),

  new Paragraph({ children: [new PageBreak()] }),
  h1("14. Long-Wall Elevation"),
  p("Front view of the south-wall cabinet run. Wall cabinets at 54\"-96\" AFF, base cabinets at 0\"-36\" AFF, range hood centered above the cooktop gap, sink + faucet at SB36, full-height pantry on the east end."),
  ...imagePage(path.join(OUT_DIR, "elevation-long-wall.png"), "Elevation — Long Wall (south)"),

  new Paragraph({ children: [new PageBreak()] }),
  h1("15. Island Elevation"),
  p("Back view of the island. Cabinet body with toe kick on the storage side; counter line above with the 12\" seating overhang visible at the top."),
  ...imagePage(path.join(OUT_DIR, "elevation-island.png"), "Elevation — Island (back / seating)"),
];

const doc = new Document({
  creator: "Callie Wells, Interior Design",
  title: "Kitchen Casework — Project Specification",
  description: "Sheet set A-201 · Plan, elevations, 3D presentation",
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
          new TextRun({ text: "Kitchen Casework · A-201", color: "777777", size: 18 }),
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
    children: [...cover, ...narrative, ...ffe, ...finish, ...services, ...modeling, ...drawings],
  }],
});

const outPath = path.join(OUT_DIR, "Kitchen-Spec.docx");
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log(`wrote ${outPath} (${buf.length.toLocaleString()} bytes)`);
}).catch(err => { console.error(err); process.exit(1); });
