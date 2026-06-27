# FORM GSTR-2B - Exact Recreation Markdown Specification

Use this file as the master prompt/specification for recreating the uploaded **FORM GSTR-2B** document in the same statutory format. The uploaded source is a 6-page image-based/scanned PDF, so the rendered page images are the authoritative reference for layout, line breaks, table continuation, and clipped text.

> **Important:** Native Markdown tables cannot reproduce this form accurately because the source document uses merged cells, rowspans, narrow tax columns, page-continuation tables, heavy border grids, clipped table continuations, and vertically compressed statutory text. Recreate the document using **HTML/CSS inside Markdown**, then convert the HTML to PDF/DOCX if needed.

---

## 1. Output Rules

### Page setup

- Paper size: **Letter portrait** (`8.5in × 11in`). The uploaded PDF page size is 612 × 792 pt.
- Use **Times New Roman** throughout.
- Use **black text** and **black table borders** only.
- Use compact statutory-form spacing.
- Keep left-aligned table blocks as in the source; do not center the large summary tables across the full page.
- Preserve the large blank/right-side whitespace visible on the source pages.
- Do not add logos, colours, watermarks, headers, decorative footers, or explanatory notes inside the recreated form.
- The original PDF does **not** show clear page numbers. Do not add page numbers unless the downstream generator specifically requires them.

### Typography

| Element | Style |
|---|---|
| Main form title | Bold, approx. 20-22 pt, centered toward upper-right visual area, three-line wrapping |
| Subtitle in parentheses | Italic, approx. 14-15 pt, centered below title |
| Section headings | Bold, approx. 13-14 pt |
| Table headers | Bold, approx. 10.5-11.5 pt |
| Table cells | Approx. 10.5-11.5 pt, compact line-height |
| Advisory column | Approx. 10.5-11 pt, narrow wrapped text |
| Instructions | Approx. 11 pt, compact, left aligned |

### Table style

- All tables must use `border-collapse: collapse`.
- All cells use `1px solid #000` borders.
- Header text is bold.
- Keep the exact statutory headings, including visible spelling and spacing such as:
  - `Centra l`
  - `State/U T tax`
  - `GSTR3B`
  - `netoff`
  - `releva headings`
  - `FORM GSTR3B`
- Long labels must wrap inside cells; do not widen the table beyond the prescribed width.
- Summary rows and part rows must span the full table width.
- Where the uploaded form is visibly clipped or cut off at a page boundary, preserve the visible text and do not invent hidden content.

---

## 2. Placeholder Convention

Use placeholders in double curly braces.

```handlebars
{{financial_year}}
{{month}}
{{gstin}}
{{legal_name}}
{{trade_name}}
{{date_of_generation}}
{{table3.partA.all_other_itc.integrated_tax}}
```

For every summary amount row, use the same amount object shape:

```json
{
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": ""
}
```

---

## 3. Required Data Schema

The document generator should accept the following data structure. The rows in the form are mostly fixed statutory rows; only the cell values are variable.

```json
{
  "financial_year": "",
  "month": "",
  "gstin": "",
  "legal_name": "",
  "trade_name": "",
  "date_of_generation": "",

  "table3": {
    "partA": {
      "all_other_itc": {
        "summary": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
        "details": {
          "b2b_invoices": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_debit_notes": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "eco_documents": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_invoices_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_debit_notes_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "eco_documents_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" }
        }
      },
      "inward_supplies_from_isd": {
        "summary": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
        "details": {
          "isd_invoices": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "isd_invoices_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" }
        }
      },
      "inward_supplies_reverse_charge": {
        "summary": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
        "details": {
          "b2b_invoices": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_debit_notes": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_invoices_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_debit_notes_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" }
        }
      },
      "import_of_goods": {
        "summary": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
        "details": {
          "impg_import_goods_overseas": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "impg_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "imgsez_import_goods_sez": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "imgsez_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" }
        }
      }
    },
    "partB": {
      "others": {
        "summary": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
        "details": {
          "b2b_credit_notes": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_credit_notes_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_credit_notes_reverse_charge": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_credit_notes_reverse_charge_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "isd_credit_notes": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "isd_credit_notes_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" }
        }
      }
    }
  },

  "table4": {
    "partA": {
      "all_other_itc": {},
      "inward_supplies_from_isd": {},
      "inward_supplies_reverse_charge": {}
    },
    "partB": {
      "others": {}
    }
  },

  "table5": {
    "partA": {
      "itc_reversal_rule37a": {
        "summary": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
        "details": {
          "b2b_invoices": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_debit_notes": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_invoices_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" },
          "b2b_debit_notes_amendment": { "integrated_tax": "", "central_tax": "", "state_ut_tax": "", "cess": "" }
        }
      }
    }
  }
}
```

For `table4`, reuse the same internal row names as the matching sections in `table3`. The heading rows and advisory text are fixed.

---

## 4. CSS to Use

