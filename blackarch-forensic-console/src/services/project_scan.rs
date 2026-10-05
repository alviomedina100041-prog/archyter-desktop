use std::collections::VecDeque;
use std::fs;
use std::io::Read;
use std::path::{Path, PathBuf};

use crate::model::{Finding, Severity};

const MAX_FILES: usize = 50_000;
const MAX_READ_BYTES: u64 = 1_048_576;

#[derive(Debug, Clone, Default)]
pub struct ScanStats {
    pub files_seen: usize,
    pub files_read: usize,
    pub skipped_large: usize,
    pub errors: usize,
}

#[derive(Debug, Clone, Default)]
pub struct ProjectScanResult {
    pub findings: Vec<Finding>,
    pub stats: ScanStats,
}

pub fn scan_project(root: &Path) -> Result<ProjectScanResult, String> {
    if !root.is_dir() {
        return Err(format!("Not a project directory: {}", root.display()));
    }

    let mut result = ProjectScanResult::default();
    let mut queue = VecDeque::from([root.to_path_buf()]);
    let mut suspicious_files = Vec::<PathBuf>::new();
    let mut secret_lines = 0u32;
    let mut permission_notes = 0u32;

    while let Some(dir) = queue.pop_front() {
        let entries = match fs::read_dir(&dir) {
            Ok(v) => v,
            Err(_) => { result.stats.errors += 1; continue; }
        };
        for entry in entries {
            if result.stats.files_seen >= MAX_FILES { break; }
            let entry = match entry { Ok(v) => v, Err(_) => { result.stats.errors += 1; continue; } };
            let path = entry.path();
            let name = entry.file_name().to_string_lossy().to_string();
            if path.is_dir() {
                if should_skip_dir(&name) { continue; }
                queue.push_back(path);
                continue;
            }
            result.stats.files_seen += 1;
            if suspicious_filename(&name) {
                suspicious_files.push(path.clone());
            }
            let meta = match entry.metadata() { Ok(v) => v, Err(_) => { result.stats.errors += 1; continue; } };
            if !meta.permissions().readonly() && is_sensitive_name(&name) {
                permission_notes += 1;
            }
            if meta.len() > MAX_READ_BYTES {
                result.stats.skipped_large += 1;
                continue;
            }
            if !looks_textual(&path) { continue; }
            let file = match fs::File::open(&path) { Ok(v) => v, Err(_) => { result.stats.errors += 1; continue; } };
            let mut text = String::new();
            if file.take(MAX_READ_BYTES).read_to_string(&mut text).is_err() { continue; }
            result.stats.files_read += 1;
            for line in text.lines() {
                let l = line.to_ascii_lowercase();
                if looks_like_secret_line(&l) { secret_lines = secret_lines.saturating_add(1); }
            }
        }
        if result.stats.files_seen >= MAX_FILES { break; }
    }

    if !suspicious_files.is_empty() {
        let preview = suspicious_files.iter().take(6).map(|p| p.display().to_string()).collect::<Vec<_>>().join("\n");
        result.findings.push(Finding {
            severity: Severity::High,
            title: "Sensitive files in project directory".into(),
            detail: format!("{} potentially sensitive filenames detected.\n{}", suspicious_files.len(), preview),
            count: suspicious_files.len().min(u32::MAX as usize) as u32,
        });
    }
    if secret_lines > 0 {
        result.findings.push(Finding {
            severity: Severity::Medium,
            title: "Potential credential artifacts in source text".into(),
            detail: "Review matching lines manually; scanner intentionally does not print secret values.".into(),
            count: secret_lines,
        });
    }
    if permission_notes > 0 {
        result.findings.push(Finding {
            severity: Severity::Low,
            title: "Writable sensitive files".into(),
            detail: "Sensitive-name files are writable. Validate ACLs and repository handling.".into(),
            count: permission_notes,
        });
    }

    Ok(result)
}

fn should_skip_dir(name: &str) -> bool {
    matches!(name.to_ascii_lowercase().as_str(), ".git" | "node_modules" | "target" | ".venv" | "venv" | "dist" | "build")
}

fn suspicious_filename(name: &str) -> bool {
    let n = name.to_ascii_lowercase();
    n == ".env" || n.starts_with(".env.") || n == "id_rsa" || n == "id_ed25519" || n.ends_with(".pem") || n.ends_with(".p12") || n.ends_with(".pfx") || n.ends_with(".key") || n.contains("credentials") || n.contains("secrets")
}

fn is_sensitive_name(name: &str) -> bool {
    suspicious_filename(name)
}

fn looks_textual(path: &Path) -> bool {
    match path.extension().and_then(|v| v.to_str()).map(|s| s.to_ascii_lowercase()) {
        None => true,
        Some(ext) => matches!(ext.as_str(), "rs" | "py" | "js" | "ts" | "tsx" | "jsx" | "json" | "yaml" | "yml" | "toml" | "ini" | "cfg" | "conf" | "env" | "txt" | "md" | "sql" | "ps1" | "sh" | "html" | "css" | "xml"),
    }
}

fn looks_like_secret_line(line: &str) -> bool {
    let has_assignment = line.contains('=') || line.contains(':');
    if !has_assignment { return false; }
    ["password", "passwd", "secret", "api_key", "apikey", "access_token", "private_key", "database_url", "connection_string"]
        .iter().any(|needle| line.contains(needle))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_secretish_names() {
        assert!(suspicious_filename(".env.production"));
        assert!(suspicious_filename("server.pem"));
        assert!(!suspicious_filename("README.md"));
    }

    #[test]
    fn secret_line_detector_requires_assignment() {
        assert!(looks_like_secret_line("db_password = abc"));
        assert!(!looks_like_secret_line("password policy documentation"));
    }
}
