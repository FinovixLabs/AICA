# FORM GSTR-3 - Exact Recreation Markdown Specification

Use this file as the master prompt/specification for recreating the uploaded **FORM GSTR-3** document in the same statutory format. The number of data entries in rate-wise sections is variable; therefore every entry section below must be generated from arrays/lists and must expand or continue onto the next page as required.

> **Important:** Native Markdown tables cannot reproduce this form exactly because the source document uses merged cells, nested headers, fixed borders, compact amount columns, digit boxes, continuation tables, and page-specific spacing. Recreate the document using **HTML/CSS inside Markdown** or convert the HTML to PDF/DOCX. Preserve the visual appearance of the original form.

---

## 1. Output Rules

### Page setup

- Paper size: **A4 portrait**.
- Margins: approximately **18 mm left/right**, **16-20 mm top**, **14-18 mm bottom**.
- Font family: **Times New Roman** for headings, tables, and body text.
- Use black text and black table borders only.
- Do **not** add logos, colours, watermarks, decorative headers, or modern styling.
- The source form does **not** show running page numbers at the bottom; do not add page numbers unless explicitly required by the consuming AI tool.
- Keep the form compact. Avoid extra spacing except where the source has visible vertical gaps.
- Use narrow cells where the source uses digit boxes or compact tax columns.

### Typography

| Element | Style |
|---|---|
| Omission note | Left aligned, bold, approx. 10-11 pt |
| `***OMITTED ***` line | Centered, bold, approx. 11-12 pt |
| Main title | Centered, bold, approx. 12-13 pt |
| Rule reference | Centered, italic, approx. 11 pt |
| Form subtitle | Centered, bold, approx. 12 pt |
| Section headings | Bold, approx. 10.5-11 pt |
| Table text | Approx. 8.5-10 pt depending on width |
| Instruction text | Approx. 11 pt, left aligned |
| Footnote | Approx. 8.5-9 pt |

### Table style

- All tables must use `border-collapse: collapse`.
- Table borders: `1px solid #000`.
- Header cells: centered vertically and horizontally unless the source text is left-aligned.
- Section separator rows such as `A.`, `(I)`, `8A.`, etc. must span the full table width and be left-aligned.
- Blank entry rows must remain bordered.
- For variable entries, repeat one row per data item.
- If a section has no entries, keep at least **one blank entry row** so the form structure remains visible.
- If a variable table spills to a new page, repeat the relevant table header on the continuation page.
- Preserve source spellings and legacy formatting, including `State /UT`, `State/UT`, `though`, `Taxable [other than zero rated]`, and bracketed footnote markers.

---

## 2. Placeholder Convention

Use placeholders in double curly braces.

Example:

```handlebars
{{gstin}}
{{legal_name}}
{{trade_name}}
{{year_digit_boxes}}
{{month}}
{{#each table4_1_A}}
  {{this.rate}}
{{/each}}
```

For digit boxes, print one character per cell. If empty, leave the cell blank.

---

## 3. Required Data Schema

The AI/document generator must accept data in this structure. Arrays may contain any number of entries.

```json
{
  "year": "",
  "month": "",
  "gstin": "",
  "legal_name": "Auto Populated",
  "trade_name": "Auto Populated",

  "turnover": {
    "taxable_other_than_zero_rated": "",
    "zero_rated_with_tax": "",
    "zero_rated_without_tax": "",
    "deemed_exports": "",
    "exempted": "",
    "nil_rated": "",
    "non_gst_supply": "",
    "total": ""
  },

  "table4_1_A": [],
  "table4_1_B": [],
  "table4_1_C": [],
  "table4_1_D": [],

  "table4_2_A": [],
  "table4_2_B": [],
  "table4_2_C": [],

  "table4_3_inter_A": [],
  "table4_3_inter_B": [],
  "table4_3_inter_C": [],
  "table4_3_intra_A": [],
  "table4_3_intra_B": [],

  "table5A_inter": [],
  "table5A_intra": [],
  "table5B_inter": [],
  "table5B_intra": [],

  "input_tax_credit": {
    "current_inputs": {},
    "current_input_services": {},
    "current_capital_goods": {},
    "amended_inputs": {},
    "amended_input_services": {},
    "amended_capital_goods": {}
  },

  "table7": {
    "a": {}, "b": {}, "c": {}, "d": {}, "e": {}, "f": {}, "g": {}
  },

  "table8_total_tax_liability": {
    "outward_supplies": [],
    "reverse_charge_inward_supplies": [],
    "itc_reversal_reclaim": [],
    "mismatch_rectification_other_reasons": []
  },

  "table9_credit_tds_tcs": {
    "tds": {},
    "tcs": {}
  },

  "table10_interest_liability": {
    "interest_as_on": "",
    "integrated_tax": {},
    "central_tax": {},
    "state_ut_tax": {},
    "cess": {}
  },

  "table11_late_fee": {
    "central_tax": "",
    "state_ut_tax": ""
  },

  "table12_tax_payable_paid": {
    "integrated_tax": {},
    "central_tax": {},
    "state_ut_tax": {},
    "cess": {}
  },

  "table13_interest_late_fee_other": {
    "interest_integrated_tax": {},
    "interest_central_tax": {},
    "interest_state_ut_tax": {},
    "interest_cess": {},
    "late_fee_central_tax": {},
    "late_fee_state_ut_tax": {}
  },

  "table14_refund_cash_ledger": {
    "integrated_tax": {},
    "central_tax": {},
    "state_ut_tax": {},
    "cess": {},
    "bank_account_details": ""
  },

  "table15_debit_entries": {
    "integrated_tax": {},
    "central_tax": {},
    "state_ut_tax": {},
    "cess": {}
  },

  "verification": {
    "place": "",
    "date": "",
    "authorised_signatory_name": "",
    "designation_status": ""
  }
}
```

### Common row object formats

```json
{
  "rate": "",
  "taxable_value": "",
  "net_differential_value": "",
  "differential_taxable_value": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "operator_gstin": ""
}
```

For `input_tax_credit` row objects:

```json
{
  "taxable_value": "",
  "tax_amount_integrated_tax": "",
  "tax_amount_central_tax": "",
  "tax_amount_state_ut_tax": "",
  "tax_amount_cess": "",
  "itc_integrated_tax": "",
  "itc_central_tax": "",
  "itc_state_ut_tax": "",
  "itc_cess": ""
}
```

For `table10_interest_liability` row objects:

```json
{
  "output_liability_on_mismatch": "",
  "itc_claimed_on_mismatched_invoice": "",
  "other_itc_reversal": "",
  "undue_excess_claims_or_reduction": "",
  "credit_of_interest_on_rectification": "",
  "interest_liability_carry_forward": "",
  "delay_in_payment_of_tax": "",
  "total_interest_liability": ""
}
```

For `table12_tax_payable_paid` and `table15_debit_entries` row objects:

```json
{
  "tax_payable": "",
  "paid_in_cash": "",
  "paid_through_itc_integrated_tax": "",
  "paid_through_itc_central_tax": "",
  "paid_through_itc_state_ut_tax": "",
  "paid_through_itc_cess": "",
  "tax_paid": "",
  "interest": "",
  "late_fee": ""
}
```

---

## 4. CSS to Use

Embed this CSS in the generated HTML/PDF. Adjust only if required to fit the page, but do not alter the visual identity.

