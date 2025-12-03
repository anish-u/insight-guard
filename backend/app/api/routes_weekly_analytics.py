from fastapi import APIRouter, Depends, HTTPException, Query
from neo4j import Driver
from neo4j.time import DateTime

from ..neo4j_client import driver_dependency

router = APIRouter(prefix="/weekly-dhs", tags=["weekly-dhs-analytics"])

def _to_iso(value):
  """Convert Neo4j DateTime (or Python datetime) to ISO string, else None/str."""
  if value is None:
    return None
  # Neo4j DateTime has .to_native()
  if isinstance(value, DateTime):
    return value.to_native().isoformat()
  # Already a Python datetime?
  try:
    return value.isoformat()
  except AttributeError:
    return str(value)

@router.get("/scans")
def list_weekly_scans(driver: Driver = Depends(driver_dependency)):
  """
  List all Weekly DHS scans (newest first)
  """
  with driver.session() as session:
    records = session.run(
      """
      MATCH (s:WeeklyDHSScan)
      RETURN s.scan_id AS scan_id,
        s.year AS year,
        s.month AS month,
        s.week_index AS week_index,
        s.scan_date AS scan_date
      ORDER BY s.scan_date DESC, s.year DESC, s.month DESC, s.week_index DESC
      """
    )
    scans = []
    for r in records:
      scans.append(
        {
          "scan_id": r["scan_id"],
          "year": r.get("year"),
          "month": r.get("month"),
          "week_index": r.get("week_index"),
          "scan_date": _to_iso(r.get("scan_date")),
        }
      )
    
    return {"items": scans}


@router.get("/{scan_id}/summary")
def weekly_summary(scan_id: str, driver: Driver = Depends(driver_dependency)):
  """
  KPI summary for a specific Weekly DHS scan
  """
  with driver.session() as session:
    scan = session.run(
      "MATCH (s:WeeklyDHSScan { scan_id: $scan_id }) RETURN s",
      scan_id=scan_id,
    ).single()
    if not scan:
      raise HTTPException(status_code=404, detail="WeeklyDHSScan not found")

    summary_rec = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      OPTIONAL MATCH (h:WeeklyDHSHost)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
      OPTIONAL MATCH (o)-[:WEEKLY_DHS_OF_VULNERABILITY]->(v:WeeklyDHSVulnerability)
      RETURN
        count(o) AS total_observations,
        sum(CASE WHEN o.severity_at_scan = 5 THEN 1 ELSE 0 END) AS critical,
        sum(CASE WHEN o.severity_at_scan = 4 THEN 1 ELSE 0 END) AS high,
        count(DISTINCT h) AS host_count,
        count(DISTINCT v) AS vuln_count,
        sum(CASE WHEN v.known_exploited = true THEN 1 ELSE 0 END) AS known_exploited_count,
        sum(CASE WHEN v.ransomware_exploited = true THEN 1 ELSE 0 END) AS ransomware_exploited_count
      """,
      scan_id=scan_id,
    ).single()

    s = scan["s"]
    raw_scan_date = s.get("scan_date")

    return {
      "scan": {
        "scan_id": s["scan_id"],
        "year": s.get("year"),
        "month": s.get("month"),
        "week_index": s.get("week_index"),
        "scan_date": _to_iso(raw_scan_date),
     },
      "summary": {
        "total_observations": summary_rec["total_observations"] or 0,
        "critical": summary_rec["critical"] or 0,
        "high": summary_rec["high"] or 0,
        "host_count": summary_rec["host_count"] or 0,
        "vuln_count": summary_rec["vuln_count"] or 0,
        "known_exploited_count": summary_rec["known_exploited_count"] or 0,
        "ransomware_exploited_count": summary_rec["ransomware_exploited_count"] or 0,
      },
    }


@router.get("/{scan_id}/charts")
def weekly_charts(
  scan_id: str,
  min_severity: int | None = Query(None, ge=1, le=5),
  driver: Driver = Depends(driver_dependency),
):
  """
  Aggregated chart data for a Weekly DHS scan:
  - severity buckets
  - top hosts
  - top vulnerabilities
  """
  with driver.session() as session:
    # severity buckets
    severity_records = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      WHERE $min_severity IS NULL OR o.severity_at_scan >= $min_severity
      RETURN o.severity_at_scan AS severity, count(*) AS count
      ORDER BY severity DESC
      """,
      scan_id=scan_id,
      min_severity=min_severity,
    )
    severity_buckets = [
      {"severity": r["severity"], "count": r["count"]}
      for r in severity_records
    ]

    # top hosts
    host_records = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      MATCH (h:WeeklyDHSHost)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
      WHERE $min_severity IS NULL OR o.severity_at_scan >= $min_severity
      RETURN h.ip AS ip,
        h.hostname AS hostname,
        count(o) AS findings,
        sum(CASE WHEN o.severity_at_scan = 5 THEN 1 ELSE 0 END) AS critical
      ORDER BY findings DESC
      LIMIT 10
      """,
      scan_id=scan_id,
      min_severity=min_severity,
    )
    top_hosts = [
      {
        "ip": r["ip"],
        "hostname": r["hostname"],
        "findings": r["findings"],
        "critical": r["critical"],
      }
      for r in host_records
    ]

    # top vulnerabilities
    vuln_records = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      MATCH (o)-[:WEEKLY_DHS_OF_VULNERABILITY]->(v:WeeklyDHSVulnerability)
      WHERE $min_severity IS NULL OR o.severity_at_scan >= $min_severity
      RETURN v.weekly_vuln_id AS weekly_vuln_id,
        v.plugin_id AS plugin_id,
        v.name AS name,
        v.severity AS severity,
        v.cvss_base_score AS cvss,
        v.known_exploited AS known_exploited,
        v.ransomware_exploited AS ransomware_exploited,
        count(o) AS findings
      ORDER BY findings DESC
      LIMIT 10
      """,
      scan_id=scan_id,
      min_severity=min_severity,
    )
    top_vulns = [
      {
        "weekly_vuln_id": r["weekly_vuln_id"],
        "plugin_id": r["plugin_id"],
        "name": r["name"],
        "severity": r["severity"],
        "cvss": r["cvss"],
        "known_exploited": bool(r["known_exploited"])
        if r["known_exploited"] is not None
        else False,
        "ransomware_exploited": bool(r["ransomware_exploited"])
        if r["ransomware_exploited"] is not None
        else False,
        "findings": r["findings"],
      }
      for r in vuln_records
    ]

    return {
      "severity_buckets": severity_buckets,
      "top_hosts": top_hosts,
      "top_vulns": top_vulns,
    }


