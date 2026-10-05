use std::process::{Command, Stdio};
use std::time::Instant;

use crate::model::AuditSummary;

#[derive(Debug, Clone)]
pub struct PgTarget {
    pub distro: String,
    pub host: String,
    pub port: u16,
    pub database: String,
    pub user: String,
}

impl Default for PgTarget {
    fn default() -> Self {
        Self {
            distro: "archlinux".into(),
            host: "127.0.0.1".into(),
            port: 5432,
            database: "postgres".into(),
            user: "postgres".into(),
        }
    }
}

#[derive(Debug, Clone)]
pub struct PgAuditResult {
    pub summary: AuditSummary,
    pub report: String,
    pub elapsed_ms: u128,
}

/// Performs a read-only PostgreSQL privilege audit.
/// Authentication is intentionally delegated to libpq (.pgpass, environment, certificates, etc.),
/// so the application never persists a database password.
pub fn audit(target: &PgTarget) -> Result<PgAuditResult, String> {
    validate_identifier_like(&target.host, "host")?;
    validate_identifier_like(&target.database, "database")?;
    validate_identifier_like(&target.user, "user")?;

    const SQL: &str = r#"
WITH role_stats AS (
  SELECT count(*)::int AS roles,
         count(*) FILTER (WHERE rolsuper OR rolcreaterole OR rolcreatedb OR rolbypassrls)::int AS risky_roles
  FROM pg_roles
  WHERE rolname !~ '^pg_'
),
public_table_grants AS (
  SELECT count(*)::int AS public_grants,
         count(DISTINCT table_schema || '.' || table_name)::int AS tables_exposed
  FROM information_schema.role_table_grants
  WHERE grantee = 'PUBLIC'
    AND table_schema NOT IN ('pg_catalog', 'information_schema')
),
public_schema_create AS (
  SELECT count(*)::int AS public_create_schemas
  FROM pg_namespace
  WHERE nspname NOT LIKE 'pg_%'
    AND nspname <> 'information_schema'
    AND has_schema_privilege('PUBLIC', oid, 'CREATE')
)
SELECT r.roles,
       p.tables_exposed,
       p.public_grants,
       (r.risky_roles + s.public_create_schemas)::int AS risky_access
FROM role_stats r, public_table_grants p, public_schema_create s;
"#;

    let start = Instant::now();
    let output = run_psql(target, SQL)?;
    let line = output.lines().find(|l| l.contains('|')).ok_or_else(|| {
        format!("PostgreSQL returned no parsable audit row. Raw output:\n{output}")
    })?;
    let parts: Vec<&str> = line.split('|').map(str::trim).collect();
    if parts.len() != 4 {
        return Err(format!("Unexpected PostgreSQL audit format: {line}"));
    }

    let summary = AuditSummary {
        roles: parse_u32(parts[0])?,
        tables_exposed: parse_u32(parts[1])?,
        public_grants: parse_u32(parts[2])?,
        risky_access: parse_u32(parts[3])?,
        raw_output: output.clone(),
    };

    let details_sql = r#"
SELECT 'ROLE|' || rolname || '|' || rolsuper || '|' || rolcreaterole || '|' || rolcreatedb || '|' || rolbypassrls
FROM pg_roles
WHERE rolname !~ '^pg_'
ORDER BY rolname;

SELECT 'PUBLIC_TABLE|' || table_schema || '.' || table_name || '|' || privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'PUBLIC'
  AND table_schema NOT IN ('pg_catalog', 'information_schema')
ORDER BY table_schema, table_name, privilege_type;
"#;
    let detail_output = run_psql(target, details_sql).unwrap_or_else(|e| format!("Details unavailable: {e}"));
    let report = format!(
        "PostgreSQL privilege audit\nTarget: {}:{} / {} as {}\n\nSummary\n  roles: {}\n  tables exposed to PUBLIC: {}\n  PUBLIC table grants: {}\n  risky access indicators: {}\n\nDetails\n{}",
        target.host, target.port, target.database, target.user,
        summary.roles, summary.tables_exposed, summary.public_grants, summary.risky_access,
        detail_output.trim()
    );

    Ok(PgAuditResult { summary, report, elapsed_ms: start.elapsed().as_millis() })
}

fn run_psql(target: &PgTarget, sql: &str) -> Result<String, String> {
    #[cfg(target_os = "windows")]
    let mut cmd = {
        let mut c = Command::new("wsl.exe");
        c.arg("-d").arg(&target.distro).arg("--").arg("psql");
        c
    };

    #[cfg(not(target_os = "windows"))]
    let mut cmd = Command::new("psql");

    let output = cmd
        .arg("-X")
        .arg("-v").arg("ON_ERROR_STOP=1")
        .arg("-A")
        .arg("-t")
        .arg("-F").arg("|")
        .arg("-h").arg(&target.host)
        .arg("-p").arg(target.port.to_string())
        .arg("-U").arg(&target.user)
        .arg("-d").arg(&target.database)
        .arg("-c").arg(sql)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .output()
        .map_err(|e| format!("Unable to start psql: {e}"))?;

    if !output.status.success() {
        let err = String::from_utf8_lossy(&output.stderr).trim().to_string();
        return Err(if err.is_empty() { "psql exited with a non-zero status".into() } else { err });
    }
    Ok(String::from_utf8_lossy(&output.stdout).into_owned())
}

fn parse_u32(v: &str) -> Result<u32, String> {
    v.parse::<u32>().map_err(|_| format!("Expected integer from PostgreSQL, got: {v}"))
}

fn validate_identifier_like(value: &str, field: &str) -> Result<(), String> {
    if value.is_empty() || value.len() > 255 {
        return Err(format!("Invalid {field}"));
    }
    if value.chars().any(|c| c.is_control() || c == '\0') {
        return Err(format!("Invalid control character in {field}"));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn target_defaults_are_safe_local_values() {
        let t = PgTarget::default();
        assert_eq!(t.host, "127.0.0.1");
        assert_eq!(t.port, 5432);
    }

    #[test]
    fn rejects_control_chars() {
        assert!(validate_identifier_like("erp\nDROP", "db").is_err());
    }
}