```html
<style>
  @page {
    size: A4 portrait;
    margin: 17mm 18mm 16mm 18mm;
  }

  body {
    font-family: "Times New Roman", Times, serif;
    color: #000;
    font-size: 10pt;
    line-height: 1.18;
  }

  .page {
    page-break-after: always;
    position: relative;
  }

  .note {
    font-weight: bold;
    font-size: 10.5pt;
    margin-top: 5mm;
    margin-bottom: 12mm;
  }

  .omitted {
    text-align: center;
    font-weight: bold;
    font-size: 11.5pt;
    margin: 8mm 0 10mm 0;
  }

  .title {
    text-align: center;
    font-weight: bold;
    font-size: 12.5pt;
    margin-top: 0;
    margin-bottom: 1.5mm;
  }

  .rule {
    text-align: center;
    font-style: italic;
    font-size: 11pt;
    margin: 0 0 7mm 0;
  }

  .subtitle {
    text-align: center;
    font-weight: bold;
    font-size: 12pt;
    margin: 0 0 2mm 0;
  }

  .part-title {
    text-align: center;
    font-weight: bold;
    text-decoration: underline;
    font-size: 11pt;
    margin: 7mm 0 7mm 0;
  }

  .section-title {
    font-weight: bold;
    font-size: 10.7pt;
    margin: 6.5mm 0 3mm 0;
  }

  .subsection-title {
    font-weight: bold;
    font-size: 10.4pt;
    margin: 5mm 0 2mm 0;
  }

  .amount-note {
    text-align: center;
    font-size: 10pt;
    margin: 0 0 2mm 0;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    table-layout: fixed;
    margin: 0;
  }

  th, td {
    border: 1px solid #000;
    padding: 1.1mm 1.2mm;
    vertical-align: top;
    font-size: 9pt;
    font-weight: normal;
  }

  th {
    text-align: center;
    vertical-align: middle;
  }

  .center { text-align: center; }
  .right { text-align: right; }
  .left { text-align: left; }
  .bold { font-weight: bold; }
  .italic { font-style: italic; }
  .underline { text-decoration: underline; }
  .small { font-size: 8pt; }
  .tiny { font-size: 7.4pt; }
  .no-border { border: none !important; }
  .nowrap { white-space: nowrap; }

  .section-row td,
  td.section-row {
    text-align: left;
    font-weight: normal;
  }

  .blank-row td { height: 6mm; }
  .tall-row td { height: 9mm; }
  .short-row td { height: 4.5mm; }

  .digit-table {
    width: auto;
    table-layout: fixed;
    border-collapse: collapse;
  }

  .digit-table td {
    width: 4.8mm;
    height: 4.8mm;
    text-align: center;
    vertical-align: middle;
    padding: 0;
  }

  .amount-boxes td {
    width: 4.1mm;
    height: 5.4mm;
    padding: 0;
  }

  .top-right-box {
    float: right;
    width: 38mm;
    margin-top: 1mm;
    margin-bottom: 8mm;
  }

  .initial-table {
    clear: both;
  }

  .compact th,
  .compact td {
    padding: 0.8mm 0.9mm;
    font-size: 8.6pt;
  }

  .very-compact th,
  .very-compact td {
    padding: 0.55mm 0.65mm;
    font-size: 8.1pt;
  }

  .instructions {
    font-size: 11pt;
    line-height: 1.28;
  }

  .instructions p {
    margin: 4.5mm 0;
  }

  .indent { margin-left: 10mm; }
  .indent2 { margin-left: 18mm; }

  .verification {
    font-size: 11pt;
    line-height: 1.25;
    margin-top: 18mm;
  }

  .signature-grid {
    width: 100%;
    border-collapse: collapse;
    margin-top: 14mm;
  }

  .signature-grid td {
    border: none;
    font-size: 11pt;
    padding: 2mm 0;
  }

  .footnote-line {
    width: 48mm;
    border-top: 1px solid #000;
    margin-top: 22mm;
    margin-bottom: 1.5mm;
  }
</style>
```

---

## 5. Document Template

### Page 1

```html
<div class="page">
  <div class="note">NOTE: This Form shall be deemed to have been omitted with effect from the 1st day of October,<br>2022 vide Notification No. 19/2022-CT dated 28.09.2022.</div>

  <div class="omitted">***OMITTED ***</div>

  <div class="title"><sup>1</sup>[FORM GSTR-3</div>
  <div class="rule">[See rule 61(1)]</div>
  <div class="subtitle">Monthly return</div>

  <table class="top-right-box compact">
    <tr>
      <td class="left" style="width:45%">Year</td>
      <td>{{year_1}}</td><td>{{year_2}}</td><td>{{year_3}}</td><td>{{year_4}}</td>
    </tr>
    <tr>
      <td class="left">Month</td>
      <td colspan="4">{{month}}</td>
    </tr>
  </table>

  <table class="initial-table compact">
    <colgroup>
      <col style="width: 5%"><col style="width: 5%"><col style="width: 48%"><col style="width: 42%">
    </colgroup>
    <tr>
      <td class="center">1.</td>
      <td colspan="2">GSTIN</td>
      <td>{{gstin_digit_boxes}}</td>
    </tr>
    <tr>
      <td class="center">2.</td>
      <td class="center">(a)</td>
      <td>Legal name of the registered person</td>
      <td>Auto Populated</td>
    </tr>
    <tr>
      <td></td>
      <td class="center">(b)</td>
      <td>Trade name, if any</td>
      <td>Auto Populated</td>
    </tr>
  </table>

  <div class="part-title">Part-A (To be auto populated)</div>
  <div class="amount-note">(Amount in Rs. for all Tables)</div>

  <table class="compact">
    <colgroup>
      <col style="width: 8%"><col style="width: 45%"><col style="width: 47%">
    </colgroup>
    <tr><td colspan="3" class="bold">3. &nbsp;&nbsp; Turnover</td></tr>
    <tr>
      <th>Sr.<br>No.</th>
      <th>Type of Turnover</th>
      <th>Amount</th>
    </tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td></tr>
    <tr><td class="center">(i)</td><td>Taxable&nbsp; [other than zero rated]</td><td>{{turnover.taxable_other_than_zero_rated_digit_boxes}}</td></tr>
    <tr><td class="center">(ii)</td><td>Zero rated supply on payment of Tax</td><td>{{turnover.zero_rated_with_tax_digit_boxes}}</td></tr>
    <tr><td class="center">(iii)</td><td>Zero rated supply without payment of<br>Tax</td><td>{{turnover.zero_rated_without_tax_digit_boxes}}</td></tr>
    <tr><td class="center">(iv)</td><td>Deemed exports</td><td>{{turnover.deemed_exports_digit_boxes}}</td></tr>
    <tr><td class="center">(v)</td><td>Exempted</td><td>{{turnover.exempted_digit_boxes}}</td></tr>
    <tr><td class="center">(vi)</td><td>Nil Rated</td><td>{{turnover.nil_rated_digit_boxes}}</td></tr>
    <tr><td class="center">(vii)</td><td>Non-GST supply</td><td>{{turnover.non_gst_supply_digit_boxes}}</td></tr>
    <tr><td></td><td>Total</td><td>{{turnover.total_digit_boxes}}</td></tr>
  </table>

  <div class="section-title">4. Outward supplies</div>
  <div class="subsection-title" style="margin-left:10mm;">4.1 Inter-State supplies (Net Supply for the month)</div>

  <table class="compact">
    <colgroup>
      <col style="width: 9%"><col style="width: 42%"><col style="width: 20%"><col style="width: 29%">
    </colgroup>
    <tr>
      <th rowspan="2">Rate</th>
      <th rowspan="2">Taxable Value</th>
      <th colspan="2">Amount of Tax</th>
    </tr>
    <tr><th>Integrated Tax</th><th>CESS</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td></tr>
  </table>
</div>
```

