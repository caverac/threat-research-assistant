"""Generate synthetic OT threat intelligence data for development and testing."""

from __future__ import annotations

import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from core.enums import AssetType, Protocol, Severity, ThreatCategory
from core.schemas import Advisory, AffectedProduct, Incident, ThreatReport

_VENDORS = [
    ("Siemens", ["SIMATIC S7-1500", "SIMATIC S7-1200", "SIMATIC S7-300", "SINUMERIK 840D", "SCALANCE X200"]),
    ("Schneider Electric", ["Modicon M340", "Modicon M580", "Modicon Premium", "EcoStruxure Control Expert", "PowerLogic PM8000"]),
    ("Rockwell Automation", ["ControlLogix 5580", "CompactLogix 5380", "MicroLogix 1400", "FactoryTalk View SE", "PowerFlex 755T"]),
    ("ABB", ["AC500 PLC", "Symphony Plus", "Ability 800xA", "REF615 Relay", "ACS880 Drive"]),
    ("Honeywell", ["ControlEdge PLC", "Experion PKS", "Safety Manager SC", "C300 Controller", "HC900 Controller"]),
    ("Emerson", ["DeltaV DCS", "ROC800 RTU", "AMS Device Manager", "Ovation DCS", "DeltaV SIS"]),
    ("GE Vernova", ["Mark VIe Controller", "PACSystems RX3i", "UR Relays", "OpShield", "CIMPLICITY HMI"]),
    ("Yokogawa", ["CENTUM VP DCS", "ProSafe-RS SIS", "STARDOM RTU", "FA-M3V PLC", "FAST/TOOLS SCADA"]),
    ("Mitsubishi Electric", ["MELSEC iQ-R", "MELSEC iQ-F", "GOT2000 HMI", "CC-Link IE", "GENESIS64 SCADA"]),
    ("Phoenix Contact", ["PLCnext Control", "mGuard Firewall", "FL SWITCH", "RFC 470S", "ILC 2050 BI"]),
]

_THREAT_ACTORS = ["VOLTZITE", "KAMACITE", "ELECTRUM", "COVELLITE", "XENOTIME", "CHRYSENE", "MAGNALLIUM", "DYMALLOY", "RASPITE", "WASSONITE"]

_SECTORS = ["energy", "water", "manufacturing", "oil-and-gas", "chemical", "transportation", "pharmaceuticals", "food-and-beverage"]

_ATTACK_TECHNIQUES = [
    ("T0800", "Activate Firmware Update Mode"),
    ("T0831", "Manipulation of Control"),
    ("T0855", "Unauthorized Command Message"),
    ("T0836", "Modify Parameter"),
    ("T0839", "Module Firmware"),
    ("T0821", "Modify Controller Tasking"),
    ("T0843", "Program Download"),
    ("T0809", "Data Destruction"),
    ("T0813", "Denial of Control"),
    ("T0826", "Loss of Availability"),
    ("T0827", "Loss of Control"),
    ("T0828", "Loss of Productivity and Revenue"),
    ("T0837", "Loss of Protection"),
    ("T0880", "Loss of Safety"),
    ("T0829", "Loss of View"),
    ("T0856", "Spoof Reporting Message"),
    ("T0862", "Supply Chain Compromise"),
    ("T0860", "Wireless Compromise"),
    ("T0866", "Exploitation of Remote Services"),
    ("T0886", "Remote Services"),
]

_VULN_TYPES = [
    "buffer overflow",
    "authentication bypass",
    "hard-coded credentials",
    "improper input validation",
    "path traversal",
    "command injection",
    "integer overflow",
    "use-after-free",
    "uncontrolled resource consumption",
    "improper access control",
    "cleartext transmission of sensitive data",
    "cross-site scripting",
    "SQL injection",
    "deserialization of untrusted data",
    "stack-based buffer overflow",
]


