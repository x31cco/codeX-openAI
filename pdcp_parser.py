from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class PdcpRat(Enum):
    LTE = "lte"
    NR = "nr"


class PdcpBearerType(Enum):
    SRB = "srb"
    DRB = "drb"


class PdcpControlPduType(Enum):
    STATUS_REPORT = 0b000
    ROHC_FEEDBACK = 0b001
    EHC_FEEDBACK = 0b010


@dataclass(frozen=True)
class PdcpContext:
    rat: PdcpRat
    bearer_type: PdcpBearerType
    sn_bits: int


@dataclass(frozen=True)
class PdcpStatusReport:
    fmc: int
    bitmap: bytes


@dataclass(frozen=True)
class PdcpPdu:
    is_control: bool
    sn: Optional[int]
    control_type: Optional[PdcpControlPduType]
    status_report: Optional[PdcpStatusReport]
    payload: bytes


class PdcpParseError(ValueError):
    pass


_VALID_SN_BITS = {
    (PdcpRat.LTE, PdcpBearerType.SRB): {5},
    (PdcpRat.LTE, PdcpBearerType.DRB): {7, 12, 15},
    (PdcpRat.NR, PdcpBearerType.SRB): {12},
    (PdcpRat.NR, PdcpBearerType.DRB): {12, 18},
}


def validate_context(ctx: PdcpContext) -> None:
    allowed = _VALID_SN_BITS[(ctx.rat, ctx.bearer_type)]
    if ctx.sn_bits not in allowed:
        raise PdcpParseError(
            f"sn_bits={ctx.sn_bits} is invalid for {ctx.rat.value}/{ctx.bearer_type.value}; allowed={sorted(allowed)}"
        )


def parse_pdcp_pdu(data: bytes, ctx: PdcpContext) -> PdcpPdu:
    """Parse a PDCP PDU with Rel-18 aware SN profiles.

    This parser is transport-agnostic and intended for integration in Wireshark dissectors.
    """
    validate_context(ctx)

    if not data:
        raise PdcpParseError("empty PDU")

    first = data[0]

    # D/C bit (1=data, 0=control) for both LTE and NR PDCP user plane.
    is_data_pdu = (first & 0x80) != 0

    if is_data_pdu:
        sn, header_len = _parse_data_header(data, ctx.sn_bits)
        return PdcpPdu(
            is_control=False,
            sn=sn,
            control_type=None,
            status_report=None,
            payload=data[header_len:],
        )

    control_type = PdcpControlPduType((first >> 4) & 0x07)

    if control_type is PdcpControlPduType.STATUS_REPORT:
        status_report, header_len = _parse_status_report(data, ctx)
        return PdcpPdu(
            is_control=True,
            sn=None,
            control_type=control_type,
            status_report=status_report,
            payload=data[header_len:],
        )

    # For feedback control PDUs, keep raw payload for upper-layer decode.
    return PdcpPdu(
        is_control=True,
        sn=None,
        control_type=control_type,
        status_report=None,
        payload=data[1:],
    )


def _parse_data_header(data: bytes, sn_bits: int) -> tuple[int, int]:
    if sn_bits <= 8:
        if len(data) < 1:
            raise PdcpParseError("truncated data PDU header")
        mask = (1 << sn_bits) - 1
        return data[0] & mask, 1

    if sn_bits <= 16:
        if len(data) < 2:
            raise PdcpParseError("truncated data PDU header")
        raw = (data[0] << 8) | data[1]
        mask = (1 << sn_bits) - 1
        return raw & mask, 2

    # 18-bit SN profile (NR DRB)
    if sn_bits == 18:
        if len(data) < 3:
            raise PdcpParseError("truncated 18-bit SN data PDU header")
        # First byte: D/C + 7 MSBs of SN.
        # Next bytes carry remaining SN bits.
        sn = ((data[0] & 0x7F) << 11) | (data[1] << 3) | ((data[2] >> 5) & 0x07)
        return sn, 3

    raise PdcpParseError(f"unsupported sn_bits={sn_bits}")


def _parse_status_report(data: bytes, ctx: PdcpContext) -> tuple[PdcpStatusReport, int]:
    sn_bits = ctx.sn_bits
    # Byte0: D/C=0 + type + reserved, then FMC starts.
    if sn_bits <= 12:
        if len(data) < 3:
            raise PdcpParseError("truncated status report")
        fmc = ((data[0] & 0x0F) << 8) | data[1]
        bitmap = data[2:]
        return PdcpStatusReport(fmc=fmc, bitmap=bitmap), 2

    if sn_bits == 18:
        if len(data) < 4:
            raise PdcpParseError("truncated 18-bit status report")
        fmc = ((data[0] & 0x0F) << 14) | (data[1] << 6) | ((data[2] >> 2) & 0x3F)
        bitmap = data[3:]
        return PdcpStatusReport(fmc=fmc, bitmap=bitmap), 3

    raise PdcpParseError(f"unsupported status report sn_bits={sn_bits}")
