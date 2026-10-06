from property_parser import PropertyDocument, build_record


def test_build_record_keeps_property_workflow_fields():
    record = build_record(
        {
            "fields": {
                "name": "Asha Patel",
                "unit": "4B",
                "maintenance_requests": ["leaking tap"],
                "tenant_documents": ["proof_of_income.pdf"],
                "inspection_reminders": ["annual gas check"],
            }
        }
    )
    assert record.tenant_name == "Asha Patel"
    assert record.unit == "4B"
    assert record.maintenance_requests == ["leaking tap"]
    assert record.tenant_documents == ["proof_of_income.pdf"]
    assert record.inspection_reminders == ["annual gas check"]


def test_document_defaults_to_pdf_name():
    assert PropertyDocument(b"%PDF").source_name == "document.pdf"


def test_build_record_from_parsed_page_text():
    record = build_record({"text_per_page": [
        "Tenant Name: Asha Patel\nUnit: 4B\nMaintenance Requests:\n- leaking tap",
        "Tenant Documents:\n- proof_of_income.pdf\nInspection Reminders:\n- annual gas check",
    ]})
    assert record.tenant_name == "Asha Patel"
    assert record.unit == "4B"
    assert record.maintenance_requests == ["leaking tap"]
    assert record.tenant_documents == ["proof_of_income.pdf"]
    assert record.inspection_reminders == ["annual gas check"]