Embed this CSS in the generated HTML/PDF. Adjust only if the downstream renderer clips text, but do not change the statutory identity of the form.

```html
<style>
  @page {
    size: Letter portrait;
    margin: 10mm 10mm 8mm 7mm;
  }

  body {
    font-family: "Times New Roman", Times, serif;
    color: #000;
    font-size: 11pt;
    line-height: 1.05;
    margin: 0;
  }

  .page {
    page-break-after: always;
    position: relative;
    min-height: 258mm;
  }

  .page:last-child { page-break-after: auto; }

  .title-block {
    text-align: center;
    margin-top: 5mm;
  }

  .main-title {
    font-weight: bold;
    font-size: 20.5pt;
    line-height: 0.95;
    width: 105mm;
    margin-left: 93mm;
  }

  .subtitle {
    font-style: italic;
    font-size: 14.5pt;
    line-height: 1.05;
    margin-top: 2mm;
  }

  .period-table {
    width: 39mm;
    margin: 5mm 0 4mm 91mm;
    border-collapse: collapse;
    table-layout: fixed;
  }

  .period-table td {
    border: 1px solid #000;
    padding: 0.5mm 1mm;
    font-size: 10pt;
    line-height: 0.95;
  }

  .info-table {
    width: 143mm;
    border-collapse: collapse;
    table-layout: fixed;
    margin-top: 3mm;
  }

  .info-table td {
    border: 1px solid #000;
    padding: 1.3mm 1.8mm;
    vertical-align: top;
    font-size: 11pt;
    line-height: 1.0;
  }

  .section-title {
    font-weight: bold;
    font-size: 13.5pt;
    margin: 5.5mm 0 4mm 2mm;
  }

  .amount-note {
    text-align: center;
    font-size: 10.5pt;
    margin: 0 0 7mm 0;
  }

  table.summary-table {
    width: 170mm;
    border-collapse: collapse;
    table-layout: fixed;
    margin: 0 0 0 0;
  }

  .summary-table th,
  .summary-table td {
    border: 1px solid #000;
    padding: 1mm 1mm;
    vertical-align: middle;
    font-size: 11pt;
    line-height: 1.0;
    word-break: normal;
    overflow-wrap: normal;
  }

  .summary-table th {
    font-weight: bold;
    text-align: left;
  }

  .summary-table .head-row th {
    height: 18mm;
  }

  .summary-table .section-row td {
    font-weight: bold;
    text-align: left;
    padding: 0.9mm 1mm;
  }

  .summary-table .part-row td {
    font-weight: bold;
    text-align: left;
    padding: 0.9mm 1mm;
  }

  .summary-table .part-label {
    width: 12mm;
    display: inline-block;
  }

  .center { text-align: center !important; }
  .left { text-align: left !important; }
  .bold { font-weight: bold !important; }
  .top { vertical-align: top !important; }
  .small { font-size: 9.5pt !important; }
  .tiny { font-size: 8.6pt !important; }
  .amt { text-align: right; }
  .advisory { line-height: 0.95; vertical-align: top !important; }
  .blank-tall { height: 82mm; }
  .summary-main { height: 33mm; }
  .detail-row td { height: 8mm; }
  .detail-tall td { height: 13mm; }

  .instructions {
    width: 184mm;
    margin-top: 8mm;
    font-size: 11pt;
    line-height: 1.05;
  }

  .instructions p {
    margin: 1.5mm 0;
  }

  .instructions .indent { margin-left: 10mm; }
  .instructions .indent2 { margin-left: 18mm; }
  .instructions .advisory-box {
    border: 2px solid #000;
    padding: 2mm 4mm;
    width: 148mm;
    margin-left: 7mm;
  }
</style>
```

---

## 5. Reusable Table Column Layout

All main ITC summary tables use this 8-column layout.

```html
<colgroup>
  <col style="width: 8%">
  <col style="width: 22%">
  <col style="width: 10%">
  <col style="width: 14%">
  <col style="width: 14%">
  <col style="width: 11%">
  <col style="width: 8%">
  <col style="width: 13%">
</colgroup>
```

Common header row:

```html
<tr class="head-row">
  <th>S.No.</th>
  <th>Heading</th>
  <th>GSTR-<br>3B<br>table</th>
  <th>Integrated<br>Tax (₹)</th>
  <th>Centra l<br><br>Tax<br>(₹)</th>
  <th>State/U<br>T tax<br>(₹)</th>
  <th>Cess<br>(₹)</th>
  <th>Advisory</th>
</tr>
```

---

## 6. Document Template

### Page 1

