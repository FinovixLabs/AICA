# FORM GSTR-2A - Exact Recreation Markdown Specification

Use this file as the master prompt/specification for recreating the uploaded **FORM GSTR-2A** document in the same statutory format. The number of data entries in each table is variable; therefore every data table below must be generated from arrays/lists and must expand or continue onto the next page as required.

> **Important:** Native Markdown tables cannot reproduce this form accurately because the source document uses merged cells, nested headers, very narrow columns, fixed borders, row groups, page breaks and compact statutory table geometry. Recreate the document using **HTML/CSS inside Markdown** or convert the HTML to PDF/DOCX. Preserve the visual appearance of the original form.

---

## 1. Output Rules

### Page setup

- Paper size: **A4 portrait**.
- Margins: approximately **15 mm left/right**, **14-18 mm top**, **12-16 mm bottom**.
- Font family: **Times New Roman** for headings, tables and body text.
- Use black text and black table borders only.
- Do not add logos, colours, watermarks, decorative headers or decorative footers.
- Keep the form compact. Avoid extra spacing.
- Source PDF has **3 pages**. Recreate the same section order and page flow.
- The source has no visible running page number; do not insert page numbers unless specifically required by the generator.

### Typography

| Element | Style |
|---|---|
| Main title | Centered, bold, approx. 12-13 pt |
| Rule reference | Right aligned near top-right, bold, approx. 10 pt |
| Form subtitle | Centered inside a thin bordered rectangle |
| Part headings | Centered, bold, underlined, approx. 11-12 pt |
| Section headings | Bold, approx. 10.5-11 pt |
| Table text | Approx. 7.4-8.5 pt, compact |
| Instructions | Approx. 10 pt |
| Footnote markers | Superscript |

### Table style

- All tables must use `border-collapse: collapse`.
- Border: `1px solid #000`.
- Use `table-layout: fixed` for all statutory tables.
- Header cells: centered vertically and horizontally unless source text is left-aligned.
- Long header text must wrap inside cells; do not widen page.
- Blank entry rows must remain bordered.
- For variable entries, repeat one row per data item.
- If a section has no entries, keep at least **one blank entry row** so the form structure remains visible.
- If a variable table spills to a new page, repeat the relevant table header on the continuation page.

---

## 2. Placeholder Convention

Use placeholders in double curly braces.

Example:

```handlebars
{{gstin}}
{{legal_name}}
{{trade_name}}
{{year}}
{{month}}
{{#each table3_inward_registered}}
  {{this.gstin_supplier}}
{{/each}}
```

For digit boxes, print one character per cell. If empty, leave the cell blank.

---

## 3. Required Data Schema

The AI/document generator must accept data in this structure. The arrays may contain any number of entries.

```json
{
  "year_digits": ["", "", "", ""],
  "month": "",
  "gstin_digits": ["", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
  "gstin": "",
  "legal_name": "",
  "trade_name": "",

  "table3_inward_registered": [],
  "table4_amend_inward_registered": [],
  "table5_debit_credit_notes": [],
  "table6_amend_debit_credit_notes": [],

  "table7_isd_credit_received": [],
  "table8_amend_isd_credit_details": [],

  "table9A_tds_credit": [],
  "table9B_tcs_credit": [],

  "table10_import_goods_overseas": [],
  "table11_sez_import_goods": []
}
```

### Table object field names

#### `table3_inward_registered`

```json
{
  "gstin_supplier": "",
  "trade_legal_name": "",
  "invoice_no": "",
  "invoice_type": "",
  "invoice_date": "",
  "invoice_value": "",
  "rate_percent": "",
  "taxable_value": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "place_of_supply": "",
  "reverse_charge": "",
  "gstr_1_1a_5_period": "",
  "gstr_1_1a_5_filing_date": "",
  "gstr_3b_filing_status": "",
  "amendment_made": "",
  "tax_period_amended": "",
  "effective_cancellation_date": ""
}
```

#### `table4_amend_inward_registered`

```json
{
  "original_document_no": "",
  "original_document_date": "",
  "revised_gstin_supplier": "",
  "revised_trade_legal_name": "",
  "revised_invoice_no": "",
  "revised_invoice_type": "",
  "revised_invoice_date": "",
  "revised_invoice_value": "",
  "rate_percent": "",
  "taxable_value": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "place_of_supply": "",
  "reverse_charge": "",
  "gstr_1_1a_5_period": "",
  "gstr_1_1a_5_filing_date": "",
  "gstr_3b_filing_status": "",
  "amendment_made": "",
  "tax_period_original_record": "",
  "effective_cancellation_date": ""
}
```

#### `table5_debit_credit_notes`

