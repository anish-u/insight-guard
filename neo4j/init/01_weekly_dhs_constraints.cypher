// Weekly DHS Network Schema

CREATE CONSTRAINT weekly_dhs_host_ip_unique IF NOT EXISTS
FOR (h:WeeklyDHSHost)
REQUIRE h.ip IS UNIQUE;

CREATE CONSTRAINT weekly_dhs_service_id_unique IF NOT EXISTS
FOR (s:WeeklyDHSService)
REQUIRE s.service_id IS UNIQUE;

CREATE CONSTRAINT weekly_dhs_vuln_plugin_unique IF NOT EXISTS
FOR (v:WeeklyDHSVulnerability)
REQUIRE v.weekly_vuln_id IS UNIQUE;

CREATE CONSTRAINT weekly_dhs_scan_unique IF NOT EXISTS
FOR (s:WeeklyDHSScan)
REQUIRE s.scan_id IS UNIQUE;

CREATE CONSTRAINT weekly_dhs_obs_unique IF NOT EXISTS
FOR (o:WeeklyDHSObservation)
REQUIRE o.obs_id IS UNIQUE;

CREATE INDEX weekly_dhs_vuln_severity_index IF NOT EXISTS
FOR (v:WeeklyDHSVulnerability)
ON (v.severity);

CREATE INDEX weekly_dhs_scan_date_index IF NOT EXISTS
FOR (s:WeeklyDHSScan)
ON (s.scan_date);