---

### Page 2

```html
<div class="page">
  <table class="compact">
    <colgroup>
      <col style="width: 9%"><col style="width: 42%"><col style="width: 20%"><col style="width: 29%">
    </colgroup>
    <tr><td colspan="4">A. &nbsp; Taxable supplies (other than reverse charge and zero rated supply) [Tax Rate Wise]</td></tr>
    {{#each table4_1_A}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_1_A}}

    <tr><td colspan="4">B. &nbsp; Supplies attracting reverse charge-Tax payable by recipient of supply</td></tr>
    {{#each table4_1_B}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_1_B}}

    <tr><td colspan="4">C. &nbsp; Zero rated supply made with payment of Integrated Tax</td></tr>
    {{#each table4_1_C}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_1_C}}

    <tr><td colspan="4">D. &nbsp; Out of the supplies mentioned at A, the value of supplies made though an e-commerce<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;operator attracting TCS-[Rate wise]</td></tr>
    <tr><td colspan="2">GSTIN of e-commerce operator</td><td colspan="2"></td></tr>
    {{#each table4_1_D}}
    <tr><td>{{rate}}</td><td>{{operator_gstin}} / {{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_1_D}}
  </table>

  <div class="subsection-title">4.2&nbsp;&nbsp; Intra-State supplies (Net supply for the month)</div>

  <table class="compact">
    <colgroup>
      <col style="width: 10%"><col style="width: 38%"><col style="width: 16%"><col style="width: 20%"><col style="width: 16%">
    </colgroup>
    <tr>
      <th rowspan="2">Rate</th>
      <th rowspan="2">Taxable Value</th>
      <th colspan="3">Amount of Tax</th>
    </tr>
    <tr><th>Central Tax</th><th>State /UT Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td></tr>

    <tr><td colspan="5">A. &nbsp; Taxable supplies (other than reverse charge) [Tax Rate wise]</td></tr>
    {{#each table4_2_A}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_2_A}}

    <tr><td colspan="5">B. &nbsp; Supplies attracting reverse charge- Tax payable by the recipient of supply</td></tr>
    {{#each table4_2_B}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_2_B}}

    <tr><td colspan="5">C. &nbsp; Out of the supplies mentioned at A, the value of supplies made though an e-commerce<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;operator attracting TCS [Rate wise]</td></tr>
    <tr><td colspan="2">GSTIN of e-commerce operator</td><td colspan="3"></td></tr>
    {{#each table4_2_C}}
    <tr><td>{{rate}}</td><td>{{operator_gstin}} / {{taxable_value}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_2_C}}
  </table>

  <div class="subsection-title">4.3 Tax effect of amendments made in respect of outward supplies</div>

  <table class="compact">
    <colgroup>
      <col style="width: 10%"><col style="width: 34%"><col style="width: 13%"><col style="width: 12%"><col style="width: 18%"><col style="width: 13%">
    </colgroup>
    <tr>
      <th rowspan="2">Rate</th>
      <th rowspan="2">Net differential value</th>
      <th colspan="4">Amount of Tax</th>
    </tr>
    <tr><th>Integrated<br>tax</th><th>Central<br>Tax</th><th>State/UT&nbsp; Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>

    <tr><td colspan="6">(I)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Inter-State supplies</td></tr>
    <tr><td colspan="6">A&nbsp;&nbsp;&nbsp;&nbsp; Taxable supplies (other than reverse charge and Zero Rated supply made with payment of<br>Integrated Tax) [Rate wise]</td></tr>
    {{#each table4_3_inter_A}}
    <tr><td>{{rate}}</td><td>{{net_differential_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_3_inter_A}}

    <tr><td colspan="6">B&nbsp;&nbsp;&nbsp;&nbsp; Zero rated supply made with payment of Integrated Tax [Rate wise]</td></tr>
    {{#each table4_3_inter_B}}
    <tr><td>{{rate}}</td><td>{{net_differential_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_3_inter_B}}

    <tr><td colspan="6">C&nbsp;&nbsp;&nbsp;&nbsp; Out of the Supplies mentioned at A, the value of supplies made though an e-commerce<br>operator attracting TCS</td></tr>
    {{#each table4_3_inter_C}}
    <tr><td>{{rate}}</td><td>{{operator_gstin}} / {{net_differential_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_3_inter_C}}
  </table>
</div>
```

---

### Page 3