def _random_date(start_year: int = 2022, end_year: int = 2024) -> datetime:
    start = datetime(start_year, 1, 1, tzinfo=timezone.utc)
    end = datetime(end_year, 12, 31, tzinfo=timezone.utc)
    delta = end - start
    random_days = random.randint(0, delta.days)
    return start + timedelta(days=random_days)


def generate_advisories(count: int = 50) -> list[Advisory]:
    """Generate synthetic ICS advisories."""
    advisories: list[Advisory] = []
    for i in range(1, count + 1):
        vendor, products = random.choice(_VENDORS)
        product = random.choice(products)
        vuln_type = random.choice(_VULN_TYPES)
        severity = random.choice(list(Severity))
        protocols = random.sample(list(Protocol), k=random.randint(1, 3))
        published = _random_date()

        advisory = Advisory(
            id=f"ICSA-{published.year}-{i:03d}",
            title=f"{vendor} {product} {vuln_type.title()}",
            published=published,
            severity=severity,
            affected_products=[
                AffectedProduct(
                    vendor=vendor,
                    product=product,
                    version=f"<{random.randint(1, 10)}.{random.randint(0, 9)}.{random.randint(0, 9)}",
                )
            ],
            protocols=protocols,
            cve_ids=[f"CVE-{published.year}-{random.randint(10000, 99999)}" for _ in range(random.randint(1, 3))],
            description=(
                f"A {vuln_type} vulnerability exists in {vendor} {product}. "
                f"Successful exploitation of this vulnerability could allow an attacker to "
                f"{'execute arbitrary code' if severity in (Severity.CRITICAL, Severity.HIGH) else 'cause a denial of service condition'} "
                f"on the affected device. The vulnerability affects {', '.join(p.value for p in protocols)} communication."
            ),
            mitigations=[
                f"Update {product} to the latest firmware version",
                "Minimize network exposure for all control system devices",
                f"Implement network segmentation to isolate {', '.join(p.value for p in protocols)} traffic",
                "Use VPN for remote access to control system networks",
                "Monitor network traffic for anomalous activity",
            ],
            source=random.choice(["ICS-CERT", "vendor", "CISA"]),
        )
        advisories.append(advisory)
    return advisories


def generate_threat_reports(count: int = 30) -> list[ThreatReport]:
    """Generate synthetic threat intelligence reports."""
    reports: list[ThreatReport] = []
    for i in range(1, count + 1):
        actor = random.choice(_THREAT_ACTORS)
        category = random.choice(list(ThreatCategory))
        targets = random.sample(list(AssetType), k=random.randint(1, 4))
        protocols = random.sample(list(Protocol), k=random.randint(1, 3))
        ttps = [t[0] for t in random.sample(_ATTACK_TECHNIQUES, k=random.randint(2, 6))]
        published = _random_date()
        sector = random.choice(_SECTORS)

        summary = (
            f"{'APT group' if category == ThreatCategory.APT else category.value.title()} activity attributed to {actor} "
            f"has been observed targeting {sector} sector infrastructure. "
            f"The campaign focuses on {', '.join(t.value for t in targets[:2])} assets using "
            f"{', '.join(p.value for p in protocols[:2])} protocols."
        )
        content = (
            f"{summary}\n\n"
            f"## Campaign Overview\n\n"
            f"{actor} has been conducting operations against {sector} sector organizations since "
            f"{published.strftime('%B %Y')}. The threat actor demonstrates deep knowledge of industrial control "
            f"systems and operational technology environments.\n\n"
            f"## Technical Details\n\n"
            f"The attack chain begins with initial access through spear-phishing emails targeting OT engineers. "
            f"After establishing a foothold in the IT network, the actor performs lateral movement to reach the "
            f"OT network. Key techniques observed include:\n\n"
            + "\n".join(f"- {t[0]}: {t[1]}" for t in _ATTACK_TECHNIQUES if t[0] in ttps)
            + f"\n\n## Impact Assessment\n\n"
            f"The campaign poses a significant risk to {sector} sector operations. Successful compromise "
            f"could result in manipulation of {', '.join(t.value for t in targets)} systems, potentially "
            f"causing physical damage or safety incidents.\n\n"
            f"## Recommendations\n\n"
            f"Organizations in the {sector} sector should review their OT network segmentation, "
            f"monitor for anomalous {', '.join(p.value for p in protocols)} traffic, and ensure "
            f"all industrial control systems are updated to the latest firmware versions."
        )

        report = ThreatReport(
            id=f"TR-{published.year}-{i:03d}",
            title=f"{actor} Campaign Targeting {sector.title()} Sector {targets[0].value.upper()} Systems",
            published=published,
            threat_category=category,
            actor=actor if category == ThreatCategory.APT else None,
            targets=targets,
            protocols=protocols,
            ttps=ttps,
            summary=summary,
            content=content,
            iocs=[f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(1, 254)}" for _ in range(random.randint(2, 5))]
            + [f"{''.join(random.choices('abcdef0123456789', k=64))}" for _ in range(random.randint(1, 3))],
        )
        reports.append(report)
    return reports


