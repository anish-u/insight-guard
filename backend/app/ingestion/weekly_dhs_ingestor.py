from datetime import date, datetime, timezone
from pathlib import Path
import csv
import io
from neo4j import Driver

from .storage import build_upload_path


def _parse_bool(value: str | bool | None) -> bool | None:
  if isinstance(value, bool):
    return value
  
  if value is None:
    return None
  
  v = str(value).strip().lower()
  
  if v in ("true", "t", "yes", "1"):
    return True
  
  if v in ("false", "f", "no", "0"):
    return False
  
  return None


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


def _parse_iso_dt(value: str | None) -> datetime | None:
  if not value:
    return None
  
  try:
    return datetime.fromisoformat(value)
  except Exception:
    return None


def ingest_weekly_dhs_scan(
  driver: Driver,
  file_bytes: bytes,
  filename: str,
  year: int,
  month: int,
  week_index: int,
) -> dict:
  """
  Store the weekly DHS CSV file, create/merge WeeklyDHSScan,
  and ingest row-level host/service/vuln/observation nodes.
  """
  upload_path: Path = build_upload_path(
    report_type="weekly_dhs",
    year=year,
    month=month,
    week_index=week_index,
  )

  # overwrite existing file
  upload_path.write_bytes(file_bytes)

  scan_id = f"weekly_dhs_{year:04d}_{month:02d}_wk{week_index}"
  scan_date = date(year=year, month=month, day=1)
  now = datetime.now(timezone.utc)

  with driver.session() as session:
    # 1) create/merge scan node
    session.run(
      """
      MERGE (s:WeeklyDHSScan { scan_id: $scan_id })
      ON CREATE SET
        s.year = $year,
        s.month = $month,
        s.week_index = $week_index,
        s.scan_date = $scan_date,
        s.source_file = $source_file,
        s.created_at = $now,
        s.updated_at = $now
      ON MATCH SET
        s.year = $year,
        s.month = $month,
        s.week_index = $week_index,
        s.scan_date = $scan_date,
        s.source_file = $source_file,
        s.updated_at = $now
      """,
      scan_id=scan_id,
      year=year,
      month=month,
      week_index=week_index,
      scan_date=scan_date,
      source_file=str(upload_path),
      now=now,
    )

    # 2) parse CSV and ingest each row
    text_stream = io.StringIO(file_bytes.decode("utf-8-sig"))
    reader = csv.DictReader(text_stream)

    for row in reader:
      ip = row.get("ip", "").strip()
      if not ip:
        continue

      hostname = row.get("Hostname", "").strip() or None
      port = _parse_int(row.get("port"))
      protocol = row.get("protocol", "").strip() or None
      plugin_id = _parse_int(row.get("plugin_id"))
      if plugin_id is None:
        continue

      severity = _parse_int(row.get("severity")) or 0
      known_exploited = _parse_bool(row.get("known_exploited"))
      ransomware_exploited = _parse_bool(row.get("ransomware_exploited"))
      cvss_base_score = _parse_float(row.get("cvss_base_score"))
      cvss_version = row.get("cvss_version")
      if isinstance(cvss_version, str):
        cvss_version = cvss_version.strip() or None

      initial_detection = _parse_iso_dt(row.get("initial_detection"))
      latest_detection = _parse_iso_dt(row.get("latest_detection"))
      age_days = _parse_int(row.get("age_days"))

      name = (row.get("name") or "").strip()
      description = (row.get("description") or "").strip() or None
      solution = (row.get("solution") or "").strip() or None
      source = (row.get("source") or "").strip() or "dhs_weekly"

      service_id = (
        f"{ip}:{port}/{protocol}"
        if port is not None and protocol
        else f"{ip}:unknown"
      )
      weekly_vuln_id = f"weekly:{plugin_id}"
      obs_id = f"{scan_id}:{ip}:{service_id}:{plugin_id}"

      # 1) Host, service, vulnerability
      session.run(
        """
        // Host
        MERGE (h:WeeklyDHSHost { ip: $ip })
        ON CREATE SET
          h.hostname = $hostname,
          h.first_seen = coalesce($initial_detection, $now),
          h.created_at = $now
        ON MATCH SET
          h.hostname = coalesce($hostname, h.hostname),
          h.last_seen = coalesce($latest_detection, $now)

        // Service
        MERGE (svc:WeeklyDHSService { service_id: $service_id })
        ON CREATE SET
          svc.ip = $ip,
          svc.port = $port,
          svc.protocol = $protocol,
          svc.created_at = $now

        MERGE (h)-[:WEEKLY_DHS_RUNS]->(svc)

        // Vulnerability
        MERGE (v:WeeklyDHSVulnerability { weekly_vuln_id: $weekly_vuln_id })
        ON CREATE SET
          v.plugin_id = $plugin_id,
          v.name = $name,
          v.severity = $severity,
          v.cvss_base_score = $cvss_base_score,
          v.cvss_version = $cvss_version,
          v.known_exploited = $known_exploited,
          v.ransomware_exploited = $ransomware_exploited,
          v.description = $description,
          v.solution = $solution,
          v.source = $source,
          v.created_at = $now,
          v.updated_at = $now
        ON MATCH SET
          v.name = $name,
          v.severity = $severity,
          v.cvss_base_score = $cvss_base_score,
          v.cvss_version = $cvss_version,
          v.known_exploited = $known_exploited,
          v.ransomware_exploited = $ransomware_exploited,
          v.description = $description,
          v.solution = $solution,
          v.source = $source,
          v.updated_at = $now
        """,
        ip=ip,
        hostname=hostname,
        port=port,
        protocol=protocol,
        service_id=service_id,
        weekly_vuln_id=weekly_vuln_id,
        plugin_id=plugin_id,
        name=name,
        severity=severity,
        cvss_base_score=cvss_base_score,
        cvss_version=cvss_version,
        known_exploited=known_exploited,
        ransomware_exploited=ransomware_exploited,
        description=description,
        solution=solution,
        source=source,
        initial_detection=initial_detection,
        latest_detection=latest_detection,
        now=now,
      )

      # 2) Observation + relationships to scan
      session.run(
        """
        MATCH (h:WeeklyDHSHost { ip: $ip })
        MATCH (svc:WeeklyDHSService { service_id: $service_id })
        MATCH (v:WeeklyDHSVulnerability { weekly_vuln_id: $weekly_vuln_id })
        MATCH (scan:WeeklyDHSScan { scan_id: $scan_id })

        MERGE (o:WeeklyDHSObservation { obs_id: $obs_id })
        ON CREATE SET
          o.plugin_id = $plugin_id,
          o.ip = $ip,
          o.service_id = $service_id,
          o.severity_at_scan = $severity,
          o.cvss_at_scan = $cvss_base_score,
          o.first_seen = coalesce($initial_detection, $now),
          o.last_seen = coalesce($latest_detection, $now),
          o.age_days = $age_days,
          o.status = "open",
          o.created_at = $now,
          o.updated_at = $now
        ON MATCH SET
          o.severity_at_scan = $severity,
          o.cvss_at_scan = $cvss_base_score,
          o.last_seen = coalesce($latest_detection, $now),
          o.age_days = $age_days,
          o.updated_at = $now

        MERGE (h)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
        MERGE (svc)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
        MERGE (o)-[:WEEKLY_DHS_OF_VULNERABILITY]->(v)
        MERGE (o)-[:WEEKLY_DHS_FOUND_IN]->(scan)
        """,
        ip=ip,
        service_id=service_id,
        weekly_vuln_id=weekly_vuln_id,
        plugin_id=plugin_id,
        severity=severity,
        cvss_base_score=cvss_base_score,
        initial_detection=initial_detection,
        latest_detection=latest_detection,
        age_days=age_days,
        scan_id=scan_id,
        obs_id=obs_id,
        now=now,
      )

  return {
    "scan_id": scan_id,
    "stored_at": str(upload_path),
    "year": year,
    "month": month,
    "week_index": week_index,
  }