```html
<div class="page">
  <table class="compact">
    <colgroup>
      <col style="width: 10%"><col style="width: 34%"><col style="width: 13%"><col style="width: 12%"><col style="width: 18%"><col style="width: 13%">
    </colgroup>
    <tr><td colspan="6">(II)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Intra-state supplies</td></tr>
    <tr><td colspan="6">A&nbsp;&nbsp;&nbsp;&nbsp; Taxable supplies (other than reverse charge) [Rate wise]</td></tr>
    {{#each table4_3_intra_A}}
    <tr><td>{{rate}}</td><td>{{net_differential_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_3_intra_A}}

    <tr><td colspan="6">B&nbsp;&nbsp;&nbsp; Out of the supplies mentioned at A, the value of supplies made though an e-commerce<br>operator attracting TCS</td></tr>
    {{#each table4_3_intra_B}}
    <tr><td>{{rate}}</td><td>{{operator_gstin}} / {{net_differential_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table4_3_intra_B}}
  </table>

  <div class="section-title">5. Inward supplies attracting reverse charge including import of services (Net of advance<br>adjustments)</div>
  <div class="subsection-title">5A. Inward supplies on which tax is payable on reverse charge basis</div>

  <table class="compact">
    <colgroup>
      <col style="width: 13%"><col style="width: 16%"><col style="width: 18%"><col style="width: 20%"><col style="width: 19%"><col style="width: 14%">
    </colgroup>
    <tr>
      <th rowspan="2">Rate of<br>tax</th>
      <th rowspan="2">Taxable<br>Value</th>
      <th colspan="4">Amount of tax</th>
    </tr>
    <tr><th>Integrated Tax</th><th>Central Tax</th><th>State/UT tax</th><th>CESS</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>

    <tr><td colspan="6">(I)&nbsp;&nbsp;&nbsp;&nbsp; Inter-State inward supplies [Rate Wise]</td></tr>
    {{#each table5A_inter}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table5A_inter}}

    <tr><td colspan="6">(II)&nbsp;&nbsp; Intra-State inward supplies&nbsp; [Rate Wise]</td></tr>
    {{#each table5A_intra}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table5A_intra}}
  </table>

  <div class="subsection-title">5B. Tax effect of amendments in respect of supplies attracting reverse charge</div>

  <table class="compact">
    <colgroup>
      <col style="width: 13%"><col style="width: 16%"><col style="width: 18%"><col style="width: 20%"><col style="width: 19%"><col style="width: 14%">
    </colgroup>
    <tr>
      <th rowspan="2">Rate of<br>tax</th>
      <th rowspan="2">Differential<br>Taxable<br>Value</th>
      <th colspan="4">Amount of tax</th>
    </tr>
    <tr><th>Integrated Tax</th><th>Central Tax</th><th>State/UT Tax</th><th>CESS</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>

    <tr><td colspan="6">(I)&nbsp;&nbsp;&nbsp;&nbsp; Inter-State inward supplies (Rate Wise)</td></tr>
    {{#each table5B_inter}}
    <tr><td>{{rate}}</td><td>{{differential_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table5B_inter}}

    <tr><td colspan="6">(II)&nbsp;&nbsp; Intra-State inward supplies (Rate Wise)</td></tr>
    {{#each table5B_intra}}
    <tr><td>{{rate}}</td><td>{{differential_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table5B_intra}}
  </table>

  <div class="section-title">6.&nbsp;&nbsp; Input tax credit</div>
  <div class="subsection-title" style="margin-left:10mm;">ITC on inward taxable supplies, including imports and ITC received from ISD<span class="italic small">[Net<br>of debit notes/credit notes]</span></div>

  <table class="very-compact">
    <colgroup>
      <col style="width: 20%"><col style="width: 10%"><col style="width: 12%"><col style="width: 9%"><col style="width: 8%"><col style="width: 8%"><col style="width: 12%"><col style="width: 9%"><col style="width: 8%"><col style="width: 8%">
    </colgroup>
    <tr>
      <th rowspan="2">Description</th>
      <th rowspan="2">Taxable<br>value</th>
      <th colspan="4">Amount of tax</th>
      <th colspan="4">Amount of ITC</th>
    </tr>
    <tr>
      <th>Integrated<br>Tax</th><th>Central<br>Tax</th><th>State/<br>UT<br>Tax</th><th>CESS</th>
      <th>Integrated<br>Tax</th><th>Central<br>Tax</th><th>State/<br>UT<br>Tax</th><th>CESS</th>
    </tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td></tr>
    <tr><td colspan="10">(I)&nbsp;&nbsp; On account of supplies received and debit notes/credit notes received during the current tax period</td></tr>
    <tr><td>(a)&nbsp;&nbsp; Inputs</td><td>{{input_tax_credit.current_inputs.taxable_value}}</td><td>{{input_tax_credit.current_inputs.tax_amount_integrated_tax}}</td><td>{{input_tax_credit.current_inputs.tax_amount_central_tax}}</td><td>{{input_tax_credit.current_inputs.tax_amount_state_ut_tax}}</td><td>{{input_tax_credit.current_inputs.tax_amount_cess}}</td><td>{{input_tax_credit.current_inputs.itc_integrated_tax}}</td><td>{{input_tax_credit.current_inputs.itc_central_tax}}</td><td>{{input_tax_credit.current_inputs.itc_state_ut_tax}}</td><td>{{input_tax_credit.current_inputs.itc_cess}}</td></tr>
  </table>
</div>
```

---

### Page 4