def generate_incidents(count: int = 20, advisory_ids: list[str] | None = None) -> list[Incident]:
    """Generate synthetic incident records."""
    incidents: list[Incident] = []
    available_advisory_ids = advisory_ids or []

    for i in range(1, count + 1):
        sector = random.choice(_SECTORS)
        asset_types = random.sample(list(AssetType), k=random.randint(1, 3))
        protocols = random.sample(list(Protocol), k=random.randint(1, 2))
        reported = _random_date()

        related = random.sample(available_advisory_ids, k=min(random.randint(0, 2), len(available_advisory_ids))) if available_advisory_ids else []

        impact_options = [
            f"Temporary shutdown of {asset_types[0].value.upper()} systems for {random.randint(1, 48)} hours",
            f"Loss of visibility into {sector} operations for {random.randint(1, 12)} hours",
            f"Unauthorized modification of {asset_types[0].value.upper()} parameters detected and reversed",
            f"Production disruption affecting {random.randint(1, 5)} facilities for {random.randint(1, 72)} hours",
            f"Safety system {random.choice(['triggered', 'bypassed', 'disabled'])} requiring manual intervention",
        ]

        incident = Incident(
            id=f"INC-{reported.year}-{i:03d}",
            reported=reported,
            sector=sector,
            asset_types=asset_types,
            protocols=protocols,
            description=(
                f"{'Unauthorized access' if random.random() > 0.5 else 'Anomalous activity'} detected in "
                f"{sector} sector {asset_types[0].value.upper()} system. "
                f"Investigation revealed {'malware' if random.random() > 0.5 else 'suspicious network traffic'} "
                f"affecting {', '.join(p.value for p in protocols)} communications."
            ),
            impact=random.choice(impact_options),
            related_advisory_ids=related,
        )
        incidents.append(incident)
    return incidents


def generate_all(data_dir: Path) -> None:
    """Generate all synthetic data and write to disk."""
    random.seed(42)

    advisories = generate_advisories(50)
    reports = generate_threat_reports(30)
    advisory_ids = [a.id for a in advisories]
    incidents = generate_incidents(20, advisory_ids)

    advisory_dir = data_dir / "advisories"
    report_dir = data_dir / "threat_reports"
    incident_dir = data_dir / "incidents"

    for d in [advisory_dir, report_dir, incident_dir]:
        d.mkdir(parents=True, exist_ok=True)

    for advisory in advisories:
        path = advisory_dir / f"{advisory.id}.json"
        path.write_text(advisory.model_dump_json(indent=2))

    for report in reports:
        path = report_dir / f"{report.id}.json"
        path.write_text(report.model_dump_json(indent=2))

    for incident in incidents:
        path = incident_dir / f"{incident.id}.json"
        path.write_text(incident.model_dump_json(indent=2))