```html
<div class="page">
  <div class="title-block">
    <div class="main-title">FORM GSTR-2B [See<br>rule 60(7)] Auto-<br>drafted ITC Statement</div>
    <div class="subtitle">(From FORM GSTR-1/IFF including E-Commerce supplies, GSTR-1A, GSTR-<br>5, GSTR-6 and Import data received from ICEGATE)</div>
  </div>

  <table class="period-table">
    <tr><td>Financial<br>Year</td><td>{{financial_year}}</td></tr>
    <tr><td>Month</td><td>{{month}}</td></tr>
  </table>

  <table class="info-table">
    <colgroup><col style="width: 39%"><col style="width: 61%"></colgroup>
    <tr><td>1. GSTIN</td><td>{{gstin}}</td></tr>
    <tr><td>2(a). Legal name of the<br>registered person</td><td>{{legal_name}}</td></tr>
    <tr><td>2(b). Trade name, if any</td><td>{{trade_name}}</td></tr>
    <tr><td>2(c). Date of generation</td><td>{{date_of_generation}}</td></tr>
  </table>

  <div class="section-title">3. &nbsp; ITC Available Summary</div>
  <div class="amount-note">(Amount in ₹ for all tables)</div>

  <table class="summary-table">
    <colgroup>
      <col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%">
    </colgroup>
    <tr class="head-row">
      <th>S.No.</th><th>Heading</th><th>GSTR-<br>3B<br>table</th><th>Integrated<br>Tax (₹)</th><th>Centra l<br><br>Tax<br>(₹)</th><th>State/U<br>T tax<br>(₹)</th><th>Cess<br>(₹)</th><th>Advisory</th>
    </tr>
    <tr class="section-row"><td colspan="8">Credit which may be availed under FORM GSTR-<br>3B</td></tr>
    <tr class="part-row"><td colspan="8"><span class="part-label">Part<br>A</span> ITC Available - Credit may be<br>claimed in relevant headings in<br><span style="margin-left:18mm;">GSTR-3B</span></td></tr>

    <tr class="summary-main">
      <td class="center">I</td>
      <td>All other ITC<br>- Supplies<br>from<br>registered<br>persons<br>other than<br>reverse<br>charge</td>
      <td class="bold">4(A)(5)</td>
      <td class="amt">{{table3.partA.all_other_itc.summary.integrated_tax}}</td>
      <td class="amt">{{table3.partA.all_other_itc.summary.central_tax}}</td>
      <td class="amt">{{table3.partA.all_other_itc.summary.state_ut_tax}}</td>
      <td class="amt">{{table3.partA.all_other_itc.summary.cess}}</td>
      <td class="advisory">Net input<br>tax credit<br>may be<br>availed<br>under<br>Table<br>4(A)(5) of<br>FORM<br>GSTR-3B.</td>
    </tr>
    <tr class="detail-row"><td rowspan="6">Detail<br>s</td><td>B2B -<br>Invoices</td><td rowspan="6"></td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices.integrated_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices.central_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices.state_ut_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices.cess}}</td><td rowspan="6"></td></tr>
    <tr class="detail-row"><td>B2B - Debit<br>notes</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes.integrated_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes.central_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes.state_ut_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes.cess}}</td></tr>
    <tr class="detail-row"><td>ECO -<br>Documents</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents.integrated_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents.central_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents.state_ut_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B -<br>Invoices<br>(Amendment)</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices_amendment.central_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_invoices_amendment.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B -<br>Debit notes<br>(Amendment)</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes_amendment.central_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.b2b_debit_notes_amendment.cess}}</td></tr>
    <tr class="detail-tall"><td>ECO -<br><br>Documents<br>(Amendment)</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents_amendment.central_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.all_other_itc.details.eco_documents_amendment.cess}}</td></tr>

    <tr class="summary-main">
      <td class="center">II</td>
      <td class="bold">Inward<br>Supplies<br>from ISD</td>
      <td class="bold">4(A)(4)</td>
      <td class="amt">{{table3.partA.inward_supplies_from_isd.summary.integrated_tax}}</td>
      <td class="amt">{{table3.partA.inward_supplies_from_isd.summary.central_tax}}</td>
      <td class="amt">{{table3.partA.inward_supplies_from_isd.summary.state_ut_tax}}</td>
      <td class="amt">{{table3.partA.inward_supplies_from_isd.summary.cess}}</td>
      <td class="advisory">Net input<br>tax credit<br>may be<br>availed<br>under</td>
    </tr>
  </table>
</div>
```

### Page 2

This page continues Table 3 Part A. The upper part of the source page begins with the tail-end of Section II and then Section III.

