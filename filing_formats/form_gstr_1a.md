# FORM GSTR-1A - High-Accuracy Markdown/HTML Recreation Specification

Use this file as the master specification for recreating the uploaded **FORM GSTR-1A** document in the same statutory format. The document is an amendment form for outward supplies for the current tax period. The number of data entries in each table is variable; every entry table below must be generated from arrays/lists and must expand vertically as required.

> **Important:** Native Markdown tables cannot reproduce this form accurately because the source uses merged cells, narrow table columns, nested headers, multi-row statutory labels, compact borders, and one very long scroll-page layout. Recreate the form using **HTML/CSS inside Markdown** or convert the HTML to PDF/DOCX. Preserve the statutory structure, wording, line breaks, and table order.

---

## 1. Source Layout Rules

### Page setup

- Source page: **single long portrait page**.
- Source PDF page size: approximately **1440 pt width × 5766 pt height**.
- For exact PDF recreation, use a custom long page: `size: 1440pt 5766pt`.
- For normal printing, the same template may be allowed to flow across A4 portrait pages, but the statutory order and table headers must remain identical.
- Font family: **Times New Roman** or **Liberation Serif**.
- Use black text and black table borders only.
- No logos, watermarks, colours, shaded headers, decorative spacing, or additional branding.
- Keep the layout compact and statutory.

### Typography

| Element | Required style |
|---|---|
| Form reference | Centered, bold, approx. 12 pt |
| Main subtitle/title line | Left aligned, bold, approx. 24 pt in the source long page |
| Section headings | Bold, approx. 11-12 pt |
| Table text | Approx. 9-11 pt depending on column density |
| Dense tables | Use narrow columns, wrapping text, and vertical compression |
| Instructions | Approx. 9-10 pt, compact, left aligned |

### Table style

- Use `border-collapse: collapse` for all tables.
- Use `1px solid #000` borders.
- Header cells must be centered vertically and horizontally unless the original is left-aligned.
- Section rows such as `4A`, `6A`, `14A`, `15A (I)` must span the full width of the table.
- If a table section has no data, preserve **one blank bordered row** below that section.
- If a section has multiple rows, repeat the same row structure for each entry.
- Long text must wrap inside the cell and must not expand table width.
- Amount columns should be right-aligned when populated with numeric values.
- Preserve statutory spelling and spacing where shown, including `FORM- GSTR-1`, `FORM GSTR -1`, `Quaterly`, `ecommerce`, `u/s`, `State/UT`, and bracketed references.

---

## 2. Placeholder Convention

Use double curly braces for dynamic values.

Example:

~~~handlebars
{{financial_year}}
{{tax_period}}
{{gstin}}
{{legal_name}}
{{trade_name}}
{{arn}}
{{arn_date}}