```html
<div class="page">
  <table class="very-compact">
    <colgroup>
      <col style="width: 20%"><col style="width: 10%"><col style="width: 12%"><col style="width: 9%"><col style="width: 8%"><col style="width: 8%"><col style="width: 12%"><col style="width: 9%"><col style="width: 8%"><col style="width: 8%">
    </colgroup>
    <tr><td>(b)&nbsp;&nbsp; Input services</td><td>{{input_tax_credit.current_input_services.taxable_value}}</td><td>{{input_tax_credit.current_input_services.tax_amount_integrated_tax}}</td><td>{{input_tax_credit.current_input_services.tax_amount_central_tax}}</td><td>{{input_tax_credit.current_input_services.tax_amount_state_ut_tax}}</td><td>{{input_tax_credit.current_input_services.tax_amount_cess}}</td><td>{{input_tax_credit.current_input_services.itc_integrated_tax}}</td><td>{{input_tax_credit.current_input_services.itc_central_tax}}</td><td>{{input_tax_credit.current_input_services.itc_state_ut_tax}}</td><td>{{input_tax_credit.current_input_services.itc_cess}}</td></tr>
    <tr><td>(c)&nbsp;&nbsp; Capital goods</td><td>{{input_tax_credit.current_capital_goods.taxable_value}}</td><td>{{input_tax_credit.current_capital_goods.tax_amount_integrated_tax}}</td><td>{{input_tax_credit.current_capital_goods.tax_amount_central_tax}}</td><td>{{input_tax_credit.current_capital_goods.tax_amount_state_ut_tax}}</td><td>{{input_tax_credit.current_capital_goods.tax_amount_cess}}</td><td>{{input_tax_credit.current_capital_goods.itc_integrated_tax}}</td><td>{{input_tax_credit.current_capital_goods.itc_central_tax}}</td><td>{{input_tax_credit.current_capital_goods.itc_state_ut_tax}}</td><td>{{input_tax_credit.current_capital_goods.itc_cess}}</td></tr>
    <tr><td colspan="10">(II) On account of amendments made (of the details furnished in earlier tax periods)</td></tr>
    <tr><td>(a)&nbsp;&nbsp; Inputs</td><td>{{input_tax_credit.amended_inputs.taxable_value}}</td><td>{{input_tax_credit.amended_inputs.tax_amount_integrated_tax}}</td><td>{{input_tax_credit.amended_inputs.tax_amount_central_tax}}</td><td>{{input_tax_credit.amended_inputs.tax_amount_state_ut_tax}}</td><td>{{input_tax_credit.amended_inputs.tax_amount_cess}}</td><td>{{input_tax_credit.amended_inputs.itc_integrated_tax}}</td><td>{{input_tax_credit.amended_inputs.itc_central_tax}}</td><td>{{input_tax_credit.amended_inputs.itc_state_ut_tax}}</td><td>{{input_tax_credit.amended_inputs.itc_cess}}</td></tr>
    <tr><td>(b)&nbsp;&nbsp; Input services</td><td>{{input_tax_credit.amended_input_services.taxable_value}}</td><td>{{input_tax_credit.amended_input_services.tax_amount_integrated_tax}}</td><td>{{input_tax_credit.amended_input_services.tax_amount_central_tax}}</td><td>{{input_tax_credit.amended_input_services.tax_amount_state_ut_tax}}</td><td>{{input_tax_credit.amended_input_services.tax_amount_cess}}</td><td>{{input_tax_credit.amended_input_services.itc_integrated_tax}}</td><td>{{input_tax_credit.amended_input_services.itc_central_tax}}</td><td>{{input_tax_credit.amended_input_services.itc_state_ut_tax}}</td><td>{{input_tax_credit.amended_input_services.itc_cess}}</td></tr>
    <tr><td>(c)&nbsp;&nbsp; Capital goods</td><td>{{input_tax_credit.amended_capital_goods.taxable_value}}</td><td>{{input_tax_credit.amended_capital_goods.tax_amount_integrated_tax}}</td><td>{{input_tax_credit.amended_capital_goods.tax_amount_central_tax}}</td><td>{{input_tax_credit.amended_capital_goods.tax_amount_state_ut_tax}}</td><td>{{input_tax_credit.amended_capital_goods.tax_amount_cess}}</td><td>{{input_tax_credit.amended_capital_goods.itc_integrated_tax}}</td><td>{{input_tax_credit.amended_capital_goods.itc_central_tax}}</td><td>{{input_tax_credit.amended_capital_goods.itc_state_ut_tax}}</td><td>{{input_tax_credit.amended_capital_goods.itc_cess}}</td></tr>
  </table>

  <div class="section-title">7. &nbsp; Addition and reduction of amount in output tax for mismatch and other reasons</div>

  <table class="compact">
    <colgroup>
      <col style="width: 5%"><col style="width: 43%"><col style="width: 15%"><col style="width: 12%"><col style="width: 10%"><col style="width: 7%"><col style="width: 8%">
    </colgroup>
    <tr>
      <th colspan="2" rowspan="2">Description</th>
      <th rowspan="2">Add to or<br>reduce from<br>output<br>liability</th>
      <th colspan="4">Amount</th>
    </tr>
    <tr><th>Integrated<br>tax</th><th>Central<br>tax</th><th>State<br>/ UT<br>tax</th><th>CESS</th></tr>
    <tr><td colspan="2" class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>
    <tr><td class="center">(a)</td><td>ITC claimed on mismatched/duplication<br>of invoices/debit notes</td><td class="center">Add</td><td>{{table7.a.integrated_tax}}</td><td>{{table7.a.central_tax}}</td><td>{{table7.a.state_ut_tax}}</td><td>{{table7.a.cess}}</td></tr>
    <tr><td class="center">(b)</td><td>Tax liability on mismatched&nbsp; credit notes</td><td class="center">Add</td><td>{{table7.b.integrated_tax}}</td><td>{{table7.b.central_tax}}</td><td>{{table7.b.state_ut_tax}}</td><td>{{table7.b.cess}}</td></tr>
    <tr><td class="center">(c)</td><td>Reclaim on rectification of mismatched<br>invoices/Debit Notes</td><td class="center">Reduce</td><td>{{table7.c.integrated_tax}}</td><td>{{table7.c.central_tax}}</td><td>{{table7.c.state_ut_tax}}</td><td>{{table7.c.cess}}</td></tr>
    <tr><td class="center">(d)</td><td>Reclaim on rectification of mismatch<br>credit note</td><td class="center">Reduce</td><td>{{table7.d.integrated_tax}}</td><td>{{table7.d.central_tax}}</td><td>{{table7.d.state_ut_tax}}</td><td>{{table7.d.cess}}</td></tr>
    <tr><td class="center">(e)</td><td>Negative tax liability from previous tax<br>periods</td><td class="center">Reduce</td><td>{{table7.e.integrated_tax}}</td><td>{{table7.e.central_tax}}</td><td>{{table7.e.state_ut_tax}}</td><td>{{table7.e.cess}}</td></tr>
    <tr><td class="center">(f)</td><td>Tax paid on advance in earlier tax<br>periods and adjusted with tax on supplies<br>made in current tax period</td><td class="center">Reduce</td><td>{{table7.f.integrated_tax}}</td><td>{{table7.f.central_tax}}</td><td>{{table7.f.state_ut_tax}}</td><td>{{table7.f.cess}}</td></tr>
    <tr><td class="center">(g)</td><td>Input Tax credit reversal/reclaim</td><td class="center">Add/Reduce</td><td>{{table7.g.integrated_tax}}</td><td>{{table7.g.central_tax}}</td><td>{{table7.g.state_ut_tax}}</td><td>{{table7.g.cess}}</td></tr>
  </table>

  <div class="section-title">8. Total tax liability</div>

  <table class="compact">
    <colgroup>
      <col style="width: 20%"><col style="width: 28%"><col style="width: 14%"><col style="width: 12%"><col style="width: 15%"><col style="width: 11%">
    </colgroup>
    <tr>
      <th rowspan="2">Rate of Tax</th>
      <th rowspan="2">Taxable value</th>
      <th colspan="4">Amount of tax</th>
    </tr>
    <tr><th>Integrated<br>tax</th><th>Central<br>tax</th><th>State/UT<br>Tax</th><th>CESS</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>

    <tr><td colspan="6">8A. On outward supplies</td></tr>
    {{#each table8_total_tax_liability.outward_supplies}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table8_outward_supplies}}

    <tr><td colspan="6">8B. On inward supplies attracting reverse charge</td></tr>
    {{#each table8_total_tax_liability.reverse_charge_inward_supplies}}
    <tr><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table8_reverse_charge_inward_supplies}}

    <tr><td colspan="2">8C. On account of Input Tax Credit<br>Reversal/reclaim</td><td>{{table8_total_tax_liability.itc_reversal_reclaim.integrated_tax}}</td><td>{{table8_total_tax_liability.itc_reversal_reclaim.central_tax}}</td><td>{{table8_total_tax_liability.itc_reversal_reclaim.state_ut_tax}}</td><td>{{table8_total_tax_liability.itc_reversal_reclaim.cess}}</td></tr>
    <tr><td colspan="2">8D. On account of mismatch/ rectification /other<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;reasons</td><td>{{table8_total_tax_liability.mismatch_rectification_other_reasons.integrated_tax}}</td><td>{{table8_total_tax_liability.mismatch_rectification_other_reasons.central_tax}}</td><td>{{table8_total_tax_liability.mismatch_rectification_other_reasons.state_ut_tax}}</td><td>{{table8_total_tax_liability.mismatch_rectification_other_reasons.cess}}</td></tr>
  </table>
</div>
```

---

### Page 5