```json
{
  "gstin_supplier": "",
  "trade_legal_name": "",
  "note_no": "",
  "note_type": "",
  "note_supply_type": "",
  "note_date": "",
  "note_value": "",
  "rate_percent": "",
  "taxable_value": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "place_of_supply": "",
  "reverse_charge": "",
  "gstr_1_1a_5_period": "",
  "gstr_1_1a_5_filing_date": "",
  "gstr_3b_filing_status": "",
  "amendment_made": "",
  "tax_period_amended": "",
  "effective_cancellation_date": ""
}
```

#### `table6_amend_debit_credit_notes`

```json
{
  "original_document_type": "",
  "original_document_no": "",
  "original_document_date": "",
  "revised_gstin_supplier": "",
  "revised_trade_legal_name": "",
  "revised_note_no": "",
  "revised_note_type": "",
  "revised_note_supply_type": "",
  "revised_note_date": "",
  "revised_note_value": "",
  "rate_percent": "",
  "taxable_value": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "place_of_supply": "",
  "reverse_charge": "",
  "gstr_1_1a_5_period": "",
  "gstr_1_1a_5_filing_date": "",
  "gstr_3b_filing_status": "",
  "amendment_made": "",
  "tax_period_original_record": "",
  "effective_cancellation_date": ""
}
```

#### `table7_isd_credit_received`

```json
{
  "gstin_isd": "",
  "trade_legal_name": "",
  "isd_document_type": "",
  "isd_document_no": "",
  "isd_document_date": "",
  "isd_invoice_no_for_credit_note": "",
  "isd_invoice_date_for_credit_note": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "gstr_6_period": "",
  "gstr_6_filing_date": "",
  "amendment_made": "",
  "tax_period_amended": "",
  "itc_eligibility": ""
}
```

#### `table8_amend_isd_credit_details`

```json
{
  "original_document_type": "",
  "original_document_no": "",
  "original_document_date": "",
  "original_gstin_isd": "",
  "original_trade_legal_name": "",
  "revised_document_type": "",
  "revised_document_no": "",
  "revised_document_date": "",
  "original_isd_invoice_no_for_credit_note": "",
  "original_isd_invoice_date_for_credit_note": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "gstr_6_period": "",
  "gstr_6_filing_date": "",
  "amendment_made": "",
  "tax_period_original_record": "",
  "itc_eligibility": ""
}
```

#### `table9A_tds_credit` and `table9B_tcs_credit`

```json
{
  "gstin_deductor_or_ecommerce_operator": "",
  "deductor_or_operator_name": "",
  "tax_period_gstr_7_or_8": "",
  "amount_received_gross_value": "",
  "value_of_supplies_returned": "",
  "net_amount_liable_for_tcs": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": ""
}
```

#### `table10_import_goods_overseas`

```json
{
  "icegate_reference_date": "",
  "port_code": "",
  "bill_entry_no": "",
  "bill_entry_date": "",
  "bill_entry_value": "",
  "integrated_tax": "",
  "cess": "",
  "amended_yes_no": ""
}
```

#### `table11_sez_import_goods`

```json
{
  "gstin_supplier_sez": "",
  "trade_legal_name": "",
  "icegate_reference_date": "",
  "port_code": "",
  "bill_entry_no": "",
  "bill_entry_date": "",
  "bill_entry_value": "",
  "integrated_tax": "",
  "cess": "",
  "amended_yes_no": ""
}
```

---

## 4. CSS to Use

Embed this CSS in the generated HTML/PDF. Adjust only if required to fit the page, but do not alter the visual identity.