```html
<div class="page">
  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>

    <tr><td colspan="7"></td><td>GSTR-3B.</td></tr>
    <tr class="detail-row"><td rowspan="2">Detail<br>s</td><td>ISD -<br>Invoices</td><td rowspan="2"></td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices.cess}}</td><td rowspan="2"></td></tr>
    <tr class="detail-tall"><td>ISD -<br><br>Invoices<br>(Amendment)</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices_amendment.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_from_isd.details.isd_invoices_amendment.cess}}</td></tr>

    <tr class="summary-main">
      <td class="center">III</td><td class="bold">Inward<br>Supplies<br>liable for<br>reverse<br>charge</td><td class="bold">3.1(d)<br>4(A)<br>(3)</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.summary.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.summary.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.summary.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.summary.cess}}</td><td class="advisory">These<br>supplies<br>shall be<br>declared</td>
    </tr>
  </table>

  <br>

  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>
    <tr class="head-row"><th>S.No.</th><th>Heading</th><th>GSTR-<br>3B<br>table</th><th>Integrated<br>Tax (₹)</th><th>Centra<br>l<br><br>Tax<br>(₹)</th><th>State/U<br>T tax<br>(₹)</th><th>Cess<br>(₹)</th><th>Advisory</th></tr>
    <tr>
      <td colspan="7" class="blank-tall"></td>
      <td class="advisory">in Table<br>3.1(d) of<br><br>FORM<br><br>GSTR-3B<br><br>for<br>payment<br>of tax.<br>Net<br>input tax<br>credit<br>may be<br>availed<br>under<br>Table<br>4A(3)<br>of<br><br>FORM<br><br>GSTR-3B<br>on<br>payment<br>of tax.</td>
    </tr>
    <tr class="detail-row"><td rowspan="4">Detail<br><br>s</td><td>B2B -<br>Invoices</td><td rowspan="4"></td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices.cess}}</td><td rowspan="4"></td></tr>
    <tr class="detail-row"><td>B2B - Debit<br>notes</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Invoices<br>-<br>(Amendment)</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices_amendment.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_invoices_amendment.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B - &nbsp;&nbsp;&nbsp;&nbsp; notes<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Debit<br>(Amendment)</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.central_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.cess}}</td></tr>

    <tr class="summary-main"><td class="center">IV</td><td class="bold">Import of<br>Goods</td><td class="bold">4(A)(1)</td><td class="amt">{{table3.partA.import_of_goods.summary.integrated_tax}}</td><td class="amt">{{table3.partA.import_of_goods.summary.central_tax}}</td><td class="amt">{{table3.partA.import_of_goods.summary.state_ut_tax}}</td><td class="amt">{{table3.partA.import_of_goods.summary.cess}}</td><td class="advisory">Net<br>input tax<br>credit<br>may be<br>availed<br>under<br>Table<br><br>4(A)(1) of<br><br>FORM<br><br>GSTR-3B.</td></tr>
  </table>
</div>
```

### Page 3

This page continues Table 3 Part A import details, then Table 3 Part B, and starts Section 4.