@router.get("/{scan_id}/findings")
def weekly_findings(
  scan_id: str,
  min_severity: int | None = Query(None, ge=1, le=5),
  search: str | None = Query(None),
  offset: int = Query(0, ge=0),
  limit: int = Query(50, ge=1, le=200),
  driver: Driver = Depends(driver_dependency),
):
  """
  Paginated findings table for a Weekly DHS scan
  Filters:
    - min_severity
    - search (ip / hostname / vuln name / plugin id)
  """
  with driver.session() as session:
    # total count
    count_rec = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      MATCH (h:WeeklyDHSHost)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
      MATCH (o)-[:WEEKLY_DHS_OF_VULNERABILITY]->(v:WeeklyDHSVulnerability)
      WHERE ($min_severity IS NULL OR o.severity_at_scan >= $min_severity)
        AND ($search IS NULL OR
          toLower(h.ip) CONTAINS toLower($search) OR
          toLower(coalesce(h.hostname, "")) CONTAINS toLower($search) OR
          toLower(coalesce(v.name, "")) CONTAINS toLower($search) OR
          toString(v.plugin_id) CONTAINS $search)
      RETURN count(DISTINCT o) AS total
      """,
      scan_id=scan_id,
      min_severity=min_severity,
      search=search,
    ).single()
    total = count_rec["total"] or 0

    # page data
    records = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      MATCH (h:WeeklyDHSHost)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
      MATCH (o)-[:WEEKLY_DHS_OF_VULNERABILITY]->(v:WeeklyDHSVulnerability)
      WHERE ($min_severity IS NULL OR o.severity_at_scan >= $min_severity)
        AND ($search IS NULL OR
          toLower(h.ip) CONTAINS toLower($search) OR
          toLower(coalesce(h.hostname, "")) CONTAINS toLower($search) OR
          toLower(coalesce(v.name, "")) CONTAINS toLower($search) OR
          toString(v.plugin_id) CONTAINS $search)
      RETURN
        o.obs_id AS obs_id,
        o.severity_at_scan AS severity,
        o.cvss_at_scan AS cvss,
        o.first_seen AS first_seen,
        o.last_seen AS last_seen,
        o.age_days AS age_days,
        h.ip AS ip,
        h.hostname AS hostname,
        v.plugin_id AS plugin_id,
        v.name AS vuln_name,
        v.known_exploited AS known_exploited,
        v.ransomware_exploited AS ransomware_exploited
      ORDER BY severity DESC, age_days DESC
      SKIP $offset
      LIMIT $limit
      """,
      scan_id=scan_id,
      min_severity=min_severity,
      search=search,
      offset=offset,
      limit=limit,
    )

    items = []
    for r in records:
      raw_first = r.get("first_seen")
      raw_last = r.get("last_seen")

      items.append(
        {
          "obs_id": r["obs_id"],
          "severity": r["severity"],
          "cvss": r["cvss"],
          "first_seen": _to_iso(raw_first),
          "last_seen": _to_iso(raw_last),
          "age_days": r.get("age_days"),
          "ip": r["ip"],
          "hostname": r.get("hostname"),
          "plugin_id": r.get("plugin_id"),
          "vuln_name": r.get("vuln_name"),
          "known_exploited": bool(r["known_exploited"])
          if r["known_exploited"] is not None
          else False,
          "ransomware_exploited": bool(r["ransomware_exploited"])
          if r["ransomware_exploited"] is not None
          else False,
        }
      )

    return {
      "total": total,
      "items": items,
      "offset": offset,
      "limit": limit,
    }