```html
<style>
  @page {
    size: A4 portrait;
    margin: 15mm 16mm 13mm 16mm;
  }

  body {
    font-family: "Times New Roman", Times, serif;
    color: #000;
    font-size: 10pt;
    line-height: 1.12;
  }

  .page {
    page-break-after: always;
    position: relative;
  }

  .title {
    text-align: center;
    font-weight: bold;
    font-size: 12.5pt;
    margin-top: 4mm;
    margin-bottom: 6mm;
  }

  .rule {
    text-align: right;
    font-weight: bold;
    font-size: 10pt;
    margin: 0 8mm 4mm 0;
  }

  .subtitle-box {
    border: 1px solid #000;
    text-align: center;
    margin: 4mm 0 5mm 0;
    padding: 2.2mm 1mm;
    line-height: 1.05;
  }

  .subtitle-main {
    font-weight: bold;
  }

  .subtitle-sub {
    font-style: italic;
    font-size: 9pt;
  }

  .part-title {
    text-align: center;
    font-weight: bold;
    text-decoration: underline;
    font-size: 11.5pt;
    margin: 7mm 0 4mm 0;
  }

  .tables-label {
    text-align: center;
    font-size: 10pt;
    margin: 0 0 2mm 0;
  }

  .section-title {
    font-weight: bold;
    font-size: 10.8pt;
    margin: 5.5mm 0 2mm 0;
  }

  .amount-note {
    text-align: right;
    font-size: 9.5pt;
    margin: -2mm 8mm 2mm 0;
  }

  table {
    border-collapse: collapse;
    table-layout: fixed;
    margin: 0;
  }

  .full-table {
    width: 100%;
  }

  th, td {
    border: 1px solid #000;
    padding: 0.9mm 0.7mm;
    vertical-align: top;
    font-size: 7.8pt;
    font-weight: normal;
    overflow-wrap: anywhere;
    word-break: normal;
  }

  th {
    text-align: center;
    vertical-align: middle;
  }

  .center { text-align: center; }
  .left { text-align: left; }
  .right { text-align: right; }
  .bold { font-weight: bold; }
  .italic { font-style: italic; }
  .underline { text-decoration: underline; }
  .small { font-size: 7.2pt; }
  .tiny { font-size: 6.7pt; }
  .no-border { border: none !important; }

  .blank-row td { height: 6.5mm; }
  .tall-blank-row td { height: 10mm; }

  .digit-table {
    border-collapse: collapse;
    table-layout: fixed;
    width: auto;
  }

  .digit-table td {
    width: 5.2mm;
    height: 5.2mm;
    text-align: center;
    vertical-align: middle;
    padding: 0;
  }

  .period-box {
    float: right;
    width: 31mm;
    margin: 0 70mm 5mm 0;
  }

  .period-box td {
    height: 8mm;
    font-size: 9pt;
    vertical-align: middle;
  }

  .identity-table {
    width: 68%;
    margin: 0 0 6mm 6mm;
  }

  .identity-table td {
    font-size: 9.2pt;
    vertical-align: middle;
  }

  .section-row td,
  td.section-row {
    font-weight: normal;
    text-align: left;
  }

  .instructions {
    margin-left: 22mm;
    font-size: 10pt;
    line-height: 1.22;
  }

  .instructions p {
    margin: 1.5mm 0;
  }

  .indent { margin-left: 8mm; }
  .nowrap { white-space: nowrap; }
</style>
```

---

## 5. Document Template

### Page 1