```html
<div class="page">
  <div class="section-title">9. Credit of TDS and TCS</div>

  <table class="compact" style="width:79%; margin-left:0;">
    <colgroup>
      <col style="width: 6%"><col style="width: 30%"><col style="width: 16%"><col style="width: 20%"><col style="width: 28%">
    </colgroup>
    <tr><td colspan="2" rowspan="2"></td><th colspan="3">Amount</th></tr>
    <tr><th>Integrated<br>tax</th><th>Central tax</th><th>State/ UT Tax</th></tr>
    <tr><td colspan="2" class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td></tr>
    <tr><td class="center">(a)</td><td class="center">TDS</td><td>{{table9_credit_tds_tcs.tds.integrated_tax}}</td><td>{{table9_credit_tds_tcs.tds.central_tax}}</td><td>{{table9_credit_tds_tcs.tds.state_ut_tax}}</td></tr>
    <tr><td class="center">(b)</td><td class="center">TCS</td><td>{{table9_credit_tds_tcs.tcs.integrated_tax}}</td><td>{{table9_credit_tds_tcs.tcs.central_tax}}</td><td>{{table9_credit_tds_tcs.tcs.state_ut_tax}}</td></tr>
  </table>

  <div class="section-title">10. &nbsp;&nbsp; Interest liability (Interest as on {{table10_interest_liability.interest_as_on_or_dots}})</div>

  <table class="very-compact">
    <colgroup>
      <col style="width: 17%"><col style="width: 10.5%"><col style="width: 11.5%"><col style="width: 8.8%"><col style="width: 9.4%"><col style="width: 12.8%"><col style="width: 8.8%"><col style="width: 9.5%"><col style="width: 11%">
    </colgroup>
    <tr>
      <th>On account of</th>
      <th>Output<br>liability<br>on<br>mismatch</th>
      <th>ITC<br>claimed on<br>mismatched<br>invoice</th>
      <th>On<br>account<br>of other<br>ITC<br>reversal</th>
      <th>Undue<br>excess<br>claims or<br>excess<br>reduction<br>[refer sec<br>50(3)]</th>
      <th>Credit of<br>interest on<br>rectification<br>of<br>mismatch</th>
      <th>Interest<br>liability<br>carry<br>forward</th>
      <th>Delay in<br>payment<br>of tax</th>
      <th>Total<br>interest<br>liability</th>
    </tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td></tr>
    <tr><td>(a)Integrated<br>&nbsp;&nbsp;&nbsp;&nbsp;Tax</td><td>{{table10_interest_liability.integrated_tax.output_liability_on_mismatch}}</td><td>{{table10_interest_liability.integrated_tax.itc_claimed_on_mismatched_invoice}}</td><td>{{table10_interest_liability.integrated_tax.other_itc_reversal}}</td><td>{{table10_interest_liability.integrated_tax.undue_excess_claims_or_reduction}}</td><td>{{table10_interest_liability.integrated_tax.credit_of_interest_on_rectification}}</td><td>{{table10_interest_liability.integrated_tax.interest_liability_carry_forward}}</td><td>{{table10_interest_liability.integrated_tax.delay_in_payment_of_tax}}</td><td>{{table10_interest_liability.integrated_tax.total_interest_liability}}</td></tr>
    <tr><td>(b) Central Tax</td><td>{{table10_interest_liability.central_tax.output_liability_on_mismatch}}</td><td>{{table10_interest_liability.central_tax.itc_claimed_on_mismatched_invoice}}</td><td>{{table10_interest_liability.central_tax.other_itc_reversal}}</td><td>{{table10_interest_liability.central_tax.undue_excess_claims_or_reduction}}</td><td>{{table10_interest_liability.central_tax.credit_of_interest_on_rectification}}</td><td>{{table10_interest_liability.central_tax.interest_liability_carry_forward}}</td><td>{{table10_interest_liability.central_tax.delay_in_payment_of_tax}}</td><td>{{table10_interest_liability.central_tax.total_interest_liability}}</td></tr>
    <tr><td>(c) State/UT<br>&nbsp;&nbsp;&nbsp;&nbsp;Tax</td><td>{{table10_interest_liability.state_ut_tax.output_liability_on_mismatch}}</td><td>{{table10_interest_liability.state_ut_tax.itc_claimed_on_mismatched_invoice}}</td><td>{{table10_interest_liability.state_ut_tax.other_itc_reversal}}</td><td>{{table10_interest_liability.state_ut_tax.undue_excess_claims_or_reduction}}</td><td>{{table10_interest_liability.state_ut_tax.credit_of_interest_on_rectification}}</td><td>{{table10_interest_liability.state_ut_tax.interest_liability_carry_forward}}</td><td>{{table10_interest_liability.state_ut_tax.delay_in_payment_of_tax}}</td><td>{{table10_interest_liability.state_ut_tax.total_interest_liability}}</td></tr>
    <tr><td>(d) Cess</td><td>{{table10_interest_liability.cess.output_liability_on_mismatch}}</td><td>{{table10_interest_liability.cess.itc_claimed_on_mismatched_invoice}}</td><td>{{table10_interest_liability.cess.other_itc_reversal}}</td><td>{{table10_interest_liability.cess.undue_excess_claims_or_reduction}}</td><td>{{table10_interest_liability.cess.credit_of_interest_on_rectification}}</td><td>{{table10_interest_liability.cess.interest_liability_carry_forward}}</td><td>{{table10_interest_liability.cess.delay_in_payment_of_tax}}</td><td>{{table10_interest_liability.cess.total_interest_liability}}</td></tr>
  </table>

  <div class="section-title">11. Late Fee</div>

  <table class="compact">
    <colgroup><col style="width: 24%"><col style="width: 22%"><col style="width: 54%"></colgroup>
    <tr><th>On account of</th><th>Central Tax</th><th>State/UT tax</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td></tr>
    <tr><td class="center">Late fee</td><td>{{table11_late_fee.central_tax}}</td><td>{{table11_late_fee.state_ut_tax}}</td></tr>
  </table>

  <div class="part-title">Part B</div>
  <div class="section-title">12. Tax payable and paid</div>

  <table class="compact">
    <colgroup>
      <col style="width: 18%"><col style="width: 11%"><col style="width: 8.5%"><col style="width: 14.5%"><col style="width: 11%"><col style="width: 13%"><col style="width: 11%"><col style="width: 13%">
    </colgroup>
    <tr>
      <th rowspan="2">Description</th>
      <th rowspan="2">Tax<br>payable</th>
      <th rowspan="2">Paid<br>in<br>cash</th>
      <th colspan="4">Paid through ITC</th>
      <th rowspan="2">Tax Paid</th>
    </tr>
    <tr><th>Integrated<br>Tax</th><th>Central<br>Tax</th><th>State/UT<br>Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td></tr>
  </table>
</div>
```

---

### Page 6

