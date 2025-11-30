// Common utility indexes

CREATE INDEX weekly_dhs_host_hostname_index IF NOT EXISTS
FOR (h:WeeklyDHSHost)
ON (h.hostname);

CREATE INDEX dept_scan_host_ip_index IF NOT EXISTS
FOR (h:DeptScanHost)
ON (h.ip);

CREATE INDEX monthly_dhs_web_app_base_url_index IF NOT EXISTS
FOR (a:MonthlyDHSWebApp)
ON (a.base_url);
