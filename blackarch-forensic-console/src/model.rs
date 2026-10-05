use std::path::PathBuf;
use std::time::SystemTime;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Severity {
    Critical,
    High,
    Medium,
    Low,
    Info,
}

impl Severity {
    pub fn label(self) -> &'static str {
        match self {
            Self::Critical => "Critical",
            Self::High => "High",
            Self::Medium => "Medium",
            Self::Low => "Low",
            Self::Info => "Info",
        }
    }
}

#[derive(Clone, Debug)]
pub struct Finding {
    pub severity: Severity,
    pub title: String,
    pub detail: String,
    pub count: u32,
}

#[derive(Clone, Debug)]
pub struct TimelineEvent {
    pub time: String,
    pub message: String,
    pub category: String,
    pub severity: Severity,
}

#[derive(Clone, Debug)]
pub struct Evidence {
    pub name: String,
    pub path: PathBuf,
    pub evidence_type: String,
    pub size_bytes: u64,
    pub acquired: String,
    pub modified: String,
    pub sha256: Option<String>,
    pub verified: bool,
    pub read_only: bool,
    pub tags: Vec<String>,
}

impl Evidence {
    pub fn demo() -> Self {
        Self {
            name: "disk01.E01".into(),
            path: PathBuf::from(r"E:\Cases\2026-DFIR-014\Evidence\disk01.E01"),
            evidence_type: "EnCase Evidence File (E01)".into(),
            size_bytes: 500 * 1024 * 1024 * 1024,
            acquired: "2026-02-14 10:32:17 UTC".into(),
            modified: "2026-02-14 10:32:17 UTC".into(),
            sha256: Some("3f4a6d7e8c9b2a1d0e5c7f9a3b6d8e2f41c7e9a8d3b6f4c1e9d0a7b3c5d9e2f11".into()),
            verified: true,
            read_only: true,
            tags: vec!["windows".into(), "server".into(), "production".into(), "erp".into(), "2026".into()],
        }
    }

    pub fn from_path(path: PathBuf) -> std::io::Result<Self> {
        let metadata = std::fs::metadata(&path)?;
        let name = path.file_name().and_then(|v| v.to_str()).unwrap_or("evidence.bin").to_string();
        let evidence_type = match path.extension().and_then(|v| v.to_str()).map(|s| s.to_ascii_lowercase()) {
            Some(ext) if ext == "e01" => "EnCase Evidence File (E01)",
            Some(ext) if ext == "raw" || ext == "dd" || ext == "img" => "Raw disk / memory image",
            Some(ext) if ext == "pcap" || ext == "pcapng" => "Packet capture",
            Some(ext) if ext == "evtx" => "Windows Event Log",
            _ => "Digital evidence",
        }.to_string();

        Ok(Self {
            name,
            path,
            evidence_type,
            size_bytes: metadata.len(),
            acquired: format_system_time(SystemTime::now()),
            modified: metadata.modified().ok().map(format_system_time).unwrap_or_else(|| "Unknown".into()),
            sha256: None,
            verified: false,
            read_only: metadata.permissions().readonly(),
            tags: Vec::new(),
        })
    }
}

fn format_system_time(_time: SystemTime) -> String {
    "Captured locally".into()
}

#[derive(Clone, Debug, Default)]
pub struct AuditSummary {
    pub roles: u32,
    pub tables_exposed: u32,
    pub public_grants: u32,
    pub risky_access: u32,
    pub raw_output: String,
}

#[derive(Clone, Debug)]
pub struct CaseData {
    pub id: String,
    pub evidence: Vec<Evidence>,
    pub findings: Vec<Finding>,
    pub timeline: Vec<TimelineEvent>,
    pub audit: AuditSummary,
    pub project_path: Option<PathBuf>,
}