```html
<div class="page">
  <table class="compact">
    <colgroup>
      <col style="width: 18%"><col style="width: 11%"><col style="width: 8.5%"><col style="width: 14.5%"><col style="width: 11%"><col style="width: 13%"><col style="width: 11%"><col style="width: 13%">
    </colgroup>
    <tr><td>(a)&nbsp;&nbsp; Integrated<br>&nbsp;&nbsp;&nbsp;&nbsp; Tax</td><td>{{table12_tax_payable_paid.integrated_tax.tax_payable}}</td><td>{{table12_tax_payable_paid.integrated_tax.paid_in_cash}}</td><td>{{table12_tax_payable_paid.integrated_tax.paid_through_itc_integrated_tax}}</td><td>{{table12_tax_payable_paid.integrated_tax.paid_through_itc_central_tax}}</td><td>{{table12_tax_payable_paid.integrated_tax.paid_through_itc_state_ut_tax}}</td><td>{{table12_tax_payable_paid.integrated_tax.paid_through_itc_cess}}</td><td>{{table12_tax_payable_paid.integrated_tax.tax_paid}}</td></tr>
    <tr><td>(b)&nbsp;&nbsp; Central Tax</td><td>{{table12_tax_payable_paid.central_tax.tax_payable}}</td><td>{{table12_tax_payable_paid.central_tax.paid_in_cash}}</td><td>{{table12_tax_payable_paid.central_tax.paid_through_itc_integrated_tax}}</td><td>{{table12_tax_payable_paid.central_tax.paid_through_itc_central_tax}}</td><td>{{table12_tax_payable_paid.central_tax.paid_through_itc_state_ut_tax}}</td><td>{{table12_tax_payable_paid.central_tax.paid_through_itc_cess}}</td><td>{{table12_tax_payable_paid.central_tax.tax_paid}}</td></tr>
    <tr><td>(c)&nbsp;&nbsp; State/UT<br>&nbsp;&nbsp;&nbsp;&nbsp; Tax</td><td>{{table12_tax_payable_paid.state_ut_tax.tax_payable}}</td><td>{{table12_tax_payable_paid.state_ut_tax.paid_in_cash}}</td><td>{{table12_tax_payable_paid.state_ut_tax.paid_through_itc_integrated_tax}}</td><td>{{table12_tax_payable_paid.state_ut_tax.paid_through_itc_central_tax}}</td><td>{{table12_tax_payable_paid.state_ut_tax.paid_through_itc_state_ut_tax}}</td><td>{{table12_tax_payable_paid.state_ut_tax.paid_through_itc_cess}}</td><td>{{table12_tax_payable_paid.state_ut_tax.tax_paid}}</td></tr>
    <tr><td>(d)&nbsp;&nbsp; Cess</td><td>{{table12_tax_payable_paid.cess.tax_payable}}</td><td>{{table12_tax_payable_paid.cess.paid_in_cash}}</td><td>{{table12_tax_payable_paid.cess.paid_through_itc_integrated_tax}}</td><td>{{table12_tax_payable_paid.cess.paid_through_itc_central_tax}}</td><td>{{table12_tax_payable_paid.cess.paid_through_itc_state_ut_tax}}</td><td>{{table12_tax_payable_paid.cess.paid_through_itc_cess}}</td><td>{{table12_tax_payable_paid.cess.tax_paid}}</td></tr>
  </table>

  <div class="section-title">13. Interest, Late Fee and any other amount (other than tax) payable and paid</div>

  <table class="compact">
    <colgroup><col style="width:47%"><col style="width:28%"><col style="width:25%"></colgroup>
    <tr><th>Description</th><th>Amount payable</th><th>Amount Paid</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td></tr>
    <tr><td colspan="3">(I)&nbsp;&nbsp;&nbsp;&nbsp; Interest on account of</td></tr>
    <tr><td>(a)&nbsp;&nbsp;&nbsp; Integrated tax</td><td>{{table13_interest_late_fee_other.interest_integrated_tax.amount_payable}}</td><td>{{table13_interest_late_fee_other.interest_integrated_tax.amount_paid}}</td></tr>
    <tr><td>(b)&nbsp;&nbsp;&nbsp; Central Tax</td><td>{{table13_interest_late_fee_other.interest_central_tax.amount_payable}}</td><td>{{table13_interest_late_fee_other.interest_central_tax.amount_paid}}</td></tr>
    <tr><td>(c)&nbsp;&nbsp;&nbsp; State/UT Tax</td><td>{{table13_interest_late_fee_other.interest_state_ut_tax.amount_payable}}</td><td>{{table13_interest_late_fee_other.interest_state_ut_tax.amount_paid}}</td></tr>
    <tr><td>(d)&nbsp;&nbsp;&nbsp; Cess</td><td>{{table13_interest_late_fee_other.interest_cess.amount_payable}}</td><td>{{table13_interest_late_fee_other.interest_cess.amount_paid}}</td></tr>
    <tr><td colspan="3">II Late fee</td></tr>
    <tr><td>(a)&nbsp;&nbsp;&nbsp; Central tax</td><td>{{table13_interest_late_fee_other.late_fee_central_tax.amount_payable}}</td><td>{{table13_interest_late_fee_other.late_fee_central_tax.amount_paid}}</td></tr>
    <tr><td>(b)&nbsp;&nbsp;&nbsp; State/UT tax</td><td>{{table13_interest_late_fee_other.late_fee_state_ut_tax.amount_payable}}</td><td>{{table13_interest_late_fee_other.late_fee_state_ut_tax.amount_paid}}</td></tr>
  </table>

  <div class="section-title">14. &nbsp; Refund claimed from Electronic cash ledger</div>

  <table class="compact">
    <colgroup><col style="width: 25%"><col style="width: 9.5%"><col style="width: 14%"><col style="width: 12%"><col style="width: 10.5%"><col style="width: 10.5%"><col style="width: 18.5%"></colgroup>
    <tr><th>Description</th><th>Tax</th><th>Interest</th><th>Penalty</th><th>Fee</th><th>Other</th><th>Debit Entry Nos.</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td></tr>
    <tr><td>(a)&nbsp;&nbsp;&nbsp; Integrated tax</td><td>{{table14_refund_cash_ledger.integrated_tax.tax}}</td><td>{{table14_refund_cash_ledger.integrated_tax.interest}}</td><td>{{table14_refund_cash_ledger.integrated_tax.penalty}}</td><td>{{table14_refund_cash_ledger.integrated_tax.fee}}</td><td>{{table14_refund_cash_ledger.integrated_tax.other}}</td><td>{{table14_refund_cash_ledger.integrated_tax.debit_entry_nos}}</td></tr>
    <tr><td>(b)&nbsp;&nbsp;&nbsp; Central Tax</td><td>{{table14_refund_cash_ledger.central_tax.tax}}</td><td>{{table14_refund_cash_ledger.central_tax.interest}}</td><td>{{table14_refund_cash_ledger.central_tax.penalty}}</td><td>{{table14_refund_cash_ledger.central_tax.fee}}</td><td>{{table14_refund_cash_ledger.central_tax.other}}</td><td>{{table14_refund_cash_ledger.central_tax.debit_entry_nos}}</td></tr>
    <tr><td>(c)&nbsp;&nbsp;&nbsp; State/UT Tax</td><td>{{table14_refund_cash_ledger.state_ut_tax.tax}}</td><td>{{table14_refund_cash_ledger.state_ut_tax.interest}}</td><td>{{table14_refund_cash_ledger.state_ut_tax.penalty}}</td><td>{{table14_refund_cash_ledger.state_ut_tax.fee}}</td><td>{{table14_refund_cash_ledger.state_ut_tax.other}}</td><td>{{table14_refund_cash_ledger.state_ut_tax.debit_entry_nos}}</td></tr>
    <tr><td>(d)&nbsp;&nbsp;&nbsp; Cess</td><td>{{table14_refund_cash_ledger.cess.tax}}</td><td>{{table14_refund_cash_ledger.cess.interest}}</td><td>{{table14_refund_cash_ledger.cess.penalty}}</td><td>{{table14_refund_cash_ledger.cess.fee}}</td><td>{{table14_refund_cash_ledger.cess.other}}</td><td>{{table14_refund_cash_ledger.cess.debit_entry_nos}}</td></tr>
    <tr><td colspan="3">Bank Account Details (Drop Down)</td><td>{{table14_refund_cash_ledger.bank_account_details}}</td><td></td><td></td><td></td></tr>
  </table>

  <div class="section-title">15. Debit entries in electronic cash/Credit ledger for tax/interest payment <span class="bold">[to be populated after</span><br><span style="font-weight:normal; margin-left:8mm;">payment of tax and submissions of return]</span></div>

  <table class="very-compact">
    <colgroup><col style="width:20%"><col style="width:11.5%"><col style="width:15%"><col style="width:13%"><col style="width:15%"><col style="width:7%"><col style="width:10%"><col style="width:8.5%"></colgroup>
    <tr>
      <th rowspan="2">Description</th>
      <th rowspan="2">Tax paid<br>in cash</th>
      <th colspan="4">Tax paid&nbsp; through ITC</th>
      <th rowspan="2">Interest</th>
      <th rowspan="2">Late<br>fee</th>
    </tr>
    <tr><th>Integrated tax</th><th>Central<br>Tax</th><th>State/UT Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td></tr>
    <tr><td>(a) Integrated tax</td><td>{{table15_debit_entries.integrated_tax.paid_in_cash}}</td><td>{{table15_debit_entries.integrated_tax.paid_through_itc_integrated_tax}}</td><td>{{table15_debit_entries.integrated_tax.paid_through_itc_central_tax}}</td><td>{{table15_debit_entries.integrated_tax.paid_through_itc_state_ut_tax}}</td><td>{{table15_debit_entries.integrated_tax.paid_through_itc_cess}}</td><td>{{table15_debit_entries.integrated_tax.interest}}</td><td>{{table15_debit_entries.integrated_tax.late_fee}}</td></tr>
    <tr><td>(b) Central Tax</td><td>{{table15_debit_entries.central_tax.paid_in_cash}}</td><td>{{table15_debit_entries.central_tax.paid_through_itc_integrated_tax}}</td><td>{{table15_debit_entries.central_tax.paid_through_itc_central_tax}}</td><td>{{table15_debit_entries.central_tax.paid_through_itc_state_ut_tax}}</td><td>{{table15_debit_entries.central_tax.paid_through_itc_cess}}</td><td>{{table15_debit_entries.central_tax.interest}}</td><td>{{table15_debit_entries.central_tax.late_fee}}</td></tr>
    <tr><td>(c) State/UT Tax</td><td>{{table15_debit_entries.state_ut_tax.paid_in_cash}}</td><td>{{table15_debit_entries.state_ut_tax.paid_through_itc_integrated_tax}}</td><td>{{table15_debit_entries.state_ut_tax.paid_through_itc_central_tax}}</td><td>{{table15_debit_entries.state_ut_tax.paid_through_itc_state_ut_tax}}</td><td>{{table15_debit_entries.state_ut_tax.paid_through_itc_cess}}</td><td>{{table15_debit_entries.state_ut_tax.interest}}</td><td>{{table15_debit_entries.state_ut_tax.late_fee}}</td></tr>
    <tr><td>(d) Cess</td><td>{{table15_debit_entries.cess.paid_in_cash}}</td><td>{{table15_debit_entries.cess.paid_through_itc_integrated_tax}}</td><td>{{table15_debit_entries.cess.paid_through_itc_central_tax}}</td><td>{{table15_debit_entries.cess.paid_through_itc_state_ut_tax}}</td><td>{{table15_debit_entries.cess.paid_through_itc_cess}}</td><td>{{table15_debit_entries.cess.interest}}</td><td>{{table15_debit_entries.cess.late_fee}}</td></tr>
  </table>
</div>
```

