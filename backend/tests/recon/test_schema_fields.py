from app.recon.schema_fields import (
    component_columns,
    alias_index_for,
    fields_for_module,
    missing_required_for_module,
    required_fields_for_module,
    suggest_map,
)


def test_flattened_headers_map_leaf_aliases_and_supplier_name():
    headers = [
        "GSTIN of Supplier",
        "Trade/Legal name",
        "Invoice Details / Invoice number",
        "Invoice Details / Invoice date",
        "Invoice Details / Invoice value",
    ]
    mapping = suggest_map(headers, "gstr2b")
    assert mapping["supplier_name"] == "Trade/Legal name"
    assert mapping["doc_no"] == "Invoice Details / Invoice number"
    assert mapping["doc_date"] == "Invoice Details / Invoice date"
    assert mapping["invoice"] == "Invoice Details / Invoice value"


def test_flattened_tax_component_uses_leaf_alias():
    assert component_columns(["Tax Details / IGST amount"]) == {"igst": 0}


def test_tax_group_parent_is_not_mistaken_for_combined_tax_column():
    mapping = suggest_map(["Tax Amount / Integrated Tax"], "gstr2b")
    assert mapping["tax"] is None


def test_ims_inward_requires_identity_and_invoice_value():
    assert required_fields_for_module("ims_inward") == (
        "supplier_gstin", "doc_type", "doc_no", "invoice",
    )
    mapping = {
        "supplier_gstin": "GSTIN",
        "doc_type": "Type",
        "doc_no": "Invoice Number",
        "doc_date": None,
        "invoice": "Invoice Value",
        "taxable": None,
        "tax": None,
    }
    assert missing_required_for_module(mapping, "ims_inward") == []


def test_gstr2b_required_fields_are_unchanged():
    mapping = {"supplier_gstin": "GSTIN", "doc_type": "Type", "doc_no": "Number"}
    assert missing_required_for_module(mapping, "gstr2b") == ["doc_date", "invoice"]


def test_ims_inward_mapping_is_not_the_gstr2b_mapping():
    fields = fields_for_module("ims_inward")
    assert fields == (
        "supplier_gstin", "supplier_name", "doc_type", "doc_no", "invoice", "tax",
    )
    assert "doc_date" not in fields
    assert "taxable" not in fields
    assert "ims_status" not in fields
    assert alias_index_for("ims_inward")["taxable value"] == "taxable"
    suggestion = suggest_map(["Taxable Value", "Invoice Number"], "ims_inward")
    assert "taxable" not in suggestion