{{#each table4A}}
  {{this.gstin_uin}}
{{/each}}
~~~

For digit boxes, print one character per cell. If the value is absent, leave the cell blank.

---

## 3. Required Data Schema

The document generator should accept this structure. Arrays may contain any number of rows.

~~~json
{
  "financial_year": "",
  "tax_period": "",
  "gstin": "",
  "legal_name": "",
  "trade_name": "",
  "arn": "<Auto>",
  "arn_date": "<Auto>",

  "table4A": [],
  "table4B": [],

  "table5": [],

  "table6A": [],
  "table6B": [],
  "table6C": [],

  "table7A": [],
  "table7B": [],

  "table8": {
    "8A": {"nil_rated": "", "exempted": "", "non_gst": ""},
    "8B": {"nil_rated": "", "exempted": "", "non_gst": ""},
    "8C": {"nil_rated": "", "exempted": "", "non_gst": ""},
    "8D": {"nil_rated": "", "exempted": "", "non_gst": ""}
  },

  "table9A": [],
  "table9B": [],
  "table9C": [],

  "table10A": [],
  "table10B": [],

  "table11A1": [],
  "table11A2": [],
  "table11B1": [],
  "table11B2": [],
  "table11_amendments": [],

  "table12_hsn": [],
  "table13_documents": [],

  "table14": [],
  "table14A": [],
  "table15": [],
  "table15A_registered_recipients": [],
  "table15A_unregistered_recipients": []
}
~~~

### Standard row field names

Use these row keys wherever applicable:

~~~json
{
  "gstin_uin": "",
  "invoice_no": "",
  "invoice_date": "",
  "invoice_value": "",
  "rate": "",
  "taxable_value": "",
  "integrated_tax": "",
  "central_tax": "",
  "state_ut_tax": "",
  "cess": "",
  "place_of_supply": "",
  "gstin_recipient": "",
  "shipping_bill_no": "",
  "shipping_bill_date": "",
  "gross_advance": "",
  "gross_advance_adjusted": "",
  "net_value_of_supplies": "",
  "tax_period_revised": "",
  "month_quarter": "",
  "operator_gstin": "",
  "revised_operator_gstin": "",
  "type_of_supplier": "",
  "type_of_recipient": "",
  "supplier_gstin": "",
  "recipient_gstin": "",
  "document_no": "",
  "document_date": "",
  "value_of_supplies_made": ""
}
~~~

---

## 4. CSS to Use

Embed this CSS in the generated HTML. Adjust only if required to fit a different renderer, but do not change the statutory visual identity.

~~~html
<style>
  @page {
    size: 1440pt 5766pt;
    margin: 0;
  }

  html, body {
    margin: 0;
    padding: 0;
    color: #000;
    background: #fff;
    font-family: "Times New Roman", "Liberation Serif", serif;
    font-size: 10pt;
    line-height: 1.1;
  }

  .gstr1a-page {
    width: 1440pt;
    min-height: 5766pt;
    box-sizing: border-box;
    padding: 8pt 6pt 8pt 6pt;
    position: relative;
  }

  .form-reference {
    text-align: center;
    font-weight: bold;
    font-size: 12pt;
    margin: 4pt 0 22pt 0;
  }

  .main-heading {
    text-align: left;
    font-weight: bold;
    font-size: 24pt;
    line-height: 1.05;
    margin: 0 0 16pt 0;
  }

  .section-title {
    font-weight: bold;
    font-size: 11.2pt;
    margin: 12pt 0 4pt 0;
  }

  .amount-note {
    text-align: right;
    font-size: 9pt;
    margin: -2pt 0 3pt 0;
  }

  table {
    border-collapse: collapse;
    table-layout: fixed;
    margin: 0 0 5pt 0;
  }

  th, td {
    border: 1px solid #000;
    padding: 2pt 2.2pt;
    vertical-align: top;
    font-size: 9pt;
    font-weight: normal;
    line-height: 1.08;
    word-wrap: break-word;
    overflow-wrap: break-word;
  }

  th {
    text-align: center;
    vertical-align: middle;
  }

  .wide { width: 100%; }
  .narrow { width: 470pt; }
  .medium { width: 620pt; }
  .full { width: 1428pt; }
  .center { text-align: center; }
  .right { text-align: right; }
  .left { text-align: left; }
  .bold { font-weight: bold; }
  .small { font-size: 8pt; }
  .tiny { font-size: 7pt; }
  .nowrap { white-space: nowrap; }
  .blank-row td { height: 15pt; }
  .tall-row td { height: 25pt; }
  .section-row td, td.section-row { text-align: left; }

  .period-table {
    width: 185pt;
    margin-bottom: 14pt;
  }

  .info-table {
    width: 420pt;
    margin-bottom: 12pt;
  }

  .instructions {
    width: 1428pt;
    margin-top: 8pt;
    font-size: 9pt;
    line-height: 1.12;
  }

  .instructions p {
    margin: 3pt 0;
  }

  .instruction-table {
    width: 720pt;
    margin-top: 6pt;
  }
</style>
~~~

---

## 5. Document Template

Paste the following HTML inside the Markdown renderer. This template intentionally uses HTML tables because Markdown tables cannot reproduce merged statutory headers.

~~~html
<div class="gstr1a-page">

  <div class="form-reference">“FORM GSTR-1A [See proviso to rule 59(1)]</div>

  <div class="main-heading">Amendment of outward supplies of goods or services for current tax period</div>

  <!-- Financial year and tax period box -->
  <table class="period-table">
    <colgroup>
      <col style="width: 90pt"><col style="width: 24pt"><col style="width: 24pt"><col style="width: 24pt"><col style="width: 23pt">
    </colgroup>
    <tr>
      <td>[Financial<br>Year]</td>
      <td class="center">{{financial_year_digit_1}}</td>
      <td class="center">{{financial_year_digit_2}}</td>
      <td class="center">{{financial_year_digit_3}}</td>
      <td class="center">{{financial_year_digit_4}}</td>
    </tr>
    <tr>
      <td>[Tax<br>Period]</td>
      <td colspan="4">{{tax_period}}</td>
    </tr>
  </table>

  <!-- Basic details -->
  <table class="info-table">
    <colgroup>
      <col style="width: 30pt"><col style="width: 35pt"><col style="width: 185pt"><col style="width: 170pt">
    </colgroup>
    <tr>
      <td class="center">1.</td>
      <td></td>
      <td>GSTIN</td>
      <td>{{gstin_digit_boxes}}</td>
    </tr>
    <tr>
      <td class="center">2.</td>
      <td class="center">(a)</td>
      <td>Legal name of the<br>registered person</td>
      <td>{{legal_name}}</td>
    </tr>
    <tr>
      <td></td>
      <td class="center">(b)</td>
      <td>Trade name, if any</td>
      <td>{{trade_name}}</td>
    </tr>
    <tr>
      <td class="center">3.</td>
      <td class="center">(a)</td>
      <td>ARN</td>
      <td>{{arn}}</td>
    </tr>
    <tr>
      <td></td>
      <td class="center">(b)</td>
      <td>Date of ARN</td>
      <td>{{arn_date}}</td>
    </tr>
  </table>

  <div class="section-title">4. Taxable outward supplies made to registered persons (including UIN-holders) other than supplies covered by Table 6</div>
  <div class="amount-note">(Amount in Rs. for all Tables)</div>

  <!-- Table 4 -->
  <table class="medium">
    <colgroup>
      <col style="width: 58pt"><col style="width: 40pt"><col style="width: 42pt"><col style="width: 45pt"><col style="width: 38pt"><col style="width: 58pt"><col style="width: 66pt"><col style="width: 58pt"><col style="width: 58pt"><col style="width: 42pt"><col style="width: 95pt">
    </colgroup>
    <tr>
      <th rowspan="2">GSTIN/<br>UIN</th>
      <th colspan="3">Invoice details</th>
      <th rowspan="2">Rate</th>
      <th rowspan="2">Taxable<br>value</th>
      <th colspan="4">Amount</th>
      <th rowspan="2">Place<br>of<br>Supply<br>(Name<br>of<br>State/UT)</th>
    </tr>
    <tr>
      <th>No.</th><th>Date</th><th>Valu<br>e</th><th>Integrat<br>ed Tax</th><th>Central<br>Tax</th><th>State<br>/ UT<br>Tax</th><th>Cess</th>
    </tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td></tr>

    <tr><td colspan="11">4A. Supplies other than those [attracting reverse charge (including supplies made through<br>e-commerce operator attracting TCS)]</td></tr>
    {{#each table4A}}
    <tr>
      <td>{{gstin_uin}}</td><td>{{invoice_no}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table4A}}

    <tr><td colspan="11">4B. Supplies attracting tax on reverse charge basis</td></tr>
    {{#each table4B}}
    <tr>
      <td>{{gstin_uin}}</td><td>{{invoice_no}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td>
    </tr>
    {{/each}}
    {{blank_rows_if_empty_table4B}}
  </table>

  <div class="section-title">5. Taxable outward inter-State supplies to un-registered persons where the invoice value is more than Rs 1 lakh</div>

  <!-- Table 5 -->
  <table class="medium">
    <colgroup>
      <col style="width: 100pt"><col style="width: 50pt"><col style="width: 50pt"><col style="width: 55pt"><col style="width: 45pt"><col style="width: 75pt"><col style="width: 95pt"><col style="width: 60pt">
    </colgroup>
    <tr>
      <th rowspan="2">Place<br>of<br>Supply<br>(State/UT)</th>
      <th colspan="3">Invoice details</th>
      <th rowspan="2">Rate</th>
      <th rowspan="2">Taxable<br>Value</th>
      <th colspan="2">Amount</th>
    </tr>
    <tr><th>No.</th><th>Date</th><th>Valu<br>e</th><th>Integra<br>ted Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td></tr>
    <tr><td colspan="8">5. Outward supplies (including supplies made through e-commerce operator, rate wise)</td></tr>
    {{#each table5}}
    <tr><td>{{place_of_supply}}</td><td>{{invoice_no}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table5}}
  </table>

  <div class="section-title">6. Zero rated supplies and Deemed Exports</div>

  <!-- Table 6 -->
  <table class="medium">
    <colgroup>
      <col style="width: 45pt"><col style="width: 32pt"><col style="width: 32pt"><col style="width: 34pt"><col style="width: 32pt"><col style="width: 32pt"><col style="width: 32pt"><col style="width: 48pt"><col style="width: 36pt"><col style="width: 32pt"><col style="width: 48pt"><col style="width: 36pt"><col style="width: 32pt"><col style="width: 48pt"><col style="width: 36pt"><col style="width: 32pt">
    </colgroup>
    <tr>
      <th rowspan="2">GS<br>TIN<br>of<br>reci<br>pien<br>t</th>
      <th colspan="3">Invoice<br>details</th>
      <th colspan="2">Shippi<br>ng<br>bill/<br>Bill of<br>export</th>
      <th colspan="3">Integrated<br>Tax</th>
      <th colspan="3">Central Tax</th>
      <th colspan="3">State / UT<br>Tax</th>
      <th rowspan="2">C<br>e<br>s<br>s</th>
    </tr>
    <tr>
      <th>N<br>o<br>.</th><th>D<br>a<br>t<br>e</th><th>V<br>a<br>l<br>u<br>e</th>
      <th>N<br>o<br>.</th><th>D<br>a<br>t<br>e</th>
      <th>R<br>at<br>e</th><th>T<br>a<br>x<br>a<br>bl<br>e<br>v<br>al<br>u<br>e</th><th>A<br>m<br>t</th>
      <th>R<br>at<br>e</th><th>T<br>a<br>x<br>a<br>bl<br>e<br>v<br>al<br>u<br>e</th><th>A<br>m<br>t</th>
      <th>R<br>at<br>e</th><th>T<br>a<br>x<br>a<br>bl<br>e<br>v<br>al<br>u<br>e</th><th>A<br>m<br>t</th>
    </tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td></tr>

    <tr><td colspan="16">6A. Exports</td></tr>
    {{#each table6A}}
    <tr><td>{{gstin_recipient}}</td><td>{{invoice_no}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{shipping_bill_no}}</td><td>{{shipping_bill_date}}</td><td>{{igst_rate}}</td><td>{{igst_taxable_value}}</td><td>{{igst_amount}}</td><td>{{cgst_rate}}</td><td>{{cgst_taxable_value}}</td><td>{{cgst_amount}}</td><td>{{sgst_rate}}</td><td>{{sgst_taxable_value}}</td><td>{{sgst_amount}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table6A}}

    <tr><td colspan="16">6B. Supplies made to SEZ unit or SEZ<br>Developer</td></tr>
    {{#each table6B}}
    <tr><td>{{gstin_recipient}}</td><td>{{invoice_no}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{shipping_bill_no}}</td><td>{{shipping_bill_date}}</td><td>{{igst_rate}}</td><td>{{igst_taxable_value}}</td><td>{{igst_amount}}</td><td>{{cgst_rate}}</td><td>{{cgst_taxable_value}}</td><td>{{cgst_amount}}</td><td>{{sgst_rate}}</td><td>{{sgst_taxable_value}}</td><td>{{sgst_amount}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table6B}}

    <tr><td colspan="16">6C. Deemed exports</td></tr>
    {{#each table6C}}
    <tr><td>{{gstin_recipient}}</td><td>{{invoice_no}}</td><td>{{invoice_date}}</td><td>{{invoice_value}}</td><td>{{shipping_bill_no}}</td><td>{{shipping_bill_date}}</td><td>{{igst_rate}}</td><td>{{igst_taxable_value}}</td><td>{{igst_amount}}</td><td>{{cgst_rate}}</td><td>{{cgst_taxable_value}}</td><td>{{cgst_amount}}</td><td>{{sgst_rate}}</td><td>{{sgst_taxable_value}}</td><td>{{sgst_amount}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table6C}}
  </table>

  <div class="section-title">7. Taxable supplies (Net of debit notes and credit notes) to unregistered persons other than the supplies covered in Table 5</div>

  <!-- Table 7 -->
  <table class="medium">
    <colgroup>
      <col style="width: 95pt"><col style="width: 120pt"><col style="width: 85pt"><col style="width: 85pt"><col style="width: 120pt"><col style="width: 65pt">
    </colgroup>
    <tr><th rowspan="2">Rate<br>of<br>tax</th><th rowspan="2">Total Taxable<br>value</th><th colspan="4">Amount</th></tr>
    <tr><th>Integrated</th><th>Central</th><th>State Tax/UT<br>Tax</th><th>Ce<br>ss</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>
    <tr><td colspan="6">7A. Intra-State supplies</td></tr>
    <tr><td colspan="6">Consolidated rate wise outward supplies [including supplies made through e-commerce<br>operator attracting<br>TCS]</td></tr>
    {{#each table7A}}
    <tr><td>{{rate}}</td><td>{{total_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table7A}}

    <tr><td colspan="6">7B. Inter-State Supplies where invoice value is upto Rs 1 Lakh [Rate wise]-</td></tr>
    <tr><td colspan="6">Consolidated rate wise outward supplies [including supplies made through e-commerce<br>operator attracting TCS]</td></tr>
    <tr><td colspan="2">Place of Supply (Name of<br>State)</td><td colspan="4"></td></tr>
    {{#each table7B}}
    <tr><td>{{rate}}</td><td>{{total_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table7B}}
  </table>

  <div class="section-title">8. Nil rated, exempted and non-GST outward supplies</div>

  <!-- Table 8 -->
  <table class="narrow">
    <colgroup><col style="width: 175pt"><col style="width: 85pt"><col style="width: 135pt"><col style="width: 75pt"></colgroup>
    <tr><th>Description</th><th>Nil Rated<br>Supplies</th><th>Exempted<br>(Other than Nil<br>rated/nonGST supply)</th><th>Non-GST<br>supplies</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td></tr>
    <tr><td>8A. Inter-State supplies to registered<br>persons</td><td>{{table8.8A.nil_rated}}</td><td>{{table8.8A.exempted}}</td><td>{{table8.8A.non_gst}}</td></tr>
    <tr><td>8B. Intra- State supplies to registered<br>persons</td><td>{{table8.8B.nil_rated}}</td><td>{{table8.8B.exempted}}</td><td>{{table8.8B.non_gst}}</td></tr>
    <tr><td>8C. Inter-State supplies to<br>unregistered persons</td><td>{{table8.8C.nil_rated}}</td><td>{{table8.8C.exempted}}</td><td>{{table8.8C.non_gst}}</td></tr>
    <tr><td>8D. Intra-State supplies<br>to unregistered persons</td><td>{{table8.8D.nil_rated}}</td><td>{{table8.8D.exempted}}</td><td>{{table8.8D.non_gst}}</td></tr>
  </table>

  <div class="section-title">9. Amendments to taxable outward supply details furnished in FORM- GSTR-1 for the current tax periods in Table 4, 5 and 6 [including debit and credit notes issued during current period and amendments thereof]</div>

  <!-- Table 9 -->
  <table class="medium">
    <colgroup>
      <col style="width: 42pt"><col style="width: 33pt"><col style="width: 36pt"><col style="width: 42pt"><col style="width: 33pt"><col style="width: 36pt"><col style="width: 33pt"><col style="width: 36pt"><col style="width: 42pt"><col style="width: 38pt"><col style="width: 58pt"><col style="width: 60pt"><col style="width: 52pt"><col style="width: 52pt"><col style="width: 38pt"><col style="width: 60pt">
    </colgroup>
    <tr>
      <th colspan="3">Details<br>of<br>original<br>document</th>
      <th colspan="6">Revised details of document<br>or details of original Debit<br>or Credit Notes</th>
      <th rowspan="2">R<br>at<br>e</th>
      <th rowspan="2">Taxa<br>ble<br>Value</th>
      <th colspan="4">Amount</th>
      <th rowspan="2">Plac<br>e of<br>supp<br>ly</th>
    </tr>
    <tr>
      <th>G<br>ST<br>IN</th><th>Do<br>c.<br>No<br>.</th><th>Do<br>c.<br>Da<br>te</th>
      <th>GS<br>TI<br>N</th><th colspan="2">Docume<br>nt</th><th colspan="2">Shipping<br>bill</th><th>Va<br>lue</th>
      <th>Inte<br>grat<br>ed<br>Tax</th><th>Cent<br>ral<br>Tax</th><th>Stat<br>e<br>/ UT<br>Tax</th><th>Cess</th>
    </tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td></tr>

    <tr><td colspan="16">9A. Amendment of invoice/Shipping bill details furnished</td></tr>
    {{#each table9A}}
    <tr><td>{{original_gstin}}</td><td>{{original_doc_no}}</td><td>{{original_doc_date}}</td><td>{{revised_gstin}}</td><td>{{document_no}}</td><td>{{document_date}}</td><td>{{shipping_bill_no}}</td><td>{{shipping_bill_date}}</td><td>{{value}}</td><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table9A}}

    <tr><td colspan="16">9B. Debit Notes/Credit Notes [original]</td></tr>
    {{#each table9B}}
    <tr><td>{{original_gstin}}</td><td>{{original_doc_no}}</td><td>{{original_doc_date}}</td><td>{{revised_gstin}}</td><td>{{document_no}}</td><td>{{document_date}}</td><td>{{shipping_bill_no}}</td><td>{{shipping_bill_date}}</td><td>{{value}}</td><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table9B}}

    <tr><td colspan="16">9C. Debit Notes/Credit Notes [Amended]</td></tr>
    {{#each table9C}}
    <tr><td>{{original_gstin}}</td><td>{{original_doc_no}}</td><td>{{original_doc_date}}</td><td>{{revised_gstin}}</td><td>{{document_no}}</td><td>{{document_date}}</td><td>{{shipping_bill_no}}</td><td>{{shipping_bill_date}}</td><td>{{value}}</td><td>{{rate}}</td><td>{{taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table9C}}
  </table>

  <div class="section-title">10. Amendments to taxable outward supplies to unregistered persons furnished in FORM GSTR-1 for current tax periods in Table 7</div>

  <!-- Table 10 -->
  <table class="medium">
    <colgroup><col style="width: 95pt"><col style="width: 125pt"><col style="width: 90pt"><col style="width: 90pt"><col style="width: 125pt"><col style="width: 65pt"></colgroup>
    <tr><th rowspan="2">Rate of tax</th><th rowspan="2">Total<br>Taxable<br>value</th><th colspan="4">Amount</th></tr>
    <tr><th>Integrated<br>Tax</th><th>Central Tax</th><th>State/UT<br>Tax<br>UT Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td></tr>
    <tr><td colspan="2">Tax period for which the<br>details are being revised</td><td colspan="4">current tax period should be auto populated here)</td></tr>
    <tr><td colspan="6">10A. Intra-State Supplies[including supplies made through e-commerce operator attracting<br>TCS] [Rate wise]</td></tr>
    {{#each table10A}}
    <tr><td>{{rate}}</td><td>{{total_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table10A}}
    <tr><td colspan="6">10B. Inter-State Supplies[including supplies made through e-commerce operator<br>attracting TCS] [Rate wise]</td></tr>
    <tr><td colspan="6">Place of Supply (Name of<br>State)</td></tr>
    {{#each table10B}}
    <tr><td>{{rate}}</td><td>{{total_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table10B}}
  </table>

  <div class="section-title">11. Consolidated Statement of Advances Received/Advance adjusted in the current tax period/ Amendments of information furnished in current tax period [(Net of refund vouchers, if any)]</div>

  <!-- Table 11 -->
  <table class="medium">
    <colgroup><col style="width: 55pt"><col style="width: 145pt"><col style="width: 110pt"><col style="width: 80pt"><col style="width: 80pt"><col style="width: 80pt"><col style="width: 70pt"></colgroup>
    <tr><th rowspan="2">Rate</th><th rowspan="2">Gross<br>Advance<br>Received/adjusted</th><th rowspan="2">Place<br>of<br>supply<br>(Name<br>of<br>State<br>/UT)</th><th colspan="4">Amount</th></tr>
    <tr><th>Integr<br>ated<br>Tax</th><th>Centr<br>al<br>Tax</th><th>State/U<br>T Tax<br>UT<br>Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td></tr>
    <tr><td colspan="7" class="bold">I Information for the current tax period</td></tr>
    <tr><td colspan="7">11A. Advance amount received in the tax period for which invoice has not been issued (tax<br>amount to be added to output tax liability)</td></tr>
    <tr><td colspan="7">11A (1). Intra-State supplies(Rate Wise)</td></tr>
    {{#each table11A1}}
    <tr><td>{{rate}}</td><td>{{gross_advance}}</td><td>{{place_of_supply}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table11A1}}
    <tr><td colspan="7">11A (2). Inter-State Supplies(Rate Wise)</td></tr>
    {{#each table11A2}}
    <tr><td>{{rate}}</td><td>{{gross_advance}}</td><td>{{place_of_supply}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table11A2}}
    <tr><td colspan="7">11B. Advance amount received in earlier tax period and adjusted against the supplies being<br>shown in this tax period in Table Nos. 4, 5, 6 and 7</td></tr>
    <tr><td colspan="7">11B (1). Intra-State Supplies (Rate Wise)</td></tr>
    {{#each table11B1}}
    <tr><td>{{rate}}</td><td>{{gross_advance_adjusted}}</td><td>{{place_of_supply}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table11B1}}
    <tr><td colspan="7">11B (2). Inter-State Supplies(Rate Wise)</td></tr>
    {{#each table11B2}}
    <tr><td>{{rate}}</td><td>{{gross_advance_adjusted}}</td><td>{{place_of_supply}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table11B2}}
    <tr><td colspan="7" class="bold">II Amendment of information furnished in Table No. 11[1] in GSTR-1 statement for current<br>tax period<br>[Furnish revised information]</td></tr>
  </table>

  <!-- Table 11 amendment selector -->
  <table class="medium">
    <colgroup><col style="width: 65pt"><col style="width: 290pt"><col style="width: 65pt"><col style="width: 65pt"><col style="width: 65pt"><col style="width: 65pt"></colgroup>
    <tr><th>Mon<br>th</th><th>Amendment relating to<br>information furnished in S.<br>No.(select)</th><th>11A(<br>1)</th><th>11A(<br>2)</th><th>11B(<br>1)</th><th>11B(<br>2)</th></tr>
    {{#each table11_amendments}}
    <tr><td>{{month}}</td><td>{{amendment_information}}</td><td>{{select_11A1}}</td><td>{{select_11A2}}</td><td>{{select_11B1}}</td><td>{{select_11B2}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table11_amendments}}
  </table>

  <div class="section-title">12. HSN-wise summary of outward supplies</div>

  <!-- Table 12 -->
  <table class="medium">
    <colgroup><col style="width: 45pt"><col style="width: 45pt"><col style="width: 95pt"><col style="width: 45pt"><col style="width: 80pt"><col style="width: 60pt"><col style="width: 80pt"><col style="width: 80pt"><col style="width: 75pt"><col style="width: 75pt"><col style="width: 55pt"></colgroup>
    <tr><th>Sr.<br>No.</th><th>H<br>S<br>N</th><th>Descriptio<br>n</th><th>U<br>Q<br>C</th><th>Total<br>Quantit<br>y</th><th>Rat<br>e of<br>Tax</th><th>Total<br>Taxab<br>le<br>Valu<br>e</th><th colspan="4">Amount</th></tr>
    <tr><th></th><th></th><th></th><th></th><th></th><th></th><th></th><th>Integr<br>ated<br>Tax</th><th>Centra<br>l Tax</th><th>State/<br>UT<br>Tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td></tr>
    {{#each table12_hsn}}
    <tr><td>{{sr_no}}</td><td>{{hsn}}</td><td>{{description}}</td><td>{{uqc}}</td><td>{{total_quantity}}</td><td>{{rate_of_tax}}</td><td>{{total_taxable_value}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table12_hsn}}
  </table>

  <div class="section-title">13. Documents issued during the tax period</div>

  <!-- Table 13 -->
  <table class="medium">
    <colgroup><col style="width: 45pt"><col style="width: 245pt"><col style="width: 55pt"><col style="width: 55pt"><col style="width: 85pt"><col style="width: 80pt"><col style="width: 80pt"></colgroup>
    <tr><th rowspan="2">Sr.<br>No.</th><th rowspan="2">Nature of document</th><th colspan="2">Sr. No.</th><th rowspan="2">Total<br>number</th><th rowspan="2">Cancelled</th><th rowspan="2">Net issued</th></tr>
    <tr><th>From</th><th>To</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td></tr>
    {{#each table13_documents}}
    <tr><td>{{sr_no}}</td><td>{{nature_of_document}}</td><td>{{from}}</td><td>{{to}}</td><td>{{total_number}}</td><td>{{cancelled}}</td><td>{{net_issued}}</td></tr>
    {{/each}}
    <!-- If table13_documents is empty, render these statutory rows exactly: -->
    {{default_table13_rows_if_empty}}
  </table>

  <div class="section-title">14. Details of the supplies made through e-commerce operators on which e-commerce operators are liable to collect tax under section 52 of the Act or liable to pay tax u/s 9(5) [Supplier to report]</div>

  <!-- Table 14 -->
  <table class="medium">
    <colgroup><col style="width: 210pt"><col style="width: 120pt"><col style="width: 105pt"><col style="width: 80pt"><col style="width: 80pt"><col style="width: 80pt"><col style="width: 55pt"></colgroup>
    <tr><th rowspan="2">Nature of supply</th><th rowspan="2">GSTIN of e-<br>commerce<br>operator</th><th rowspan="2">Net<br>value of<br>supplies</th><th colspan="4">Tax amount</th></tr>
    <tr><th>Integrated<br>tax</th><th>Central<br>tax</th><th>State /<br>UT<br>tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td></tr>
    <tr><td>(a) Supplies on<br>which ecommerce<br>operator is<br>liable to collect tax<br>u/s 52</td><td>{{table14.collect.operator_gstin}}</td><td>{{table14.collect.net_value_of_supplies}}</td><td>{{table14.collect.integrated_tax}}</td><td>{{table14.collect.central_tax}}</td><td>{{table14.collect.state_ut_tax}}</td><td>{{table14.collect.cess}}</td></tr>
    <tr><td>(b) Supplies on<br>which ecommerce<br>operator is<br>liable to pay tax u/s<br>9(5)</td><td>{{table14.pay.operator_gstin}}</td><td>{{table14.pay.net_value_of_supplies}}</td><td>{{table14.pay.integrated_tax}}</td><td>{{table14.pay.central_tax}}</td><td>{{table14.pay.state_ut_tax}}</td><td>{{table14.pay.cess}}</td></tr>
  </table>

  <div class="section-title">14A. Amendment to details of the supplies made through e-commerce operators on which e-commerce operators are liable to collect tax<br>under section 52 of the Act or liable to pay tax u/s 9(5) [Supplier to report]</div>

  <!-- Table 14A -->
  <table class="medium">
    <colgroup><col style="width: 140pt"><col style="width: 85pt"><col style="width: 100pt"><col style="width: 115pt"><col style="width: 90pt"><col style="width: 75pt"><col style="width: 75pt"><col style="width: 75pt"><col style="width: 55pt"></colgroup>
    <tr><th rowspan="2">Nature of<br>supply</th><th colspan="2">Original details</th><th>Revised<br>details</th><th rowspan="2">Net<br>value of<br>supplies</th><th colspan="4">Tax amount</th></tr>
    <tr><th>Month<br>/<br>Quarter</th><th>GSTIN<br>of e-<br>commerc<br>e<br>operator</th><th>GSTIN of<br>ecommerce<br>operator</th><th>Integra<br>ted<br>tax</th><th>Central<br>tax</th><th>State<br>/<br>UT<br>tax</th><th>Cess</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td></tr>
    <tr><td>(a)<br>Supplies<br>on which<br>ecommerce<br>operator is<br>liable to<br>collect tax<br>u/s 52</td><td>{{table14A.collect.month_quarter}}</td><td>{{table14A.collect.operator_gstin}}</td><td>{{table14A.collect.revised_operator_gstin}}</td><td>{{table14A.collect.net_value_of_supplies}}</td><td>{{table14A.collect.integrated_tax}}</td><td>{{table14A.collect.central_tax}}</td><td>{{table14A.collect.state_ut_tax}}</td><td>{{table14A.collect.cess}}</td></tr>
    <tr><td>(b)<br>Supplies<br>on which<br>ecommerce<br>operator is<br>liable to<br>pay tax u/s<br>9(5)</td><td>{{table14A.pay.month_quarter}}</td><td>{{table14A.pay.operator_gstin}}</td><td>{{table14A.pay.revised_operator_gstin}}</td><td>{{table14A.pay.net_value_of_supplies}}</td><td>{{table14A.pay.integrated_tax}}</td><td>{{table14A.pay.central_tax}}</td><td>{{table14A.pay.state_ut_tax}}</td><td>{{table14A.pay.cess}}</td></tr>
  </table>

  <div class="section-title">15. Details of the supplies made through e-commerce operators on which e-commerce operator is liable to pay tax u/s 9(5) [e-commerce operator to report]</div>

  <!-- Table 15 -->
  <table class="medium">
    <colgroup><col style="width: 62pt"><col style="width: 70pt"><col style="width: 60pt"><col style="width: 60pt"><col style="width: 58pt"><col style="width: 58pt"><col style="width: 35pt"><col style="width: 68pt"><col style="width: 62pt"><col style="width: 55pt"><col style="width: 55pt"><col style="width: 35pt"><col style="width: 60pt"></colgroup>
    <tr><th rowspan="2">Type of<br>suppli<br>er</th><th rowspan="2">Type of<br>recipient</th><th rowspan="2">GST<br>IN<br>of<br>supp<br>lier</th><th rowspan="2">GSTI<br>N of<br>recip<br>ient</th><th rowspan="2">Docu<br>ment<br>no.</th><th rowspan="2">Docu<br>ment<br>date</th><th rowspan="2">R<br>at<br>e</th><th rowspan="2">Valu<br>e of<br>supp<br>lies<br>mad<br>e</th><th colspan="4">Tax<br>amount</th><th rowspan="2">Pla<br>ce<br>of<br>sup<br>ply</th></tr>
    <tr><th>Integra<br>ted<br>tax</th><th>Ce<br>ntra<br>l<br>tax</th><th>St<br>at<br>e /<br>UT<br>tax</th><th>C<br>e<br>s<br>s</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td></tr>
    {{#each table15}}
    <tr><td>{{type_of_supplier}}</td><td>{{type_of_recipient}}</td><td>{{supplier_gstin}}</td><td>{{recipient_gstin}}</td><td>{{document_no}}</td><td>{{document_date}}</td><td>{{rate}}</td><td>{{value_of_supplies_made}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table15}}
  </table>

  <div class="section-title">15A (I). Amendment to details of the supplies made through e-commerce operators on which e-commerce operator is liable to pay tax u/s<br>9(5) [e-commerce operator to report, for registered recipients]</div>

  <!-- Table 15A(I) -->
  <table class="medium">
    <colgroup><col style="width: 65pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 35pt"><col style="width: 65pt"><col style="width: 58pt"><col style="width: 45pt"><col style="width: 45pt"><col style="width: 35pt"><col style="width: 55pt"></colgroup>
    <tr><th rowspan="2">Type of<br>supplier</th><th colspan="4">Original details</th><th colspan="4">Revised details</th><th rowspan="2">R<br>a<br>t<br>e</th><th rowspan="2">Va<br>lue<br>of<br>su<br>ppl<br>ies<br>ma<br>de</th><th colspan="4">Tax<br>amount</th><th rowspan="2">Pl<br>ac<br>e<br>of<br>su<br>pp<br>ly</th></tr>
    <tr><th>GS<br>TI<br>N<br>of<br>sup<br>plie<br>r</th><th>GS<br>TI<br>N<br>of<br>rec<br>ipi<br>ent</th><th>Do<br>c.<br>no.</th><th>Do<br>c.<br>Da<br>te</th><th>GS<br>TI<br>N<br>of<br>su<br>ppl<br>ier</th><th>GS<br>TI<br>N<br>of<br>rec<br>ipi<br>ent</th><th>Do<br>c.<br>no.</th><th>Do<br>c.<br>Da<br>te</th><th>Integ<br>rated<br>tax</th><th>Ce<br>ntr<br>al<br>tax</th><th>S<br>ta<br>te<br>/<br>U<br>T<br>ta<br>x</th><th>C<br>e<br>ss</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td><td class="center">12</td><td class="center">13</td><td class="center">14</td><td class="center">15</td><td class="center">16</td></tr>
    {{#each table15A_registered_recipients}}
    <tr><td>{{type_of_supplier}}</td><td>{{original_supplier_gstin}}</td><td>{{original_recipient_gstin}}</td><td>{{original_doc_no}}</td><td>{{original_doc_date}}</td><td>{{revised_supplier_gstin}}</td><td>{{revised_recipient_gstin}}</td><td>{{revised_doc_no}}</td><td>{{revised_doc_date}}</td><td>{{rate}}</td><td>{{value_of_supplies_made}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table15A_registered_recipients}}
  </table>

  <div class="section-title">15A (II). Amendment to details of the supplies made through e-commerce operators on which ecommerce operator is liable to pay tax u/s 9(5) [e-commerce operator to report, for unregistered recipients]</div>

  <!-- Table 15A(II) -->
  <table class="medium">
    <colgroup><col style="width: 75pt"><col style="width: 75pt"><col style="width: 75pt"><col style="width: 75pt"><col style="width: 45pt"><col style="width: 85pt"><col style="width: 80pt"><col style="width: 65pt"><col style="width: 65pt"><col style="width: 45pt"><col style="width: 65pt"></colgroup>
    <tr><th rowspan="2">Type<br>supplier<br>of</th><th colspan="2">Original<br>details</th><th>Revise<br>d<br>details</th><th rowspan="2">Rat<br>e</th><th rowspan="2">Value<br>of<br>supplie<br>s<br>made</th><th colspan="4">Tax<br>amount</th><th rowspan="2">Place<br>of<br>suppl<br>y</th></tr>
    <tr><th>GSTI<br>N of<br>suppli<br>er</th><th>Tax<br>perio<br>d</th><th>GSTIN<br>of<br>supplie<br>r</th><th>Integrate<br>d tax</th><th>Centr<br>al<br>tax</th><th>Stat<br>e /<br>UT<br>tax</th><th>Ce<br>ss</th></tr>
    <tr><td class="center">1</td><td class="center">2</td><td class="center">3</td><td class="center">4</td><td class="center">5</td><td class="center">6</td><td class="center">7</td><td class="center">8</td><td class="center">9</td><td class="center">10</td><td class="center">11</td></tr>
    {{#each table15A_unregistered_recipients}}
    <tr><td>{{type_of_supplier}}</td><td>{{original_supplier_gstin}}</td><td>{{tax_period}}</td><td>{{revised_supplier_gstin}}</td><td>{{rate}}</td><td>{{value_of_supplies_made}}</td><td>{{integrated_tax}}</td><td>{{central_tax}}</td><td>{{state_ut_tax}}</td><td>{{cess}}</td><td>{{place_of_supply}}</td></tr>
    {{/each}}
    {{blank_rows_if_empty_table15A_unregistered_recipients}}
  </table>

  <div class="instructions">
    <p class="bold">Instructions for filing of GSTR-1A:</p>

    <p>1. It is an additional facility provided to add any particulars of current tax period missed out in reporting in FORM GSTR-1 of current tax period or amend any particulars already declared FORM GSTR-1 of current tax period (including those declared in IFF, for the first and second months of a quarter, if any,for quarterly taxpayers)The form is an optional form without levy of late fees.</p>

    <p>2. The FORM will be available on the portal after due date of filing of FORM GSTR -1 or the actual date of filing of FORM GSTR -1 ,whichever is later, till filing of corresponding FORM GSTR-3B of the same tax period. Similarly, for quarterly taxpayers, the FORM GSTR-1A shall be opened quarterly after filing of the FORM GSTR-1 (Quarterly) or the due date of filing of FORM GSTR -1 ( Quaterly),whichever is later, till filing of FORM GSTR-3B of the same tax period.</p>

    <p>3. The particulars declared in FORM GSTR-1A along with particulars declared in FORM GSTR-1 shall be made available in FORM GSTR-3B. In case of taxpayers opting for filing of quarterly returns the same shall be made available in FORM GSTR-3B (Quarterly) along with particular furnished in FORM GSTR-1 and IFF of Month M1 and M2 (if filed).</p>

    <p>4. Amendment of a document which is related to change of Recipient‘s GSTIN shall not be allowed in GSTR-1A.</p>

    <p>5. In addition to the GSTR-2B already generated, GSTR-2B shall also consist of all the supplies declared by the respective suppliers in GSTR-1A. However, supplies declared or amended in FORM GSTR-1A shall be made available in the next open FORM GSTR-2B. For example,</p>

    <p>(i) a supplier issues two invoices INV1 and INV2 in the month of January 2023. Then he furnished the details of the invoice INV1 on 8th Feb 2023 in FORM GSTR-1. However, he misses one invoice INV2 and furnishes the details of the same in FORM GSTR-1A on 15th Feb 2023. In this case, INV1 will go to the FORM GSTR-2B of the recipient for the month of January made available on 14th Feb 2023. Further, INV2 will be made available in FORM GSTR-2B of the recipient for the month of February made available on 14th March 2023.</p>

    <p>(ii) a supplier issues two invoices INV3 and INV4 in the month of January 2023. Then he furnished the details of the invoice INV3 on 15th Feb 2023 in FORM GSTR-1. However, he declared INV 4 in FORM GSTR-1A on 16th Feb 2023. In this case, both INV3 and INV4 will be made available in FORM GSTR-2B of the recipient for the month of February made available on 14th March 2023.</p>

    <p>6. Instructions for specific tables:-</p>

    <table class="instruction-table">
      <colgroup><col style="width: 180pt"><col style="width: 540pt"></colgroup>
      <tr><th>Table No.</th><th>Instructions</th></tr>
      <tr>
        <td>4A, 4B, 5, 6, 9B (for<br>registered recipients)</td>
        <td>Taxpayers may declare additional details of invoices /<br>documents for the current tax period other than those<br>already declared in FORM GSTR-1.</td>
      </tr>
      <tr>
        <td>7</td>
        <td>• Taxpayers may declare additional details of invoices/<br>documents for the current tax period other than those<br>already declared in FORM GSTR-1.<br>• In case a POS with any combination of rate has<br>already been declared in FORM GSTR-1, then a new<br>rate cannot be added through Table 7 and the taxpayer<br>will have to use amendment facility in Table 10 for the<br>same.</td>
      </tr>
      <tr>
        <td>8,</td>
        <td>Taxpayers may declare additional details of Nil rated,<br>Exempted and Non-GST supplies for the current tax<br>period other than those already declared in FORM<br>GSTR-1.</td>
      </tr>
      <tr>
        <td>9A and 9C</td>
        <td>Amendment of values reported in table 4A, 4B, 5,<br>6A, 6B 6C and 9B in IFF, for the first and second<br>months of a quarter, if any, and FORM GSTR-1<br>of the current tax period.</td>
      </tr>
      <tr>
        <td>12</td>
        <td>HSN details as per additional/amendments details<br>reported in FORM GSTR 1A shall be declared<br>here. In case of any downward amendment, entry<br>can be made with the minus sign for the<br>differential part.</td>
      </tr>
      <tr>
        <td>11A(1) &amp; 11A(2), 11B(1) &amp;<br>11B(2)</td>
        <td>• Taxpayers may declare details of advances received or<br>adjusted for the current tax period other than those<br>already declared in FORM GSTR-1.<br>• In case a POS with any combination of rate has<br>already been declared in FORM GSTR-1, then a new<br>rate cannot be added through these tables and the<br>taxpayer will have to use amendment Table 11(II) as<br>the case may be.</td>
      </tr>
      <tr>
        <td>14</td>
        <td>Taxpayers may declare additional details of supplies<br>made through e-commerce operator for the current tax<br>period</td>
      </tr>
      <tr>
        <td>15</td>
        <td>• ECO Taxpayers may declare additional details of<br>supplies for unregistered recipients (rate wise) for the<br>current tax period other than those already declared in<br>FORM GSTR-1.</td>
      </tr>
      <tr>
        <td>10, 11(II), 14A, 15A(I),<br>15A(II)</td>
        <td>• Taxpayers may amend details already declared in<br>FORM GSTR1 of the current period.‖.</td>
      </tr>
    </table>
  </div>

</div>
~~~

---

## 6. Default Rows for Table 13

If `table13_documents` is empty, render the following statutory document rows exactly.

~~~html
<tr><td class="center">1</td><td>Invoices for outward<br>supply</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">2</td><td>Invoices for inward supply<br>from unregistered person</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">3</td><td>Revised Invoice</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">4</td><td>Debit Note</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">5</td><td>Credit Note</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">6</td><td>Receipt voucher</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">7</td><td>Payment Voucher</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">8</td><td>Refund voucher</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">9</td><td>Delivery Challan for job<br>work</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">10</td><td>Delivery Challan for<br>supply on<br>approval</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">11</td><td>Delivery Challan in case<br>of liquid gas</td><td></td><td></td><td></td><td></td><td></td></tr>
<tr><td class="center">12</td><td>Delivery Challan in cases<br>other than by way of<br>supply (excluding at S no.<br>9 to 11)</td><td></td><td></td><td></td><td></td><td></td></tr>
~~~

---

## 7. Variable-Entry Handling Rules

1. Every table section using `{{#each ...}}` is dynamic.
2. Do not restrict entries to the blank rows visible in the source PDF.
3. If a section has zero entries, keep one blank bordered row.
4. If a section has many rows, continue vertically and repeat the table header when pagination is used.
5. For exact single-page recreation, expand the custom long page height if needed rather than shrinking text below legibility.
6. Long GSTINs, invoice numbers, document numbers, HSN codes, and descriptions must wrap within the cell.
7. Numeric amount fields should be right-aligned if populated.
8. Keep all statutory section labels exactly in the same order: 1 to 15A(II), followed by Instructions.
9. Do not merge GSTR-1 wording into GSTR-1A. GSTR-1A uses **current tax period** language and includes Tables **14, 14A, 15, 15A(I), 15A(II)**.
10. Preserve the one-page long-form character of the source PDF unless the final renderer requires A4 pagination.

---

## 8. Final AI Instruction Block

Copy this instruction into the AI that will generate the final document:

~~~text
Recreate FORM GSTR-1A exactly as per this Markdown/HTML specification. Use the same statutory wording, table order, compact layout, merged headers, black borders, Times New Roman/Liberation Serif font, and dynamic row handling. Treat all data-entry tables as arrays. If a table has no entries, render one blank bordered row. If entries exceed the visible blank area, continue vertically and repeat the relevant header if paginating. Preserve Tables 14, 14A, 15, 15A(I), and 15A(II). Do not redesign, simplify, modernize, add colour, add logos, or convert this into a plain text form.
~~~