```html
<div class="page">
  <div class="title"><sup>1</sup>[FORM GSTR-2A]</div>
  <div class="rule">[See rule 60(1)]</div>

  <div class="subtitle-box">
    <div class="subtitle-main">Details of auto drafted supplies</div>
    <div class="subtitle-sub">(From GSTR1, 1A, GSTR5, GSTR-6, GSTR-7, GSTR-8, import of goods and inward<br>supplies of goods received from SEZ units / developers)</div>
  </div>

  <table class="period-box">
    <tr>
      <td class="left" style="width: 45%">Year</td>
      {{#each year_digits}}<td class="center">{{this}}</td>{{/each}}
    </tr>
    <tr>
      <td class="left">Month</td>
      <td colspan="4" class="center">{{month}}</td>
    </tr>
  </table>
  <div style="clear: both;"></div>

  <table class="identity-table">
    <colgroup>
      <col style="width: 6%"><col style="width: 8%"><col style="width: 38%"><col style="width: 48%">
    </colgroup>
    <tr>
      <td class="center">1.</td>
      <td></td>
      <td>GSTIN</td>
      <td>
        <table class="digit-table"><tr>{{#each gstin_digits}}<td>{{this}}</td>{{/each}}</tr></table>
      </td>
    </tr>
    <tr>
      <td class="center">2.</td>
      <td class="center">(a)</td>
      <td>Legal name of the registered<br>person</td>
      <td>{{legal_name}}</td>
    </tr>
    <tr>
      <td></td>
      <td class="center">(b)</td>
      <td>Trade name, if any</td>
      <td>{{trade_name}}</td>
    </tr>
  </table>

  <div class="part-title">PART A</div>
  <div class="tables-label">Tables)</div>
  <div class="amount-note">(Amount in Rs. all</div>

  <div class="section-title">3. Inward supplies received from a registered person including supplies attracting reverse charge</div>

  <table class="full-table">
    <colgroup>
      <col style="width:5.5%"><col style="width:5.5%"><col style="width:2.8%"><col style="width:2.8%"><col style="width:3.5%"><col style="width:4.5%"><col style="width:3.2%"><col style="width:4%"><col style="width:5.5%"><col style="width:4%"><col style="width:4%"><col style="width:4%"><col style="width:6%"><col style="width:7%"><col style="width:7%"><col style="width:7%"><col style="width:5.5%"><col style="width:7%"><col style="width:5.5%"><col style="width:5.7%">
    </colgroup>
    <tr>
      <th rowspan="2">GSTI<br>N of<br>suppli<br>er</th>
      <th rowspan="2">Trade/<br>Legal<br>name</th>
      <th colspan="4">Invoice<br>details</th>
      <th rowspan="2">Ra<br>te<br>(<br>%<br>)</th>
      <th rowspan="2">Tax<br>able<br>valu<br>e</th>
      <th colspan="4">Amount of<br>tax</th>
      <th rowspan="2">Place<br>of<br>supply<br>(Name of<br>State/<br>UT)</th>
      <th rowspan="2">Suppl<br>y<br>attract<br>ing<br>reverse<br>charge<br>(Y/N)</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>period]</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>filing<br>date]</th>
      <th rowspan="2">GST<br>R-3B<br>filing<br>status<br>(Yes/<br>No)</th>
      <th rowspan="2">Amend<br>ment<br>made,<br>if any<br>(GSTIN,<br>Others)</th>
      <th rowspan="2">Tax<br>perio<br>d in<br>which<br>amen<br>ded</th>
      <th rowspan="2">Effecti<br>ve<br>date of<br>cancell<br>ation,<br>if any</th>
    </tr>
    <tr>
      <th>N<br>o.</th><th>Ty<br>pe</th><th>Da<br>te</th><th>Val<br>ue</th>
      <th>Integr<br>ated<br>tax</th><th>Cen<br>tral<br>tax</th><th>Sta<br>te/<br>UT<br>tax</th><th>C<br>es<br>s</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td><td class="center">17</td><td class="center">18</td><td class="center">19</td><td class="center">20</td>
    </tr>
    {{#each table3_inward_registered}}
    <tr>
      <td>{{gstin_supplier}}</td><td>{{trade_legal_name}}</td><td>{{invoice_no}}</td><td>{{invoice_type}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{rate_percent}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td><td>{{reverse_charge}}</td><td>{{gstr_1_1a_5_period}}</td><td>{{gstr_1_1a_5_filing_date}}</td><td>{{gstr_3b_filing_status}}</td><td>{{amendment_made}}</td><td>{{tax_period_amended}}</td><td>{{effective_cancellation_date}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table3_inward_registered}}
  </table>

  <div class="section-title">4. Amendment to Inward supplies received from a registered person including supplies attracting reverse charge (Amendment to 3)</div>

  <table class="full-table">
    <colgroup>
      <col style="width:4%"><col style="width:4%"><col style="width:5%"><col style="width:5.5%"><col style="width:3.2%"><col style="width:3.2%"><col style="width:3.2%"><col style="width:4.2%"><col style="width:3.2%"><col style="width:4%"><col style="width:5%"><col style="width:4%"><col style="width:4%"><col style="width:4%"><col style="width:5%"><col style="width:5.5%"><col style="width:6%"><col style="width:6%"><col style="width:5.5%"><col style="width:6%"><col style="width:5%"><col style="width:5%">
    </colgroup>
    <tr>
      <th colspan="2">Details<br>of<br>original<br>Docume<br>nt</th>
      <th colspan="6">Revised<br>details</th>
      <th rowspan="2">Ra<br>te<br>(%)</th>
      <th rowspan="2">Tax<br>able<br>valu<br>e</th>
      <th colspan="4">Amount of<br>tax</th>
      <th rowspan="2">Place<br>of<br>supply<br>(Name of<br>State/<br>UT)</th>
      <th rowspan="2">Supp<br>ly<br>attracting<br>reverse<br>charge<br>(Y/N)</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>period]</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>filing<br>date]</th>
      <th rowspan="2">GST<br>R-3B<br>filing<br>status<br>(Yes/<br>No)</th>
      <th rowspan="2">Amendment<br>made<br>(GSTIN,<br>Others)</th>
      <th rowspan="2">Tax<br>period<br>of<br>original<br>record</th>
      <th rowspan="2">Effective<br>date of<br>cancellation<br>if any</th>
    </tr>
    <tr>
      <th>No.</th><th>Date</th><th>GSTIN</th><th>Trade /<br>Legal<br>name</th><th>N<br>o.</th><th>Ty<br>pe</th><th>Da<br>te</th><th>Val<br>ue</th><th>Integrated<br>tax</th><th>Central<br>tax</th><th>State/<br>UT<br>tax</th><th>Cess</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td><td class="center">17</td><td class="center">18</td><td class="center">19</td><td class="center">20</td><td class="center">21</td><td class="center">22</td>
    </tr>
    {{#each table4_amend_inward_registered}}
    <tr>
      <td>{{original_document_no}}</td><td>{{original_document_date}}</td><td>{{revised_gstin_supplier}}</td><td>{{revised_trade_legal_name}}</td><td>{{revised_invoice_no}}</td><td>{{revised_invoice_type}}</td><td>{{revised_invoice_date}}</td><td>{{revised_invoice_value}}</td><td>{{rate_percent}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td><td>{{reverse_charge}}</td><td>{{gstr_1_1a_5_period}}</td><td>{{gstr_1_1a_5_filing_date}}</td><td>{{gstr_3b_filing_status}}</td><td>{{amendment_made}}</td><td>{{tax_period_original_record}}</td><td>{{effective_cancellation_date}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table4_amend_inward_registered}}
  </table>
</div>
```