impl CaseData {
    pub fn demo() -> Self {
        let findings = vec![
            Finding { severity: Severity::Critical, title: "Excessive privileges for role \"erp_app\"".into(), detail: "Application role appears to have administrative permissions.".into(), count: 3 },
            Finding { severity: Severity::High, title: "Database tables exposed to PUBLIC".into(), detail: "PUBLIC has privileges on application tables.".into(), count: 5 },
            Finding { severity: Severity::High, title: "Sensitive files in project directory".into(), detail: "Potential credentials, keys, or environment files detected.".into(), count: 4 },
            Finding { severity: Severity::Medium, title: "Potential credential artifacts in logs".into(), detail: "Review logs for secrets and connection strings.".into(), count: 8 },
            Finding { severity: Severity::Low, title: "Misconfigured file permissions".into(), detail: "Some files are writable by broader principals than expected.".into(), count: 6 },
        ];

        let timeline = vec![
            TimelineEvent { time: "10:32:17".into(), message: "Evidence acquired: disk01.E01".into(), category: "Evidence".into(), severity: Severity::Info },
            TimelineEvent { time: "10:45:02".into(), message: "Hash verification completed (SHA256)".into(), category: "Integrity".into(), severity: Severity::Low },
            TimelineEvent { time: "11:02:11".into(), message: "Mounted disk image (read-only)".into(), category: "System".into(), severity: Severity::Low },
            TimelineEvent { time: "11:15:33".into(), message: "PostgreSQL audit initiated".into(), category: "Database".into(), severity: Severity::Medium },
            TimelineEvent { time: "11:28:46".into(), message: "Scanned project directory (4,823 files)".into(), category: "File System".into(), severity: Severity::Info },
            TimelineEvent { time: "11:42:19".into(), message: "Memory analysis started (memory.raw)".into(), category: "Memory".into(), severity: Severity::Info },
            TimelineEvent { time: "12:01:07".into(), message: "Suspicious file pattern detected: *.pem".into(), category: "File System".into(), severity: Severity::High },
            TimelineEvent { time: "12:14:55".into(), message: "PostgreSQL risky access detected".into(), category: "Database".into(), severity: Severity::Critical },
            TimelineEvent { time: "12:27:31".into(), message: "Report draft generated".into(), category: "Report".into(), severity: Severity::Info },
        ];

        Self {
            id: "2026-DFIR-014".into(),
            evidence: vec![Evidence::demo()],
            findings,
            timeline,
            audit: AuditSummary { roles: 5, tables_exposed: 7, public_grants: 3, risky_access: 4, raw_output: String::new() },
            project_path: Some(PathBuf::from(r"C:\Projects\erp_project_backend")),
        }
    }

    pub fn severity_counts(&self) -> [u32; 4] {
        let mut out = [0u32; 4];
        for finding in &self.findings {
            match finding.severity {
                Severity::Critical => out[0] += finding.count.max(1),
                Severity::High => out[1] += finding.count.max(1),
                Severity::Medium => out[2] += finding.count.max(1),
                Severity::Low | Severity::Info => out[3] += finding.count.max(1),
            }
        }
        out
    }
}

pub fn human_bytes(bytes: u64) -> String {
    const KB: f64 = 1024.0;
    const MB: f64 = KB * 1024.0;
    const GB: f64 = MB * 1024.0;
    const TB: f64 = GB * 1024.0;
    let b = bytes as f64;
    if b >= TB { format!("{:.2} TB", b / TB) }
    else if b >= GB { format!("{:.2} GB", b / GB) }
    else if b >= MB { format!("{:.2} MB", b / MB) }
    else if b >= KB { format!("{:.2} KB", b / KB) }
    else { format!("{} B", bytes) }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn byte_formatting_is_stable() {
        assert_eq!(human_bytes(1024), "1.00 KB");
        assert_eq!(human_bytes(1024 * 1024), "1.00 MB");
    }

    #[test]
    fn severity_rollup_counts_weighted_findings() {
        let case = CaseData::demo();
        assert_eq!(case.severity_counts(), [3, 9, 8, 6]);
    }
}