```html
<div class="page">
  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>
    <tr class="detail-row"><td rowspan="4">Detail<br><br>s</td><td>IMPG - Import of<br>goods from overseas</td><td rowspan="4"></td><td class="amt">{{table3.partA.import_of_goods.details.impg_import_goods_overseas.integrated_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.impg_import_goods_overseas.central_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.impg_import_goods_overseas.state_ut_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.impg_import_goods_overseas.cess}}</td><td rowspan="4"></td></tr>
    <tr class="detail-row"><td>IMPG (Amendment)</td><td class="amt">{{table3.partA.import_of_goods.details.impg_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.impg_amendment.central_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.impg_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.impg_amendment.cess}}</td></tr>
    <tr class="detail-row"><td>IMGSEZ - Import of<br>goods from SEZ</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_import_goods_sez.integrated_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_import_goods_sez.central_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_import_goods_sez.state_ut_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_import_goods_sez.cess}}</td></tr>
    <tr class="detail-row"><td>IMGSEZ<br>(Amendment)</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_amendment.integrated_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_amendment.central_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_amendment.state_ut_tax}}</td><td class="amt">{{table3.partA.import_of_goods.details.imgsez_amendment.cess}}</td></tr>

    <tr class="part-row"><td colspan="8"><span class="part-label">Part<br>B</span> ITC Available - Credit Notes should be net-off against relevant<br>available headings<br><span style="margin-left:28mm;">in GSTR-3B</span></td></tr>
    <tr class="summary-main"><td class="center">I</td><td class="bold">Others</td><td class="bold">4(A)</td><td class="amt">{{table3.partB.others.summary.integrated_tax}}</td><td class="amt">{{table3.partB.others.summary.central_tax}}</td><td class="amt">{{table3.partB.others.summary.state_ut_tax}}</td><td class="amt">{{table3.partB.others.summary.cess}}</td><td class="advisory">Credit<br>Notes<br>shall<br>be<br><br>net-off</td></tr>

    <tr class="head-row"><th>S.No.</th><th>Heading</th><th>GSTR-<br>3B<br>table</th><th>Integrated<br>Tax (₹)</th><th>Centra l<br><br>Tax<br>(₹)</th><th>State/U<br>T tax<br>(₹)</th><th>Cess<br>(₹)</th><th>Advisory</th></tr>
    <tr><td colspan="7" class="blank-tall"></td><td class="advisory">against<br>relevant<br>ITC<br><br>available<br>tables<br>[Table<br>4A(3,4,5)]<br>. Liability<br>against<br>Credit<br><br>Notes<br>(Reverse<br>Charge)<br>shall be<br>net-off in<br><br>Table<br><br>3.1(d).</td></tr>
    <tr class="detail-row"><td rowspan="6">Detail<br><br>s</td><td>B2B - Credit<br>notes</td><td class="bold">4(A)(5)</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes.integrated_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes.central_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes.state_ut_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes.cess}}</td><td rowspan="6"></td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; notes<br>Credit<br>(Amendment)</td><td class="bold">4(A)(5)</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_amendment.integrated_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_amendment.central_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_amendment.cess}}</td></tr>
    <tr class="detail-row"><td>B2B - Credit notes<br>(Reverse charge)</td><td class="bold">3.1(d)<br><br>4(A)(3)</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge.integrated_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge.central_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge.state_ut_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B - Credit notes<br>(Reverse charge)<br>(Amendment)</td><td class="bold">3.1(d)<br><br>4(A)(3)</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge_amendment.integrated_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge_amendment.central_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge_amendment.state_ut_tax}}</td><td class="amt">{{table3.partB.others.details.b2b_credit_notes_reverse_charge_amendment.cess}}</td></tr>
    <tr class="detail-row"><td>ISD - Credit<br>notes</td><td class="bold">4(A)(4)</td><td class="amt">{{table3.partB.others.details.isd_credit_notes.integrated_tax}}</td><td class="amt">{{table3.partB.others.details.isd_credit_notes.central_tax}}</td><td class="amt">{{table3.partB.others.details.isd_credit_notes.state_ut_tax}}</td><td class="amt">{{table3.partB.others.details.isd_credit_notes.cess}}</td></tr>
    <tr class="detail-tall"><td>ISD &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; - &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Credit<br>notes<br>(Amendment)</td><td class="bold">4(A)(4)</td><td class="amt">{{table3.partB.others.details.isd_credit_notes_amendment.integrated_tax}}</td><td class="amt">{{table3.partB.others.details.isd_credit_notes_amendment.central_tax}}</td><td class="amt">{{table3.partB.others.details.isd_credit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table3.partB.others.details.isd_credit_notes_amendment.cess}}</td></tr>
  </table>

  <div class="section-title" style="margin-top:10mm;">4. &nbsp; ITC Not Available Summary</div>
  <div class="amount-note">(Amount in ₹ in all sections)</div>
</div>
```

### Page 4

This page contains Section 4, Part A, including continuation-style header rows.

```html
<div class="page">
  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>
    <tr class="head-row"><th>S.n<br>o.</th><th>Heading</th><th>GST<br>R-3B<br>Table</th><th>Integr<br>ated<br>Tax<br>(₹)</th><th>Centra l<br><br>Tax<br>(₹)</th><th>State/<br>UT<br>tax<br>(₹)</th><th>Cess<br>(₹)</th><th>Advisory</th></tr>
    <tr class="section-row"><td colspan="8">Credit which may not be availed under FORM<br>GSTR-3B</td></tr>
    <tr class="part-row"><td colspan="8">Par<br><span style="margin-left:12mm;">ITC Not Available</span><br>t A</td></tr>

    <tr class="summary-main"><td class="center">I</td><td class="bold">All other ITC -<br>Supplies from<br>registered persons<br>other than reverse<br>charge</td><td class="bold">4(D)(<br>2)</td><td class="amt">{{table4.partA.all_other_itc.summary.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.summary.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.summary.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.summary.cess}}</td><td class="advisory">Such credit<br>shall not be<br>taken and<br>has to be<br>reported in<br>table 4(D)<br>(2) of<br>FORM<br>GSTR-3B.</td></tr>
    <tr class="detail-row"><td rowspan="6">Det<br>ails</td><td>B2B - Invoices</td><td rowspan="6"></td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices.cess}}</td><td rowspan="6"></td></tr>
    <tr class="detail-row"><td>B2B - Debit notes</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes.cess}}</td></tr>
    <tr class="detail-row"><td>ECO - Documents</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; -<br>Invoices<br>(Amendment)</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices_amendment.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices_amendment.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices_amendment.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_invoices_amendment.cess}}</td></tr>

    <tr class="head-row"><th>S.n<br>o.</th><th>Heading</th><th>GST<br>R-3B<br>Table</th><th>Integr<br>ated<br>Tax<br>(₹)</th><th>Centra l<br><br>Tax<br>(₹)</th><th>State/<br>UT<br>tax<br>(₹)</th><th>Cess<br>(₹)</th><th>Advisory</th></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Debit<br>notes<br>(Amendment)</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes_amendment.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes_amendment.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.b2b_debit_notes_amendment.cess}}</td></tr>
    <tr class="detail-tall"><td class="center">II</td><td>ECO -<br>Documents<br><br>(Amendment)</td><td></td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents_amendment.integrated_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents_amendment.central_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents_amendment.state_ut_tax}}</td><td class="amt">{{table4.partA.all_other_itc.details.eco_documents_amendment.cess}}</td><td></td></tr>

    <tr class="summary-main"><td></td><td class="bold">Inward Supplies<br>from ISD</td><td class="bold">4(D)(<br>2)</td><td class="amt">{{table4.partA.inward_supplies_from_isd.summary.integrated_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.summary.central_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.summary.state_ut_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.summary.cess}}</td><td class="advisory">Such<br>credit<br>shall not<br>be taken<br>and has to<br>be<br>reported<br>in table<br>4(D)(2) of<br><br>FORM<br>GSTR-3B</td></tr>
    <tr class="detail-row"><td rowspan="2">Det<br>ails</td><td>ISD - Invoices</td><td rowspan="2" class="bold">3.1(d)</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices.integrated_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices.central_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices.state_ut_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices.cess}}</td><td rowspan="2"></td></tr>
    <tr class="detail-tall"><td>ISD -<br>Invoices<br><br>(Amendment)</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices_amendment.integrated_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices_amendment.central_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices_amendment.state_ut_tax}}</td><td class="amt">{{table4.partA.inward_supplies_from_isd.details.isd_invoices_amendment.cess}}</td></tr>

    <tr class="summary-main"><td class="center">III</td><td class="bold">Inward Supplies<br>liable for reverse<br>charge</td><td class="bold">4(D)(<br>2)</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.summary.integrated_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.summary.central_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.summary.state_ut_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.summary.cess}}</td><td class="advisory">These<br>supplies<br>shall be<br>declared<br>in Table<br>3.1(d) of<br>FORM<br>GSTR-3B<br>for<br>payment<br>of tax.</td></tr>
    <tr class="detail-row"><td></td><td>B2B - Invoices</td><td></td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_invoices.integrated_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_invoices.central_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_invoices.state_ut_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_invoices.cess}}</td><td></td></tr>
  </table>
</div>
```

