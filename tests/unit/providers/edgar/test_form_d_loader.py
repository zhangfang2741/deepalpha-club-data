import pytest
from deepalpha.infrastructure.providers.edgar.form_d_loader import _parse_business_desc


def test_parse_business_desc_extracts_text():
    xml = """<?xml version="1.0"?>
<edgarSubmission>
  <offeringData>
    <businessDescription>AI inference platform using MCP protocol and HBM memory</businessDescription>
  </offeringData>
</edgarSubmission>"""
    desc = _parse_business_desc(xml)
    assert "MCP" in desc
    assert "HBM" in desc


def test_parse_business_desc_missing_tag_returns_empty():
    xml = "<edgarSubmission><offeringData></offeringData></edgarSubmission>"
    assert _parse_business_desc(xml) == ""


def test_parse_business_desc_malformed_xml_returns_empty():
    assert _parse_business_desc("not xml at all <<<") == ""