### Page 2

```html
<div class="page">
  <div class="section-title">5. Debit / Credit notes received during current tax period</div>

  <table class="full-table">
    <colgroup>
      <col style="width:5%"><col style="width:5.4%"><col style="width:4%"><col style="width:3.8%"><col style="width:4.6%"><col style="width:3.2%"><col style="width:4%"><col style="width:3%"><col style="width:4.2%"><col style="width:4%"><col style="width:3.8%"><col style="width:3.8%"><col style="width:3.8%"><col style="width:5%"><col style="width:4.5%"><col style="width:6.4%"><col style="width:6.4%"><col style="width:4.5%"><col style="width:5.5%"><col style="width:7%"><col style="width:6.1%">
    </colgroup>
    <tr>
      <th rowspan="2">GSTI<br>N of<br>suppl<br>ier</th>
      <th rowspan="2">Trade<br>/<br>Legal<br>name</th>
      <th colspan="5">Credit / Debit Note<br>Details</th>
      <th rowspan="2">Ra<br>te<br>(%)</th>
      <th rowspan="2">Tax<br>able<br>value</th>
      <th colspan="4">Amount of<br>tax</th>
      <th rowspan="2">Place<br>of<br>supply<br>(Name of<br>State/<br>UT)</th>
      <th rowspan="2">Supp<br>ly<br>attracting<br>reverse<br>charge<br>(Y/N)</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>perio<br>D]</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>filing<br>date]</th>
      <th rowspan="2">GST<br>R3B<br>filing<br>status<br>(Yes/<br>No)</th>
      <th rowspan="2">Ame<br>ndment<br>made,<br>if any<br>(GSTIN,<br>Others)</th>
      <th rowspan="2">Tax<br>period<br>in<br>which<br>amended</th>
      <th rowspan="2">Effecti<br>ve<br>date of<br>cancell<br>ation,<br>if any</th>
    </tr>
    <tr>
      <th>No.</th><th>No<br>te<br>typ<br>e</th><th>Note<br>supp<br>ly<br>type</th><th>Da<br>te</th><th>Val<br>ue</th>
      <th>Inte<br>grated<br>tax</th><th>Ce<br>ntr<br>al<br>tax</th><th>Stat<br>e/<br>UT<br>tax</th><th>Ce<br>ss</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td><td class="center">17</td><td class="center">18</td><td class="center">19</td><td class="center">20</td><td class="center">21</td>
    </tr>
    {{#each table5_debit_credit_notes}}
    <tr>
      <td>{{gstin_supplier}}</td><td>{{trade_legal_name}}</td><td>{{note_no}}</td><td>{{note_type}}</td><td>{{note_supply_type}}</td><td>{{note_date}}</td><td>{{note_value}}</td><td>{{rate_percent}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td><td>{{reverse_charge}}</td><td>{{gstr_1_1a_5_period}}</td><td>{{gstr_1_1a_5_filing_date}}</td><td>{{gstr_3b_filing_status}}</td><td>{{amendment_made}}</td><td>{{tax_period_amended}}</td><td>{{effective_cancellation_date}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table5_debit_credit_notes}}
  </table>

  <div class="section-title">6. Amendment to Debit / Credit notes (Amendment to 5)</div>

  <table class="full-table">
    <colgroup>
      <col style="width:2.8%"><col style="width:2.8%"><col style="width:3.1%"><col style="width:4.2%"><col style="width:5.6%"><col style="width:3.4%"><col style="width:3.7%"><col style="width:3.7%"><col style="width:3.4%"><col style="width:3.7%"><col style="width:2.9%"><col style="width:4%"><col style="width:4.6%"><col style="width:4.2%"><col style="width:4%"><col style="width:3.8%"><col style="width:4.8%"><col style="width:5%"><col style="width:6.5%"><col style="width:6.5%"><col style="width:5%"><col style="width:5.5%"><col style="width:4.4%"><col style="width:5.8%">
    </colgroup>
    <tr>
      <th colspan="3">Details<br>of<br>origina<br>l<br>docume<br>nt</th>
      <th colspan="7">Revised details</th>
      <th rowspan="2">R<br>at<br>e<br>(%)</th>
      <th rowspan="2">Tax<br>able<br>value</th>
      <th colspan="4">Amount of tax</th>
      <th rowspan="2">Pl<br>ac<br>e<br>of<br>supply<br>(Name<br>of State/<br>UT)</th>
      <th rowspan="2">Supp<br>ly<br>attracting<br>reverse<br>charge<br>(Y/N)</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>peri od]</th>
      <th rowspan="2"><sup>2</sup>[GSTR-<br>1/1A/5<br>filin g<br>date]</th>
      <th rowspan="2">GS<br>TR3B<br>filin<br>g stat<br>us<br>(Yes/<br>No)</th>
      <th rowspan="2">Amen<br>dment<br>made<br>(GSTIN,<br>Others)</th>
      <th rowspan="2">Tax<br>period<br>of<br>original<br>record</th>
      <th rowspan="2">Effecti<br>ve<br>date of<br>cancell<br>ation<br>if any</th>
    </tr>
    <tr>
      <th>Ty<br>pe</th><th>N<br>o.</th><th>D<br>at<br>e</th><th>GST<br>IN<br>of<br>Supplier</th><th>Tr<br>ad<br>e /<br>Le<br>ga<br>l<br>na<br>me</th><th>N<br>o.</th><th>N<br>ote<br>typ<br>e</th><th>Not<br>e<br>supp<br>ly<br>type</th><th>D<br>at<br>e</th><th>Va<br>lue</th><th>Integ<br>rated<br>tax</th><th>Cen<br>tral<br>tax</th><th>Sta<br>te/<br>UT<br>tax</th><th>Ce<br>ss</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td><td class="center">17</td><td class="center">18</td><td class="center">19</td><td class="center">20</td><td class="center">21</td><td class="center">22</td><td class="center">23</td><td class="center">24</td>
    </tr>
    {{#each table6_amend_debit_credit_notes}}
    <tr>
      <td>{{original_document_type}}</td><td>{{original_document_no}}</td><td>{{original_document_date}}</td><td>{{revised_gstin_supplier}}</td><td>{{revised_trade_legal_name}}</td><td>{{revised_note_no}}</td><td>{{revised_note_type}}</td><td>{{revised_note_supply_type}}</td><td>{{revised_note_date}}</td><td>{{revised_note_value}}</td><td>{{rate_percent}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td><td>{{reverse_charge}}</td><td>{{gstr_1_1a_5_period}}</td><td>{{gstr_1_1a_5_filing_date}}</td><td>{{gstr_3b_filing_status}}</td><td>{{amendment_made}}</td><td>{{tax_period_original_record}}</td><td>{{effective_cancellation_date}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table6_amend_debit_credit_notes}}
  </table>

  <div class="part-title">PART B</div>
  <div class="section-title">7. ISD credit received</div>

  <table class="full-table">
    <colgroup>
      <col style="width:8%"><col style="width:7%"><col style="width:5%"><col style="width:3%"><col style="width:4%"><col style="width:4.5%"><col style="width:5%"><col style="width:6.5%"><col style="width:6%"><col style="width:6.5%"><col style="width:8%"><col style="width:8.5%"><col style="width:7.5%"><col style="width:8%"><col style="width:7.5%"><col style="width:7.5%">
    </colgroup>
    <tr>
      <th rowspan="2">GSTIN<br>of ISD</th>
      <th rowspan="2">Trade/<br>Legal<br>name</th>
      <th colspan="3">ISD<br>docum<br>ent<br>details</th>
      <th colspan="2">ISD<br>invoice<br>details (for<br>ISD credit<br>note only)</th>
      <th colspan="4">ITC amount&nbsp;&nbsp; involved</th>
      <th rowspan="2">GSTR-6<br><br>Period</th>
      <th rowspan="2">GSTR-<br>6<br>filing<br>date</th>
      <th rowspan="2">Amend<br>ment<br>made,<br>if any</th>
      <th rowspan="2">Tax<br>Period<br>in which<br>amende<br>d</th>
      <th rowspan="2">ITC<br>Eligibi<br>lity</th>
    </tr>
    <tr>
      <th>Typ<br>e</th><th>N<br>o.</th><th>Dat<br>e</th><th>No.</th><th>Dat<br>e</th><th>Integ<br>rated<br>tax</th><th>Cen<br>tral<br>tax</th><th>State/<br>UT<br>tax</th><th>Cess</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td>
    </tr>
    {{#each table7_isd_credit_received}}
    <tr>
      <td>{{gstin_isd}}</td><td>{{trade_legal_name}}</td><td>{{isd_document_type}}</td><td>{{isd_document_no}}</td><td>{{isd_document_date}}</td><td>{{isd_invoice_no_for_credit_note}}</td><td>{{isd_invoice_date_for_credit_note}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{gstr_6_period}}</td><td>{{gstr_6_filing_date}}</td><td>{{amendment_made}}</td><td>{{tax_period_amended}}</td><td>{{itc_eligibility}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table7_isd_credit_received}}
  </table>

  <div class="section-title">8. Amendments to ISD credit details</div>

  <table class="full-table">
    <colgroup>
      <col style="width:4%"><col style="width:3%"><col style="width:4%"><col style="width:7%"><col style="width:7%"><col style="width:4%"><col style="width:3%"><col style="width:4%"><col style="width:4%"><col style="width:4%"><col style="width:7%"><col style="width:6.5%"><col style="width:6.5%"><col style="width:5.5%"><col style="width:6%"><col style="width:6%"><col style="width:9%"><col style="width:5.5%"><col style="width:7.5%">
    </colgroup>
    <tr>
      <th colspan="3">Original<br>document<br>details</th>
      <th colspan="2">Original<br>ISD details</th>
      <th colspan="3">Revised<br>document<br>details</th>
      <th colspan="2">Original ISD invoice<br>details<br>(for ISD credit note only)</th>
      <th colspan="4">ITC amount</th>
      <th rowspan="2">GSTR-6<br>Period</th>
      <th rowspan="2">GSTR-6<br>filing date</th>
      <th rowspan="2">Amendment<br>made, if any</th>
      <th rowspan="2">Tax<br>period of<br>original<br>record</th>
      <th rowspan="2">ITC<br>Eligibility</th>
    </tr>
    <tr>
      <th>Ty<br>pe</th><th>N<br>o.</th><th>Dat<br>e</th><th>GSTI<br>N of<br>ISD</th><th>Trad<br>e/<br>Legal<br>name</th><th>Ty<br>pe</th><th>N<br>o.</th><th>Dat<br>e</th><th>N<br>o.</th><th>Da<br>te</th><th>Integra<br>ted<br>Tax</th><th>Cent<br>ral<br>Tax</th><th>Stat<br>e/<br>UT<br>Tax</th><th>Ce<br>ss</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td><td class="center">17</td><td class="center">18</td><td class="center">19</td>
    </tr>
    {{#each table8_amend_isd_credit_details}}
    <tr>
      <td>{{original_document_type}}</td><td>{{original_document_no}}</td><td>{{original_document_date}}</td><td>{{original_gstin_isd}}</td><td>{{original_trade_legal_name}}</td><td>{{revised_document_type}}</td><td>{{revised_document_no}}</td><td>{{revised_document_date}}</td><td>{{original_isd_invoice_no_for_credit_note}}</td><td>{{original_isd_invoice_date_for_credit_note}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{gstr_6_period}}</td><td>{{gstr_6_filing_date}}</td><td>{{amendment_made}}</td><td>{{tax_period_original_record}}</td><td>{{itc_eligibility}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table8_amend_isd_credit_details}}
  </table>
</div>
```