### Page 5

This page continues Section 4 and then starts Section 5.

```html
<div class="page">
  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>
    <tr class="detail-tall"><td></td><td>(Amendment)</td><td></td><td></td><td></td><td></td><td></td><td rowspan="2">nt ITC</td></tr>
    <tr class="detail-tall"><td></td><td>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Debit<br>notes<br><br>(Amendment)</td><td></td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.integrated_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.central_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table4.partA.inward_supplies_reverse_charge.details.b2b_debit_notes_amendment.cess}}</td></tr>

    <tr class="part-row"><td colspan="8">Part B ITC Not Available - Credit notes should be net-off available<br>against releva headings in GSTR-3B</td></tr>
    <tr class="summary-main"><td class="center">I</td><td class="bold">Others</td><td class="bold">4(A)</td><td class="amt">{{table4.partB.others.summary.integrated_tax}}</td><td class="amt">{{table4.partB.others.summary.central_tax}}</td><td class="amt">{{table4.partB.others.summary.state_ut_tax}}</td><td class="amt">{{table4.partB.others.summary.cess}}</td><td class="advisory">Credit<br>Notes<br>should be<br>netoff<br>against<br>relevant<br>ITC<br>available<br>tables<br>[Table<br>4A(3,4,5)].</td></tr>
    <tr class="detail-row"><td rowspan="6">Det<br>ails</td><td>B2B - Credit<br>notes</td><td class="bold">4(A)(<br>5)</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes.integrated_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes.central_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes.state_ut_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes.cess}}</td><td rowspan="6"></td></tr>
    <tr class="detail-tall"><td>notes<br>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; -<br><br>Credit<br>(Amendment)</td><td class="bold">4(A)(<br>5)</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_amendment.integrated_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_amendment.central_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_amendment.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp; - &nbsp;&nbsp;&nbsp; notes<br>Credit<br><br>(Reverse<br>charge)</td><td class="bold">4(A)(<br>3)</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge.integrated_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge.central_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge.state_ut_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge.cess}}</td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp; - &nbsp;&nbsp;&nbsp; notes<br>Credit &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; charge)<br><br>(Reverse<br><br>(Amendment)</td><td class="bold">4(A)(<br>3)</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge_amendment.integrated_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge_amendment.central_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge_amendment.state_ut_tax}}</td><td class="amt">{{table4.partB.others.details.b2b_credit_notes_reverse_charge_amendment.cess}}</td></tr>
    <tr class="detail-row"><td>ISD - Credit<br>notes</td><td class="bold">4(A)(<br>4)</td><td class="amt">{{table4.partB.others.details.isd_credit_notes.integrated_tax}}</td><td class="amt">{{table4.partB.others.details.isd_credit_notes.central_tax}}</td><td class="amt">{{table4.partB.others.details.isd_credit_notes.state_ut_tax}}</td><td class="amt">{{table4.partB.others.details.isd_credit_notes.cess}}</td></tr>
    <tr class="detail-tall"><td>notes<br>ISD &nbsp;&nbsp;&nbsp;&nbsp;&nbsp; -<br><br>Credit<br>(Amendment)</td><td class="bold">4(A)(<br>4)</td><td class="amt">{{table4.partB.others.details.isd_credit_notes_amendment.integrated_tax}}</td><td class="amt">{{table4.partB.others.details.isd_credit_notes_amendment.central_tax}}</td><td class="amt">{{table4.partB.others.details.isd_credit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table4.partB.others.details.isd_credit_notes_amendment.cess}}</td></tr>
  </table>

  <div class="section-title" style="margin-top:7mm;">5. &nbsp; ITC Reversal Summary (Rule 37A)</div>
  <div class="amount-note">(Amount in ₹ in all sections)</div>

  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>
    <tr class="head-row"><th>S.n<br>o.</th><th>Heading</th><th>GST<br>R-3B<br>Table</th><th>Integr<br>ated<br>Tax<br>(₹)</th><th>Centra l<br><br>Tax<br>(₹)</th><th>State/<br>UT<br>tax<br>(₹)</th><th>Cess<br>(₹)</th><th>Advisory</th></tr>
    <tr class="section-row"><td colspan="8">Credit which may be reversed under<br>FORM GSTR-3B</td></tr>
    <tr class="part-row"><td colspan="8">Par<br><span style="margin-left:18mm;">ITC Reversed - Others</span><br>t A</td></tr>
    <tr class="summary-main"><td class="center">I</td><td class="bold">ITC<br>Reversal on<br>account of<br>Rule 37A</td><td class="bold">4(B)(<br>2)</td><td class="amt">{{table5.partA.itc_reversal_rule37a.summary.integrated_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.summary.central_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.summary.state_ut_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.summary.cess}}</td><td class="advisory">Such<br>credit<br>shall be<br>reversed<br>and has to<br>be<br>reported<br>in table<br>4(B)(2) of</td></tr>
  </table>
</div>
```

