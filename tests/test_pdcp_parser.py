import pytest

from pdcp_parser import (
    PdcpBearerType,
    PdcpContext,
    PdcpControlPduType,
    PdcpParseError,
    PdcpRat,
    parse_pdcp_pdu,
)


def test_parse_nr_drb_18bit_data_pdu():
    ctx = PdcpContext(PdcpRat.NR, PdcpBearerType.DRB, 18)
    # SN=0x2AAAA => split over bytes with D/C set
    pdu = bytes([0xD5, 0x55, 0x40, 0xDE, 0xAD])
    out = parse_pdcp_pdu(pdu, ctx)
    assert out.is_control is False
    assert out.sn == 0x2AAAA
    assert out.payload == b"\xDE\xAD"


def test_parse_nr_srb_12bit_data_pdu():
    ctx = PdcpContext(PdcpRat.NR, PdcpBearerType.SRB, 12)
    pdu = bytes([0x8A, 0xBC, 0x01])
    out = parse_pdcp_pdu(pdu, ctx)
    assert out.sn == 0xABC
    assert out.payload == b"\x01"


def test_parse_status_report_18bit():
    ctx = PdcpContext(PdcpRat.NR, PdcpBearerType.DRB, 18)
    # control/status type (0), FMC=0x2ABCD
    pdu = bytes([0x0A, 0xAF, 0x34, 0xFF, 0x00])
    out = parse_pdcp_pdu(pdu, ctx)
    assert out.is_control is True
    assert out.control_type == PdcpControlPduType.STATUS_REPORT
    assert out.status_report is not None
    assert out.status_report.fmc == 0x2ABCD
    assert out.status_report.bitmap == b"\xFF\x00"


def test_invalid_sn_profile_rejected():
    ctx = PdcpContext(PdcpRat.NR, PdcpBearerType.DRB, 15)
    with pytest.raises(PdcpParseError):
        parse_pdcp_pdu(b"\x80", ctx)
