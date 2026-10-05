use std::fs;
use std::path::Path;

use crate::model::{human_bytes, CaseData};

pub fn write_markdown(case: &CaseData, path: &Path) -> Result<(), String> {
    let mut out = String::new();
    out.push_str(&format!("# BlackArch Forensic Console — Case {}\n\n", case.id));
    out.push_str("Generated DFIR working report. Findings require analyst validation before production use.\n\n");

    out.push_str("## Evidence\n\n");
    for ev in &case.evidence {
        out.push_str(&format!("- **{}** — {} — {}\n", ev.name, human_bytes(ev.size_bytes), ev.path.display()));
        if let Some(hash) = &ev.sha256 { out.push_str(&format!("  - SHA256: {}\n", hash)); }
        out.push_str(&format!("  - Verified: {}\n", if ev.verified { "yes" } else { "no" }));
    }

    out.push_str("\n## Findings\n\n");
    for finding in &case.findings {
        out.push_str(&format!("### [{}] {} ({})\n\n{}\n\n", finding.severity.label(), finding.title, finding.count, finding.detail));
    }

    out.push_str("## PostgreSQL Audit\n\n");
    out.push_str(&format!("- Roles: {}\n- Tables exposed to PUBLIC: {}\n- PUBLIC grants: {}\n- Risky access indicators: {}\n",
        case.audit.roles, case.audit.tables_exposed, case.audit.public_grants, case.audit.risky_access));
    if !case.audit.raw_output.is_empty() {
        out.push_str("\n    Raw output:\n");
        out.push_str(&case.audit.raw_output);
        out.push_str("\n");
    }

    out.push_str("\n## Timeline\n\n");
    for event in &case.timeline {
        out.push_str(&format!("- {} **{}** — {}\n", event.time, event.category, event.message));
    }

    fs::write(path, out).map_err(|e| format!("Unable to write report {}: {e}", path.display()))
}