### Page 6

This page continues Section 5 details and then contains the Instructions. Instruction 8 is visibly cut at the page bottom in the uploaded PDF; only visible text is reproduced.

```html
<div class="page">
  <table class="summary-table">
    <colgroup><col style="width: 8%"><col style="width: 22%"><col style="width: 10%"><col style="width: 14%"><col style="width: 14%"><col style="width: 11%"><col style="width: 8%"><col style="width: 13%"></colgroup>
    <tr class="detail-row"><td class="center">I</td><td>B2B -<br>Invoices</td><td></td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices.integrated_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices.central_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices.state_ut_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices.cess}}</td><td></td></tr>
    <tr class="detail-row"><td rowspan="3">Det<br>ails</td><td>B2B - Debit<br>notes</td><td></td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes.integrated_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes.central_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes.state_ut_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes.cess}}</td><td></td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;-<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Invoices<br>(Amendment)</td><td></td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices_amendment.integrated_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices_amendment.central_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices_amendment.state_ut_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_invoices_amendment.cess}}</td><td></td></tr>
    <tr class="detail-tall"><td>B2B &nbsp;&nbsp;&nbsp;&nbsp; -<br>Debit notes<br>(Amendment)</td><td></td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes_amendment.integrated_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes_amendment.central_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes_amendment.state_ut_tax}}</td><td class="amt">{{table5.partA.itc_reversal_rule37a.details.b2b_debit_notes_amendment.cess}}</td><td></td></tr>
  </table>

  <div class="instructions">
    <p>Instructions:</p>
    <p class="indent">1. Terms Used :-</p>
    <p class="indent2">a. &nbsp; ITC - Input tax credit</p>
    <p class="indent2">b. &nbsp; B2B - Business to Business</p>
    <p class="indent2">c. &nbsp; ISD - Input service distributor</p>
    <p class="indent2">d. &nbsp; IMPG - Import of goods</p>
    <p class="indent2">e. &nbsp; IMPGSEZ - Import of goods from SEZ</p>
    <p class="indent2">f. &nbsp; ECO - E-Commerce Operator</p>

    <div class="advisory-box">
      <p>2. &nbsp; <b>Important Advisory:</b></p>
      <p class="indent">a) &nbsp; FORM GSTR-2B is a statement which has been generated on<br>the basis of the information furnished by your suppliers or by<br>ECOs in their respective FORMS GSTR-1/IFF, 1A, 5 and 6. It is<br>a static statement and will be made available once a month.<br>The documents filed by the Supplier in any FORMS GSTR-<br>1/IFF, 5 and 6 would reflect in the next open FORM GSTR-2B<br>of the recipient irrespective of suppliers date of filing.<br>Taxpayers are advised to refer FORM GSTR-2B for availing<br>credit in FORM GSTR-3B. However, in case of additional<br>details, they may refer to their respective FORM GSTR-2A<br>(which is updated on near real time basis) for more details.</p>
      <p class="indent">b) &nbsp; In addition, the supplies declared or amended in FORM GSTR-<br>1A shall be made available in the next open FORM GSTR-2B.</p>
      <p class="indent">c) &nbsp; Input tax credit shall be indicated to be non-available in the<br>following scenarios: -</p>
      <p class="indent2">i. &nbsp;&nbsp;&nbsp;&nbsp; Invoice or debit note for supply of goods or services<br>or both where the recipient is not entitled to input tax<br>credit as per the provisions of sub-section (4) of<br>Section 16 of CGST Act, 2017.</p>
      <p class="indent2">ii. &nbsp;&nbsp;&nbsp; Invoice or debit note where the Supplier (GSTIN)<br>and place of supply are in the same State while<br>recipient is in another State.</p>
      <p>However, there may be other scenarios for which input tax credit<br>may not be available to the taxpayers and the same has not been<br>generated by the system. Taxpayers should self-assess and<br>reverse such credit in their FORM GSTR-3B.</p>
    </div>

    <p>3. &nbsp; It may be noted that FORM GSTR-2B will consist of all the GSTR-1/IFFs,5s and 6s being filed by your<br>respective supplier or by ECOs. Generally, this date will be between filing date of<br>GSTR1(Monthly/Quarterly)/IFF for previous month (M-1) to filing date of GSTR-1(Monthly/Quarterly)/IFF<br>for the current month (M). For example, GSTR-2B for the month of February will consist of all the documents<br>filed by suppliers in their GSTR-1/IFF, 5 and 6 from 00:00 hours on 12<sup>th</sup> February to 23:59 hours on 11<sup>th</sup> March.<br>It may be noted that for import of goods, the data is being updated on real time basis, therefore, imports made<br>in the month (month for which GSTR-2B is being generated for) shall be made available. The dates for which the<br>relevant data has been extracted is available under the<br>—View Advisory|| tab on the online portal.</p>

    <p>4. &nbsp; It also contains information on imports of goods from the ICEGATE system including data on imports from<br>Special Economic Zones Units / Developers.</p>

    <p>5. &nbsp; It may be noted that reverse charge credit on import of services is not part of this statement and will be<br>continued to be entered by taxpayers in Table 4(A)(2) of FORM GSTR-3B.</p>

    <p>6. &nbsp; Table 3 captures the summary of ITC available as on the date of generation of GSTR-2B. It is divided into<br>following two parts:</p>
    <p class="indent">A. &nbsp; Part A captures the summary of credit that may be availed in relevant tables of FORM GSTR-3B.</p>
    <p class="indent">B. &nbsp; Part B captures the summary of credit that shall be net-off from &nbsp; relevant table of FORM GSTR3B.</p>

    <p>7. &nbsp; Table 4 captures the summary of ITC not available as on the date of generation of GSTR-2B. Credit available in<br>this table shall not be availed as credit in FORM GSTR-3B but to be reported as ineligible ITC in Table 4(D)(2) of<br>FORM GSTR-3B. However, the liability to pay tax on reverse charge basis and the liability to net-off &nbsp; credit on<br>receipt of credit notes continues for such supplies.</p>

    <p>8. &nbsp; Table 5 captures the summary of ITC to be reversed under Rule 37A on or before 30th November following the<br>end of financial year in which the ITC in respect of such invoice or debit note has been availed and</p>
  </div>
</div>
```