@router.get("/{scan_id}/graph")
def weekly_graph(scan_id: str, driver: Driver = Depends(driver_dependency)):
  """
  Graph data for a specific Weekly DHS scan –
  reuse pattern from /dashboard/weekly-latest but parameterized by scan_id.
  """
  MAX_OBS = 80

  def _dedup_node(nodes: dict, node_id: str, label: str, ntype: str, extra=None):
    if node_id in nodes:
      return
    base = {"id": node_id, "label": label, "type": ntype}
    if extra:
      base.update(extra)
    nodes[node_id] = base

  def _dedup_link(links: dict, source: str, target: str, ltype: str):
    key = f"{source}->{target}:{ltype}"
    if key in links:
      return
    links[key] = {"source": source, "target": target, "type": ltype}

  with driver.session() as session:
    scan_rec = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      RETURN s
      """,
      scan_id=scan_id,
    ).single()
    if not scan_rec:
      raise HTTPException(status_code=404, detail="WeeklyDHSScan not found")

    s = scan_rec["s"]

    records = session.run(
      """
      MATCH (s:WeeklyDHSScan { scan_id: $scan_id })
      MATCH (o:WeeklyDHSObservation)-[:WEEKLY_DHS_FOUND_IN]->(s)
      WITH s, o
      ORDER BY o.severity_at_scan DESC
      LIMIT $max_obs
      OPTIONAL MATCH (h:WeeklyDHSHost)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
      OPTIONAL MATCH (svc:WeeklyDHSService)-[:WEEKLY_DHS_HAS_OBSERVATION]->(o)
      OPTIONAL MATCH (o)-[:WEEKLY_DHS_OF_VULNERABILITY]->(v:WeeklyDHSVulnerability)
      RETURN s, o, h, svc, v
      """,
      scan_id=scan_id,
      max_obs=MAX_OBS,
    )

    nodes: dict[str, dict] = {}
    links: dict[str, dict] = {}
    obs_count = 0
    host_ids: set[str] = set()
    vuln_ids: set[str] = set()

    _dedup_node(
      nodes,
      scan_id,
      label=scan_id,
      ntype="weekly_scan",
      extra={
          "year": s.get("year"),
          "month": s.get("month"),
          "week_index": s.get("week_index"),
      },
    )

    for rec in records:
      o = rec["o"]
      if not o:
        continue
      obs_count += 1
      obs_id = o["obs_id"]

      _dedup_node(
        nodes,
        obs_id,
        label=f"Obs {obs_id}",
        ntype="weekly_observation",
        extra={
          "severity": o.get("severity_at_scan"),
          "cvss": o.get("cvss_at_scan"),
        },
      )
      _dedup_link(links, obs_id, scan_id, "WEEKLY_DHS_FOUND_IN")

      h = rec["h"]
      if h:
        host_id = h["ip"]
        host_ids.add(host_id)
        _dedup_node(
          nodes,
          host_id,
          label=h.get("hostname") or host_id,
          ntype="weekly_host",
        )
        _dedup_link(links, host_id, obs_id, "WEEKLY_DHS_HAS_OBSERVATION")

      svc = rec["svc"]
      if svc:
        svc_id = svc["service_id"]
        _dedup_node(
          nodes,
          svc_id,
          label=svc_id,
          ntype="weekly_service",
        )
        if h:
          _dedup_link(links, h["ip"], svc_id, "WEEKLY_DHS_RUNS")
        _dedup_link(links, svc_id, obs_id, "WEEKLY_DHS_HAS_OBSERVATION")

      v = rec["v"]
      if v:
        vid = v["weekly_vuln_id"]
        vuln_ids.add(vid)
        _dedup_node(
          nodes,
          vid,
          label=v.get("name") or f"Vuln {vid}",
          ntype="weekly_vuln",
          extra={
            "severity": v.get("severity"),
            "cvss": v.get("cvss_base_score"),
            },
        )
        _dedup_link(links, obs_id, vid, "WEEKLY_DHS_OF_VULNERABILITY")

      return {
        "scan_id": scan_id,
        "summary": {
          "observation_count": obs_count,
          "host_count": len(host_ids),
          "vuln_count": len(vuln_ids),
          "node_count": len(nodes),
          "link_count": len(links),
        },
        "graph": {
          "nodes": list(nodes.values()),
          "links": list(links.values()),
        },
      }
