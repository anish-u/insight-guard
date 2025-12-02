from datetime import date, datetime, timezone
from pathlib import Path
import csv
import io
from neo4j import Driver

from .storage import build_upload_path, sanitize_dept


def _parse_int(value: str | None) -> int | None:
  if value is None or str(value).strip() == "":
    return None
  try:
    return int(float(value))
  except Exception:
    return None


def ingest_dept_scan(
  driver: Driver,
  file_bytes: bytes,
  filename: str,
  year: int,
  month: int,
  department: str,
) -> dict:
  upload_path: Path = build_upload_path(
    report_type="dept_scan",
    year=year,
    month=month,
    department=department,
  )

  upload_path.write_bytes(file_bytes)

  dept_slug = sanitize_dept(department)
  scan_id = f"dept_scan_{dept_slug}_{year:04d}_{month:02d}"
  scan_date = date(year=year, month=month, day=1)
  now = datetime.now(timezone.utc)

  with driver.session() as session:
    # 1) Department + scan
    session.run(
      """
      MERGE (d:DeptScanDepartment { dept_id: $dept_id })
      ON CREATE SET
        d.name = $dept_name,
        d.created_at = $now
      ON MATCH SET
        d.name = coalesce($dept_name, d.name)

      MERGE (s:DeptScanScan { scan_id: $scan_id })
      ON CREATE SET
        s.dept_id = $dept_id,
        s.scan_date = $scan_date,
        s.source_file = $source_file,
        s.created_at = $now,
        s.updated_at = $now
      ON MATCH SET
        s.dept_id = $dept_id,
        s.scan_date = $scan_date,
        s.source_file = $source_file,
        s.updated_at = $now

      MERGE (s)-[:DEPT_SCAN_FOR_DEPARTMENT]->(d)
      """,
      dept_id=dept_slug,
      dept_name=department,
      scan_id=scan_id,
      scan_date=scan_date,
      source_file=str(upload_path),
      now=now,
    )

    # 2) parse per-row
    text_stream = io.StringIO(file_bytes.decode("utf-8-sig"))
    reader = csv.DictReader(text_stream)

    for row in reader:
      ip = (row.get("IP") or "").strip()
      if not ip:
        continue

      dns = (row.get("DNS") or "").strip() or None
      netbios = (row.get("NetBIOS") or "").strip() or None
      os_name = (row.get("OS") or "").strip() or None
      ip_status = (row.get("IP Status") or "").strip() or None

      qid = (row.get("QID") or "").strip()
      if not qid:
        continue

      title = (row.get("Title") or "").strip()
      vtype = (row.get("Type") or "").strip() or None
      severity = _parse_int(row.get("Severity")) or 0
      port = _parse_int(row.get("Port"))
      protocol = (row.get("Protocol") or "").strip() or None
      ssl = (row.get("SSL") or "").strip() or None
      cve_id = (row.get("CVE ID") or "").strip() or None
      vendor_ref = (row.get("Vendor Reference") or "").strip() or None
      bugtraq_id = (row.get("Bugtraq ID") or "").strip() or None
      threat = (row.get("Threat") or "").strip() or None
      impact = (row.get("Impact") or "").strip() or None
      solution = (row.get("Solution") or "").strip() or None
      exploitability = (row.get("Exploitability") or "").strip() or None
      assoc_malware = (row.get("Associated Malware") or "").strip() or None
      pci_vuln = (row.get("PCI Vuln") or "").strip() or None
      instance = (row.get("Instance") or "").strip() or None
      category = (row.get("Category") or "").strip() or None

      host_id = f"{dept_slug}:{ip}"
      service_id = (
        f"{host_id}:{port}/{protocol}"
        if port is not None and protocol
        else f"{host_id}:no-port"
      )
      dept_vuln_id = f"dept:{qid}"
      obs_id = f"{scan_id}:{host_id}:{qid}:{instance or '0'}"

      # 1) Host, dept, service, vulnerability
      session.run(
        """
        // Host
        MERGE (h:DeptScanHost { host_id: $host_id })
        ON CREATE SET
          h.ip = $ip,
          h.dns = $dns,
          h.netbios = $netbios,
          h.os_name = $os_name,
          h.ip_status = $ip_status,
          h.created_at = $now
        ON MATCH SET
          h.dns = coalesce($dns, h.dns),
          h.netbios = coalesce($netbios, h.netbios),
          h.os_name = coalesce($os_name, h.os_name),
          h.ip_status = coalesce($ip_status, h.ip_status)

        MERGE (d:DeptScanDepartment { dept_id: $dept_id })
        MERGE (d)-[:DEPT_SCAN_OWNS_HOST]->(h)

        // Service
        MERGE (svc:DeptScanService { service_id: $service_id })
        ON CREATE SET
          svc.ip = $ip,
          svc.port = $port,
          svc.protocol = $protocol,
          svc.ssl = $ssl,
          svc.created_at = $now

        MERGE (h)-[:DEPT_SCAN_RUNS]->(svc)

        // Vulnerability
        MERGE (v:DeptScanVulnerability { dept_vuln_id: $dept_vuln_id })
        ON CREATE SET
          v.qid = $qid,
          v.title = $title,
          v.type = $vtype,
          v.severity = $severity,
          v.cve_id = $cve_id,
          v.vendor_reference = $vendor_ref,
          v.bugtraq_id = $bugtraq_id,
          v.threat = $threat,
          v.impact = $impact,
          v.solution = $solution,
          v.exploitability = $exploitability,
          v.associated_malware = $assoc_malware,
          v.pci_vuln = $pci_vuln,
          v.category = $category,
          v.created_at = $now,
          v.updated_at = $now
        ON MATCH SET
          v.title = $title,
          v.type = $vtype,
          v.severity = $severity,
          v.cve_id = $cve_id,
          v.vendor_reference = $vendor_ref,
          v.bugtraq_id = $bugtraq_id,
          v.threat = $threat,
          v.impact = $impact,
          v.solution = $solution,
          v.exploitability = $exploitability,
          v.associated_malware = $assoc_malware,
          v.pci_vuln = $pci_vuln,
          v.category = $category,
          v.updated_at = $now
        """,
        dept_id=dept_slug,
        host_id=host_id,
        ip=ip,
        dns=dns,
        netbios=netbios,
        os_name=os_name,
        ip_status=ip_status,
        service_id=service_id,
        port=port,
        protocol=protocol,
        ssl=ssl,
        dept_vuln_id=dept_vuln_id,
        qid=qid,
        title=title,
        vtype=vtype,
        severity=severity,
        cve_id=cve_id,
        vendor_ref=vendor_ref,
        bugtraq_id=bugtraq_id,
        threat=threat,
        impact=impact,
        solution=solution,
        exploitability=exploitability,
        assoc_malware=assoc_malware,
        pci_vuln=pci_vuln,
        category=category,
        now=now,
      )


      # 2) Observation + relationships
      session.run(
        """
        MATCH (h:DeptScanHost { host_id: $host_id })
        MATCH (svc:DeptScanService { service_id: $service_id })
        MATCH (v:DeptScanVulnerability { dept_vuln_id: $dept_vuln_id })
        MATCH (scan:DeptScanScan { scan_id: $scan_id })

        MERGE (o:DeptScanObservation { obs_id: $obs_id })
        ON CREATE SET
          o.qid = $qid,
          o.host_id = $host_id,
          o.service_id = $service_id,
          o.instance = $instance,
          o.severity_at_scan = $severity,
          o.status = "open",
          o.created_at = $now,
          o.updated_at = $now
        ON MATCH SET
          o.severity_at_scan = $severity,
          o.instance = $instance,
          o.updated_at = $now

        MERGE (h)-[:DEPT_SCAN_HAS_OBSERVATION]->(o)
        MERGE (svc)-[:DEPT_SCAN_HAS_OBSERVATION]->(o)
        MERGE (o)-[:DEPT_SCAN_OF_VULNERABILITY]->(v)
        MERGE (o)-[:DEPT_SCAN_FOUND_IN]->(scan)
        """,
        host_id=host_id,
        service_id=service_id,
        dept_vuln_id=dept_vuln_id,
        scan_id=scan_id,
        obs_id=obs_id,
        qid=qid,
        instance=instance,
        severity=severity,
        now=now,
      )


  return {
    "scan_id": scan_id,
    "stored_at": str(upload_path),
    "year": year,
    "month": month,
    "department": department,
    "dept_id": dept_slug,
  }