### Page 3

```html
<div class="page">
  <div class="part-title">PART- C</div>
  <div class="section-title">9. TDS and TCS Credit (including amendments thereof) received</div>

  <table class="full-table">
    <colgroup>
      <col style="width:12%"><col style="width:13%"><col style="width:12%"><col style="width:12%"><col style="width:10%"><col style="width:9%"><col style="width:11%"><col style="width:8.5%"><col style="width:12.5%">
    </colgroup>
    <tr>
      <th rowspan="2">GSTIN of<br>Deductor /<br><br>GSTIN of<br>E-<br>Commerce<br><br>Operator</th>
      <th rowspan="2">Deductor<br>Name /<br>ECommerce<br>Operator<br>Name</th>
      <th rowspan="2">Tax<br>period of<br>GSTR-7 /<br>GSTR-8<br>(Original /<br><br>Amended)</th>
      <th rowspan="2">Amount<br>received /<br><br>Gross<br>value<br>(Original<br>/<br>Revised)</th>
      <th rowspan="2">Value of<br>supplies<br>returned</th>
      <th rowspan="2">Net<br>amount<br>liable<br>for<br>TCS</th>
      <th colspan="3">Amount (Original /<br>Revised)</th>
    </tr>
    <tr>
      <th>Integrated<br>tax</th><th>Central<br>tax</th><th>State<br>/UT&nbsp;&nbsp;tax</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td>
    </tr>
    <tr><td colspan="9" style="height: 10mm;">9A.</td></tr>
    <tr><td colspan="9" style="height: 10mm;">TDS</td></tr>
    {{#each table9A_tds_credit}}
    <tr>
      <td>{{gstin_deductor_or_ecommerce_operator}}</td><td>{{deductor_or_operator_name}}</td><td>{{tax_period_gstr_7_or_8}}</td><td>{{amount_received_gross_value}}</td><td>{{value_of_supplies_returned}}</td><td>{{net_amount_liable_for_tcs}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table9A_tds_credit}}
    <tr><td colspan="9" style="height: 7mm;">9B.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;TCS</td></tr>
    {{#each table9B_tcs_credit}}
    <tr>
      <td>{{gstin_deductor_or_ecommerce_operator}}</td><td>{{deductor_or_operator_name}}</td><td>{{tax_period_gstr_7_or_8}}</td><td>{{amount_received_gross_value}}</td><td>{{value_of_supplies_returned}}</td><td>{{net_amount_liable_for_tcs}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table9B_tcs_credit}}
  </table>

  <div class="part-title">PART- D</div>
  <div class="section-title">10.&nbsp;&nbsp;&nbsp; Import of goods from overseas on bill of entry (including amendments thereof)</div>

  <table class="full-table" style="width: 82%; margin-left: 18mm;">
    <colgroup>
      <col style="width:20%"><col style="width:9%"><col style="width:7%"><col style="width:8%"><col style="width:9%"><col style="width:17%"><col style="width:12%"><col style="width:18%">
    </colgroup>
    <tr>
      <th rowspan="2">ICEGATE<br>Reference date</th>
      <th colspan="4">Bill of entry details</th>
      <th colspan="2">Amount of tax</th>
      <th rowspan="2">Amended (Yes/ No)</th>
    </tr>
    <tr>
      <th>Port<br>code</th><th>No.</th><th>Date</th><th>Value</th><th>Integrated tax</th><th>Cess</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td>
    </tr>
    {{#each table10_import_goods_overseas}}
    <tr>
      <td>{{icegate_reference_date}}</td><td>{{port_code}}</td><td>{{bill_entry_no}}</td><td>{{bill_entry_date}}</td><td>{{bill_entry_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td><td>{{amended_yes_no}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table10_import_goods_overseas}}
  </table>

  <div class="section-title">11.Inward supplies of goods received from SEZ units / developers on bill of entry (including amendments thereof)</div>

  <table class="full-table" style="width: 92%; margin-left: 10mm;">
    <colgroup>
      <col style="width:11%"><col style="width:10%"><col style="width:13%"><col style="width:9%"><col style="width:8%"><col style="width:8%"><col style="width:10%"><col style="width:13%"><col style="width:13%"><col style="width:15%">
    </colgroup>
    <tr>
      <th rowspan="2">GSTIN<br>of the<br>Supplier<br><br>(SEZ)</th>
      <th rowspan="2">Trade /<br>Legal<br>name</th>
      <th rowspan="2">ICEGATE<br>Reference<br>date</th>
      <th colspan="4">Bill of Entry details</th>
      <th colspan="2">Amount of tax</th>
      <th rowspan="2">Amended&nbsp;&nbsp; (Yes/<br>No)</th>
    </tr>
    <tr>
      <th>Port<br>code</th><th>No.</th><th>Date</th><th>Value</th><th>Integrated<br>tax</th><th>Cess</th>
    </tr>
    <tr>
      <td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td>
    </tr>
    {{#each table11_sez_import_goods}}
    <tr>
      <td>{{gstin_supplier_sez}}</td><td>{{trade_legal_name}}</td><td>{{icegate_reference_date}}</td><td>{{port_code}}</td><td>{{bill_entry_no}}</td><td>{{bill_entry_date}}</td><td>{{bill_entry_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td><td>{{amended_yes_no}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table11_sez_import_goods}}
  </table>

  <div class="instructions">
    <p class="bold">Instructions:</p>
    <p>1.&nbsp;&nbsp;&nbsp;&nbsp; Terms Used :-</p>
    <p class="indent">a.&nbsp;&nbsp;&nbsp; ITC – Input tax credit</p>
    <p class="indent">b.&nbsp;&nbsp;&nbsp; ISD – Input Service Distributor</p>
  </div>
</div>
```

