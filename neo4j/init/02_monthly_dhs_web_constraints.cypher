// Monthly DHS Web Application Schema

CREATE CONSTRAINT monthly_dhs_web_app_unique IF NOT EXISTS
FOR (a:MonthlyDHSWebApp)
REQUIRE a.app_id IS UNIQUE;

CREATE CONSTRAINT monthly_dhs_web_vuln_unique IF NOT EXISTS
FOR (v:MonthlyDHSWebVulnerability)
REQUIRE v.web_vuln_id IS UNIQUE;

CREATE CONSTRAINT monthly_dhs_web_scan_unique IF NOT EXISTS
FOR (s:MonthlyDHSWebScan)
REQUIRE s.scan_id IS UNIQUE;

CREATE CONSTRAINT monthly_dhs_web_obs_unique IF NOT EXISTS
FOR (o:MonthlyDHSWebObservation)
REQUIRE o.obs_id IS UNIQUE;

CREATE INDEX monthly_dhs_web_vuln_severity_index IF NOT EXISTS
FOR (v:MonthlyDHSWebVulnerability)
ON (v.severity);

CREATE INDEX monthly_dhs_web_scan_date_index IF NOT EXISTS
FOR (s:MonthlyDHSWebScan)
ON (s.scan_date);