---

## 7. Accuracy Notes for Reproduction

1. The source file is a 6-page image-based PDF with no selectable parsed text.
2. The tables visibly continue across page boundaries. Preserve continuation behaviour.
3. Page 4 and page 5 begin mid-table; this is intentional and should be retained for exact visual recreation.
4. Page 6 instruction 8 is visibly cut off at the bottom of the source page. The template reproduces only the visible portion.
5. Do not normalize `GSTR3B` to `GSTR-3B` in the instruction line where the source shows `GSTR3B`.
6. Do not correct `releva headings`, `netoff`, or split words in headers if exact source matching is required.
7. Use the same tax column order everywhere: Integrated Tax, Central Tax, State/UT tax, Cess.
8. Leave amount cells blank unless data is supplied.

---

## 8. Final AI Instruction Block

Copy this instruction into the AI that will generate the final document:

```text
Recreate FORM GSTR-2B exactly as per the provided Markdown/HTML specification. Use Letter portrait page setup, Times New Roman, black text, black table borders, compact statutory layout, and the same six-page continuation structure. Treat the statutory rows as fixed and insert variable data only into the placeholders. Preserve original wording, visible line breaks, awkward header splits, table continuation, and clipped Instruction 8 exactly as shown. Do not redesign, simplify, modernize, correct spelling, add logos, add colours, add watermarks, or add page numbers unless separately instructed.
```