---

## 6. Variable-Entry Handling Rules

1. Every table section with `{{#each ...}}` is dynamic.
2. Do **not** restrict the number of entries to the number of blank rows visible in the original PDF.
3. For more entries:
   - Add rows with identical borders and column widths.
   - Continue naturally to the next page.
   - Repeat the table header on the new page.
   - Keep the statutory section title with the first part of that table.
4. For zero entries:
   - Keep one bordered blank row below that table or sub-section.
5. Long text must wrap inside cells. Do not expand page width.
6. Amount columns must be right-aligned if numeric data is inserted.
7. GSTIN, invoice number, bill of entry number and document serial numbers may be left-aligned unless the original cell is centered.
8. Preserve original spelling, spacing and punctuation where shown, including phrases such as `PART- C`, `PART- D`, `GSTR1, 1A`, `ECommerce`, `Tax Period`, and `11.Inward` if exact statutory reproduction is required.
9. Do not modernize the wording unless specifically instructed.
10. The uploaded PDF shows only the visible instruction terms at the end of page 3. Do not add additional instruction text unless separately supplied.

---

## 7. Final AI Instruction Block

Copy this instruction into the AI that will generate the final document:

```text
Recreate FORM GSTR-2A exactly as per the provided Markdown/HTML specification. Use A4 portrait, Times New Roman, black borders, compact statutory-form layout, and the same section order from pages 1 to 3. Treat all entry tables as dynamic arrays. If a table has more rows than the original blank space, continue it onto the next page while repeating the relevant table header. If a table has no entries, show one blank bordered row. Preserve the original text, numbering, part labels, table headers, superscript markers, visible instruction text, borders, narrow cells and statutory layout. Do not redesign, simplify, colour, modernize or add new content to the form.
```
