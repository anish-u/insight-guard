from fastapi import APIRouter, Depends, HTTPException
from neo4j import Driver

from ..neo4j_client import driver_dependency

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

MAX_OBS = 50  # limit observations per scan so graphs stay small


def _dedup_node(nodes: dict, node_id: str, label: str, ntype: str, extra: dict | None = None):
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


@router.get("/weekly-latest")
def weekly_latest(driver: Driver = Depends(driver_dependency)):
    """
    Latest Weekly DHS scan: small graph of Host -> Service -> Observation -> Vuln -> Scan
    """
    with driver.session() as session:
        # get latest scan
        scan_record = session.run(
            """
            MATCH (s:WeeklyDHSScan)
            WITH s ORDER BY s.scan_date DESC, s.year DESC, s.month DESC, s.week_index DESC
            LIMIT 1
            RETURN s
            """
        ).single()

        if not scan_record:
            raise HTTPException(status_code=404, detail="No WeeklyDHSScan found")

        s = scan_record["s"]
        scan_id = s["scan_id"]

        # sample observations + related nodes
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

        # scan node
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

            # observation node
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

            # host
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

            # service
            svc = rec["svc"]
            if svc:
                svc_id = svc["service_id"]
                _dedup_node(
                    nodes,
                    svc_id,
                    label=svc_id,
                    ntype="weekly_service",
                )
                # host -> service
                if h:
                    _dedup_link(links, h["ip"], svc_id, "WEEKLY_DHS_RUNS")
                # service -> observation
                _dedup_link(links, svc_id, obs_id, "WEEKLY_DHS_HAS_OBSERVATION")

            # vulnerability
            v = rec["v"]
            if v:
                vid = v["weekly_vuln_id"]
                vuln_ids.add(vid)
                _dedup_node(
                    nodes,
                    vid,
                    label=v.get("name") or f"Vuln {vid}",
                    ntype="weekly_vuln",
                    extra={"severity": v.get("severity"), "cvss": v.get("cvss_base_score")},
                )
                _dedup_link(links, obs_id, vid, "WEEKLY_DHS_OF_VULNERABILITY")

        return {
            "scan_id": scan_id,
            "year": s.get("year"),
            "month": s.get("month"),
            "week_index": s.get("week_index"),
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


@router.get("/monthly-web-latest")
def monthly_web_latest(driver: Driver = Depends(driver_dependency)):
    """
    Latest Monthly DHS Web scan: App -> Observation -> Vuln -> Scan
    """
    with driver.session() as session:
        scan_record = session.run(
            """
            MATCH (s:MonthlyDHSWebScan)
            WITH s ORDER BY s.scan_date DESC, s.year DESC, s.month DESC
            LIMIT 1
            RETURN s
            """
        ).single()

        if not scan_record:
            raise HTTPException(status_code=404, detail="No MonthlyDHSWebScan found")

        s = scan_record["s"]
        scan_id = s["scan_id"]

        records = session.run(
            """
            MATCH (s:MonthlyDHSWebScan { scan_id: $scan_id })
            MATCH (o:MonthlyDHSWebObservation)-[:MONTHLY_DHS_WEB_FOUND_IN]->(s)
            WITH s, o
            ORDER BY o.severity_at_scan DESC
            LIMIT $max_obs
            OPTIONAL MATCH (app:MonthlyDHSWebApp)-[:MONTHLY_DHS_WEB_HAS_OBSERVATION]->(o)
            OPTIONAL MATCH (o)-[:MONTHLY_DHS_WEB_OF_VULNERABILITY]->(v:MonthlyDHSWebVulnerability)
            RETURN s, o, app, v
            """,
            scan_id=scan_id,
            max_obs=MAX_OBS,
        )

        nodes: dict[str, dict] = {}
        links: dict[str, dict] = {}
        obs_count = 0
        app_ids: set[str] = set()
        vuln_ids: set[str] = set()

        _dedup_node(
            nodes,
            scan_id,
            label=scan_id,
            ntype="monthly_web_scan",
            extra={"year": s.get("year"), "month": s.get("month")},
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
                ntype="monthly_web_observation",
                extra={
                    "severity": o.get("severity_at_scan"),
                    "cvss": o.get("base_cvss_at_scan"),
                    "url": o.get("url"),
                },
            )
            _dedup_link(links, obs_id, scan_id, "MONTHLY_DHS_WEB_FOUND_IN")

            app = rec["app"]
            if app:
                app_id = app["app_id"]
                app_ids.add(app_id)
                _dedup_node(
                    nodes,
                    app_id,
                    label=app.get("name") or app_id,
                    ntype="monthly_web_app",
                )
                _dedup_link(links, app_id, obs_id, "MONTHLY_DHS_WEB_HAS_OBSERVATION")

            v = rec["v"]
            if v:
                vid = v["web_vuln_id"]
                vuln_ids.add(vid)
                _dedup_node(
                    nodes,
                    vid,
                    label=v.get("name") or f"Vuln {vid}",
                    ntype="monthly_web_vuln",
                    extra={"severity": v.get("severity"), "cvss": v.get("base_cvss")},
                )
                _dedup_link(links, obs_id, vid, "MONTHLY_DHS_WEB_OF_VULNERABILITY")

        return {
            "scan_id": scan_id,
            "year": s.get("year"),
            "month": s.get("month"),
            "summary": {
                "observation_count": obs_count,
                "app_count": len(app_ids),
                "vuln_count": len(vuln_ids),
                "node_count": len(nodes),
                "link_count": len(links),
            },
            "graph": {
                "nodes": list(nodes.values()),
                "links": list(links.values()),
            },
        }


@router.get("/dept-latest")
def dept_latest(department: str = "IT", driver: Driver = Depends(driver_dependency)):
    """
    Latest departmental scan for a given department (default IT):
    Dept -> Host -> Service -> Observation -> Vuln -> Scan
    """
    from ..ingestion.storage import sanitize_dept

    dept_id = sanitize_dept(department)

    with driver.session() as session:
        scan_record = session.run(
            """
            MATCH (s:DeptScanScan)-[:DEPT_SCAN_FOR_DEPARTMENT]->(d:DeptScanDepartment { dept_id: $dept_id })
            WITH s, d
            ORDER BY s.scan_date DESC
            LIMIT 1
            RETURN s, d
            """,
            dept_id=dept_id,
        ).single()

        if not scan_record:
            raise HTTPException(
                status_code=404,
                detail=f"No DeptScanScan found for department '{department}'",
            )

        s = scan_record["s"]
        d = scan_record["d"]
        scan_id = s["scan_id"]

        records = session.run(
            """
            MATCH (s:DeptScanScan { scan_id: $scan_id })
            MATCH (o:DeptScanObservation)-[:DEPT_SCAN_FOUND_IN]->(s)
            WITH s, o
            ORDER BY o.severity_at_scan DESC
            LIMIT $max_obs
            OPTIONAL MATCH (h:DeptScanHost)-[:DEPT_SCAN_HAS_OBSERVATION]->(o)
            OPTIONAL MATCH (svc:DeptScanService)-[:DEPT_SCAN_HAS_OBSERVATION]->(o)
            OPTIONAL MATCH (o)-[:DEPT_SCAN_OF_VULNERABILITY]->(v:DeptScanVulnerability)
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

        # dept + scan
        _dedup_node(
            nodes,
            d["dept_id"],
            label=d.get("name") or d["dept_id"],
            ntype="dept",
        )
        _dedup_node(
            nodes,
            scan_id,
            label=scan_id,
            ntype="dept_scan",
            extra={"year": s.get("year"), "month": s.get("month")},
        )
        _dedup_link(links, scan_id, d["dept_id"], "DEPT_SCAN_FOR_DEPARTMENT")

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
                ntype="dept_observation",
                extra={"severity": o.get("severity_at_scan")},
            )
            _dedup_link(links, obs_id, scan_id, "DEPT_SCAN_FOUND_IN")

            h = rec["h"]
            if h:
                host_id = h["host_id"]
                host_ids.add(host_id)
                _dedup_node(
                    nodes,
                    host_id,
                    label=h.get("ip") or host_id,
                    ntype="dept_host",
                )
                _dedup_link(links, d["dept_id"], host_id, "DEPT_SCAN_OWNS_HOST")
                _dedup_link(links, host_id, obs_id, "DEPT_SCAN_HAS_OBSERVATION")

            svc = rec["svc"]
            if svc:
                svc_id = svc["service_id"]
                _dedup_node(
                    nodes,
                    svc_id,
                    label=svc_id,
                    ntype="dept_service",
                )
                if h:
                    _dedup_link(links, host_id, svc_id, "DEPT_SCAN_RUNS")
                _dedup_link(links, svc_id, obs_id, "DEPT_SCAN_HAS_OBSERVATION")

            v = rec["v"]
            if v:
                vid = v["dept_vuln_id"]
                vuln_ids.add(vid)
                _dedup_node(
                    nodes,
                    vid,
                    label=v.get("title") or f"Vuln {vid}",
                    ntype="dept_vuln",
                    extra={"severity": v.get("severity")},
                )
                _dedup_link(links, obs_id, vid, "DEPT_SCAN_OF_VULNERABILITY")

        return {
            "scan_id": scan_id,
            "year": s.get("year"),
            "month": s.get("month"),
            "department": d.get("name") or department,
            "dept_id": d["dept_id"],
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
