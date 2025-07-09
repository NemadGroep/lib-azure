import os
import json
import pytest
from decimal import Decimal
from lib_azure.ai_document_intelligence import FormRecognizer

@pytest.fixture
def result():
    result = os.getenv("RESULT")
    if not result:
        pytest.skip("No RESULT found")
    try:
        return json.loads(result)
    except json.JSONDecodeError as e:
        pytest.exit(f"Invalid JSON in RESULT: {e}")

@pytest.fixture
def locale():
    return "de_DE"

@pytest.fixture
def form():
    return FormRecognizer()
    
def test_print_result(form, result):
    form.print_result(result)

def test_processing_pipe(form, result, locale):
    result_w_numbers = form.parse_numbers(result, locale)
    result_w_numbers_n_dates = form.parse_dates(result_w_numbers)

    kv_pairs = form.extract_kv_pairs(result_w_numbers_n_dates)
    assert isinstance(kv_pairs, dict)

    date = kv_pairs.get("Invoice_date")
    assert isinstance(date, str)
    assert date == "20250425"

    material_list = kv_pairs.get("Material_list")
    assert isinstance(material_list, list)
    assert len(material_list)==1

    material_list_line = material_list[0]
    assert len(material_list_line.keys()) == 3
    assert material_list_line.get("Material_number_vendor") == "5.001"
    assert material_list_line.get("Purchase_order_line") == "4500132616"

    qty = material_list_line.get("Quantity")
    assert isinstance(qty, Decimal)
    assert qty == Decimal("12.00")
