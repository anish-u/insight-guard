from datetime import date, datetime, timezone
from pathlib import Path
import csv
import io
from neo4j import Driver

from .storage import build_upload_path


def _parse_float(value: str | None) -> float | None:
  if value is None or str(value).strip() == "":
    return None
  try:
    return float(value)
  except Exception:
    return None


def _parse_int(value: str | None) -> int | None:
  if value is None or str(value).strip() == "":
    return None
  try:
    return int(float(value))
  except Exception:
    return None


def _parse_web_dt(value: str | None) -> datetime | None:
  """
  Example from Qualys-like report: '06 Jul 2024 02:01AM GMT'
  """
  if not value:
    return None
  v = value.strip()
  try:
    return datetime.strptime(v, "%d %b %Y %I:%M%p GMT").replace(
      tzinfo=timezone.utc
    )
  except Exception:
    return None


def ingest_monthly_dhs_web_scan(
  driver: Driver,
  file_bytes: bytes,
  filename: str,
  year: int,
  month: int,
) -> dict:
  """
  Ingest Monthly DHS Web App scan:

  - One MonthlyDHSWebScan per (year, month)
  - One MonthlyDHSWebApp per web application
  - One MonthlyDHSWebVulnerability per QID
  - Many MonthlyDHSWebObservation attached directly to the app
    (no separate endpoint node; URL is just a property).
  """
  upload_path: Path = build_upload_path(
    report_type="monthly_dhs_web",
    year=year,
    month=month,
  )

  upload_path.write_bytes(file_bytes)

  scan_id = f"monthly_dhs_web_{year:04d}_{month:02d}"
  scan_date = date(year=year, month=month, day=1)
  now = datetime.now(timezone.utc)

  with driver.session() as session:
    # 1) Scan node
    session.run(
      """
      MERGE (s:MonthlyDHSWebScan { scan_id: $scan_id })
      ON CREATE SET
        s.year = $year,
        s.month = $month,
        s.scan_date = $scan_date,
        s.source_file = $source_file,
        s.created_at = $now,
        s.updated_at = $now
      ON MATCH SET
        s.year = $year,
        s.month = $month,
        s.scan_date = $scan_date,
        s.source_file = $source_file,
        s.updated_at = $now
      """,
      scan_id=scan_id,
      year=year,
      month=month,
      scan_date=scan_date,
      source_file=str(upload_path),
      now=now,
    )

    # 2) parse rows – all observations hang directly off the app
    text_stream = io.StringIO(file_bytes.decode("utf-8-sig"))
    reader = csv.DictReader(text_stream)

    for row_idx, row in enumerate(reader, start=1):
      qid = (row.get("QID") or "").strip()
      if not qid:
        continue

      name = (row.get("NAME") or "").strip()
      vuln_id = (row.get("VULN_ID") or "").strip() or None
      severity = _parse_int(row.get("SEVERITY")) or 0
      base_cvss = _parse_float(row.get("BASE CVSS"))
      cwe = (row.get("CWE") or "").strip() or None
      cve = (row.get("CVE") or "").strip() or None
      group_name = (row.get("GROUP") or "").strip() or None
      webapp = (row.get("WEB APPLICATION") or "").strip()
      url = (row.get("URL") or "").strip() or "/"
      description = (row.get("DESCRIPTION") or "").strip() or None
      impact = (row.get("IMPACT") or "").strip() or None
      solution = (row.get("SOLUTION") or "").strip() or None
      vuln_type = (row.get("VULN TYPE") or "").strip() or None

      first_det = _parse_web_dt(row.get("FIRST DETECTION"))
      last_det = _parse_web_dt(row.get("LAST DETECTION"))

      # Single app node per web application
      app_id = f"app:{webapp}" if webapp else "app:unknown"
      web_vuln_id = f"monthly_web:{qid}"

      # Observation id – include row index so multiple rows for same QID/app are distinct
      obs_id = f"{scan_id}:{app_id}:{qid}:{row_idx}"

      # 1) App + Vulnerability
      session.run(
        """
        MERGE (app:MonthlyDHSWebApp { app_id: $app_id })
        ON CREATE SET
          app.name = $app_name,
          app.base_url = $webapp,
          app.created_at = $now
        ON MATCH SET
          app.base_url = coalesce($webapp, app.base_url)

        MERGE (v:MonthlyDHSWebVulnerability { web_vuln_id: $web_vuln_id })
        ON CREATE SET
          v.qid = $qid,
          v.vuln_id = $vuln_id,
          v.name = $name,
          v.severity = $severity,
          v.base_cvss = $base_cvss,
          v.cwe = $cwe,
          v.cve = $cve,
          v.group_name = $group_name,
          v.description = $description,
          v.impact = $impact,
          v.solution = $solution,
          v.vuln_type = $vuln_type,
          v.created_at = $now,
          v.updated_at = $now
        ON MATCH SET
          v.name = $name,
          v.severity = $severity,
          v.base_cvss = $base_cvss,
          v.cwe = $cwe,
          v.cve = $cve,
          v.group_name = $group_name,
          v.description = $description,
          v.impact = $impact,
          v.solution = $solution,
          v.vuln_type = $vuln_type,
          v.updated_at = $now
        """,
        app_id=app_id,
        app_name=webapp or "Unknown App",
        webapp=webapp or None,
        web_vuln_id=web_vuln_id,
        qid=qid,
        vuln_id=vuln_id,
        name=name,
        severity=severity,
        base_cvss=base_cvss,
        cwe=cwe,
        cve=cve,
        group_name=group_name,
        description=description,
        impact=impact,
        solution=solution,
        vuln_type=vuln_type,
        now=now,
      )

      # 2) Observation + relationships (app, vuln, scan)
      session.run(
        """
        MATCH (app:MonthlyDHSWebApp { app_id: $app_id })
        MATCH (v:MonthlyDHSWebVulnerability { web_vuln_id: $web_vuln_id })
        MATCH (scan:MonthlyDHSWebScan { scan_id: $scan_id })

        MERGE (o:MonthlyDHSWebObservation { obs_id: $obs_id })
        ON CREATE SET
          o.qid = $qid,
          o.app_id = $app_id,
          o.url = $url,
          o.severity_at_scan = $severity,
          o.base_cvss_at_scan = $base_cvss,
          o.first_seen = coalesce($first_det, $now),
          o.last_seen = coalesce($last_det, $now),
          o.status = "open",
          o.created_at = $now,
          o.updated_at = $now
        ON MATCH SET
          o.url = $url,
          o.severity_at_scan = $severity,
          o.base_cvss_at_scan = $base_cvss,
          o.last_seen = coalesce($last_det, $now),
          o.updated_at = $now

        MERGE (app)-[:MONTHLY_DHS_WEB_HAS_OBSERVATION]->(o)
        MERGE (o)-[:MONTHLY_DHS_WEB_OF_VULNERABILITY]->(v)
        MERGE (o)-[:MONTHLY_DHS_WEB_FOUND_IN]->(scan)
        """,
        app_id=app_id,
        web_vuln_id=web_vuln_id,
        scan_id=scan_id,
        obs_id=obs_id,
        qid=qid,
        url=url,
        severity=severity,
        base_cvss=base_cvss,
        first_det=first_det,
        last_det=last_det,
        now=now,
      )

  return {
    "scan_id": scan_id,
    "stored_at": str(upload_path),
    "year": year,
    "month": month,
  }
