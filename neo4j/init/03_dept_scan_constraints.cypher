// Departmental Monthly Network Scan Schema

CREATE CONSTRAINT dept_scan_dept_unique IF NOT EXISTS
FOR (d:DeptScanDepartment)
REQUIRE d.dept_id IS UNIQUE;

CREATE CONSTRAINT dept_scan_host_unique IF NOT EXISTS
FOR (h:DeptScanHost)
REQUIRE h.host_id IS UNIQUE;

CREATE CONSTRAINT dept_scan_service_unique IF NOT EXISTS
FOR (s:DeptScanService)
REQUIRE s.service_id IS UNIQUE;

CREATE CONSTRAINT dept_scan_vuln_unique IF NOT EXISTS
FOR (v:DeptScanVulnerability)
REQUIRE v.dept_vuln_id IS UNIQUE;

CREATE CONSTRAINT dept_scan_scan_unique IF NOT EXISTS
FOR (s:DeptScanScan)
REQUIRE s.scan_id IS UNIQUE;

CREATE CONSTRAINT dept_scan_obs_unique IF NOT EXISTS
FOR (o:DeptScanObservation)
REQUIRE o.obs_id IS UNIQUE;

CREATE INDEX dept_scan_vuln_severity_index IF NOT EXISTS
FOR (v:DeptScanVulnerability)
ON (v.severity);

CREATE INDEX dept_scan_scan_date_index IF NOT EXISTS
FOR (s:DeptScanScan)
ON (s.scan_date);

CREATE INDEX dept_scan_dept_name_index IF NOT EXISTS
FOR (d:DeptScanDepartment)
ON (d.name);