---

### Page 7

```html
<div class="page">
  <div class="verification">
    <p>Verification</p>
    <p>I hereby solemnly affirm and declare that the information given herein above is true and correct to the<br>best of my knowledge and belief and nothing has been concealed therefrom.</p>

    <table class="signature-grid">
      <tr>
        <td style="width:48%;">……………………………</td>
        <td style="width:52%;">Signatures of Authorised Signatory</td>
      </tr>
      <tr>
        <td>Place ……………<br>….……………………</td>
        <td>Name of Authorised Signatory</td>
      </tr>
      <tr>
        <td>Date …………….<br>/Status……………………………………</td>
        <td>Designation</td>
      </tr>
    </table>
  </div>

  <div class="instructions">
    <p class="bold">Instructions:-</p>

    <p>1. &nbsp; Terms Used :-</p>
    <p class="indent">a)&nbsp;&nbsp; GSTIN :- &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Goods and Services Tax Identification Number<br>
       b)&nbsp;&nbsp; TDS :- &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Tax Deducted at source<br>
       c)&nbsp;&nbsp; TCS :- &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Tax Collected at source</p>

    <p>2. &nbsp; GSTR 3 can be generated only when GSTR-1 and GSTR- 2 of the tax period have been<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;filed.</p>

    <p>3. &nbsp; Electronic liability register, electronic cash ledger and electronic credit ledger of taxpayer<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;will be updated on generation of GSTR-3 by taxpayer.</p>

    <p>4. &nbsp; Part-A of GSTR-3 is auto-populated on the basis of GSTR 1, GSTR 1A and GSTR 2.</p>

    <p>5. &nbsp; Part-B of GSTR-3 relates to payment of tax, interest, late fee etc. by utilising credit<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;available in electronic credit ledger and cash ledger.</p>

    <p>6. &nbsp; Tax liability relating to outward supplies in Table 4 is net of invoices, debit/credit notes<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;and advances received.</p>

    <p>7. &nbsp; Table 4.1 will not include zero rated supplies made without payment of taxes.</p>

    <p>8. &nbsp; Table 4.3 will not include amendments of supplies originally made under reverse charge<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;basis.</p>
  </div>
</div>
```

---

### Page 8

```html
<div class="page">
  <div class="instructions">
    <p>9. &nbsp; Tax liability due to reverse charge on inward supplies in Table 5 is net of invoices,<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;debit/credit notes, advances paid and adjustments made out of tax paid on advances<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;earlier.</p>

    <p>10. Utilization of input tax credit should be made in accordance with the provisions of section<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;49.</p>

    <p>11. GSTR-3 filed without discharging complete liability will not be treated as valid return.</p>

    <p>12. If taxpayer has filed a return which was not valid earlier and later on, he intends to<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;discharge the remaining liability, then he has to file the Part B of GSTR-3 again.</p>

    <p>13. Refund from cash ledger can only be claimed only when all the return related liabilities<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;for that tax period have been discharged.</p>

    <p>14. Refund claimed from cash ledger through Table 14 will result in a debit entry in electronic<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;cash ledger on filing of valid GSTR 3.]</p>

    <div class="footnote-line"></div>
    <p class="small"><sup>1</sup> Omitted vide Notification No. 19/2022- CT dated 28.09.2022(w.e.f. 01.10.2022).</p>
  </div>
</div>
```

---

## 6. Table-Specific Recreation Notes

### Tables 4.1 and 4.2

- These are rate-wise summary tables.
- In e-commerce rows, preserve the separate line `GSTIN of e-commerce operator` before the variable entry row.
- Use `operator_gstin` for the e-commerce GSTIN and keep the remaining values in the same rate-wise columns.

### Table 4.3

- This table starts on Page 2 and continues on Page 3.
- Repeat the header if the table flows to a new page.
- Preserve the split between `(I) Inter-State supplies` and `(II) Intra-state supplies`.

### Table 6 - Input tax credit

- The header has ten columns.
- `Amount of tax` spans columns 3-6.
- `Amount of ITC` spans columns 7-10.
- The first group `(I)` starts on Page 3 and continues on Page 4.

### Tables 12 and 15

- Both are eight-column payment tables.
- In Table 12, `Paid through ITC` spans columns 4-7.
- In Table 15, `Tax paid through ITC` spans columns 3-6.

---

## 7. Variable-Entry Handling Rules

1. Every table section with `{{#each ...}}` is dynamic.
2. Do **not** restrict the number of entries to the number of blank rows visible in the original PDF.
3. For more entries:
   - Add rows with identical borders and column widths.
   - Continue naturally to the next page.
   - Repeat the table header on the new page.
   - Preserve the section label, e.g., `A.`, `B.`, `(I)`, only at the beginning of that section unless the continuation page requires context.
4. For zero entries:
   - Keep one bordered blank row below that section.
5. Long text must wrap inside cells. Do not expand page width.
6. Amount columns should be right-aligned when numeric data is inserted.
7. Tax rates may be centered.
8. GSTIN fields may be left-aligned unless being rendered as fixed digit boxes.
9. Preserve the omitted-form note and footnote exactly.
10. Do not modernize statutory language.

---

## 8. Final AI Instruction Block

Copy this instruction into the AI that will generate the final document:

```text
Recreate FORM GSTR-3 exactly as per the provided Markdown/HTML specification. Use A4 portrait, Times New Roman, black borders, compact statutory-form layout, and the same section order from pages 1 to 8. Treat all rate-wise entry tables as dynamic arrays. If a table has more rows than the original blank space, continue it onto the next page while repeating the relevant table header. If a table has no entries, show one blank bordered row. Preserve the NOTE at the top, the ***OMITTED *** line, title, rule reference, Part-A/Part-B labels, table numbering, verification clause, instructions, and footnote. Do not redesign, simplify, or modernize the form.
```
