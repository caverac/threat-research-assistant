"""OT threat intelligence domain enumerations."""

from enum import Enum


class Protocol(str, Enum):
    """ICS/OT communication protocols."""

    MODBUS = "modbus"
    DNP3 = "dnp3"
    OPCUA = "opc-ua"
    ETHERNET_IP = "ethernet-ip"
    PROFINET = "profinet"
    BACNET = "bacnet"
    IEC_61850 = "iec-61850"
    IEC_104 = "iec-104"


class AssetType(str, Enum):
    """ICS/OT asset types."""

    PLC = "plc"
    RTU = "rtu"
    HMI = "hmi"
    SCADA = "scada"
    DCS = "dcs"
    HISTORIAN = "historian"
    ENGINEERING_WORKSTATION = "engineering-workstation"
    SAFETY_SYSTEM = "safety-system"


class Severity(str, Enum):
    """Advisory severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ThreatCategory(str, Enum):
    """Threat intelligence categories."""

    RANSOMWARE = "ransomware"
    APT = "apt"
    SUPPLY_CHAIN = "supply-chain"
    INSIDER = "insider"
    VULNERABILITY = "vulnerability"
