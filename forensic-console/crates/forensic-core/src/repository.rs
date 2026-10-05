use crate::{hash_file_sha256, CaseRecord, ChainEvent, EvidenceRecord, VerificationResult};
use anyhow::{bail, Context, Result};
use chrono::Utc;
use directories::ProjectDirs;
use std::{
    fs,
    path::{Path, PathBuf},
};
use uuid::Uuid;

#[derive(Debug, Clone)]
pub struct CaseRepository {
    data_dir: PathBuf,
}

pub fn default_data_dir() -> PathBuf {
    ProjectDirs::from("dev", "BlackArch", "ForensicConsole")
        .map(|dirs| dirs.data_local_dir().to_path_buf())
        .unwrap_or_else(|| {
            std::env::current_dir()
                .unwrap_or_else(|_| PathBuf::from("."))
                .join(".forensic-console")
        })
}

impl Default for CaseRepository {
    fn default() -> Self {
        Self::new(default_data_dir())
    }
}

impl CaseRepository {
    pub fn new(data_dir: impl Into<PathBuf>) -> Self {
        Self {
            data_dir: data_dir.into(),
        }
    }

    fn cases_dir(&self) -> PathBuf {
        self.data_dir.join("cases")
    }

    fn case_dir(&self, id: &str) -> PathBuf {
        self.cases_dir().join(id)
    }

    fn case_file(&self, id: &str) -> PathBuf {
        self.case_dir(id).join("case.json")
    }

    fn ensure_dirs(&self) -> Result<()> {
        fs::create_dir_all(self.cases_dir()).context("failed to create forensic case store")
    }

    pub fn list_cases(&self) -> Result<Vec<CaseRecord>> {
        self.ensure_dirs()?;
        let mut cases = Vec::new();

        for entry in fs::read_dir(self.cases_dir())? {
            let entry = entry?;
            if !entry.file_type()?.is_dir() {
                continue;
            }
            let file = entry.path().join("case.json");
            if !file.is_file() {
                continue;
            }
            let raw = fs::read_to_string(&file)
                .with_context(|| format!("failed reading {}", file.display()))?;
            match serde_json::from_str::<CaseRecord>(&raw) {
                Ok(case) => cases.push(case),
                Err(error) => eprintln!("Skipping invalid case {}: {error}", file.display()),
            }
        }

        cases.sort_by(|a, b| b.created_at.cmp(&a.created_at));
        Ok(cases)
    }

    pub fn create_case(&self, name: &str) -> Result<CaseRecord> {
        let name = name.trim();
        if name.len() < 3 {
            bail!("case name must contain at least 3 characters");
        }

        self.ensure_dirs()?;
        let id = format!("DFIR-{}", Uuid::new_v4().simple());
        let case_dir = self.case_dir(&id);
        fs::create_dir_all(case_dir.join("notes"))?;
        fs::create_dir_all(case_dir.join("reports"))?;

        let now = Utc::now().to_rfc3339();
        let case = CaseRecord {
            id: id.clone(),
            name: name.to_string(),
            created_at: now.clone(),
            root_dir: case_dir.to_string_lossy().into_owned(),
            evidence: Vec::new(),
            timeline: vec![ChainEvent {
                id: Uuid::new_v4().to_string(),
                timestamp: now,
                action: "Case created".to_string(),
                actor: current_actor(),
                detail: "Forensic workspace initialized. Evidence is referenced read-only by default."
                    .to_string(),
            }],
        };

        self.save_case(&case)?;
        Ok(case)
    }

    pub fn get_case(&self, id: &str) -> Result<CaseRecord> {
        let file = self.case_file(id);
        let raw =
            fs::read_to_string(&file).with_context(|| format!("case not found: {id}"))?;
        serde_json::from_str(&raw).context("case metadata is invalid")
    }

    pub fn add_evidence(&self, case_id: &str, source: &Path) -> Result<CaseRecord> {
        if !source.is_file() {
            bail!("evidence path is not a regular file");
        }

        let mut case = self.get_case(case_id)?;
        let metadata = fs::metadata(source)?;
        let sha256 = hash_file_sha256(source)?;
        let now = Utc::now().to_rfc3339();

        let record = EvidenceRecord {
            id: Uuid::new_v4().to_string(),
            name: source
                .file_name()
                .map(|name| name.to_string_lossy().into_owned())
                .unwrap_or_else(|| "evidence".to_string()),
            path: source.to_string_lossy().into_owned(),
            size: metadata.len(),
            sha256: sha256.clone(),
            added_at: now.clone(),
            verified_at: Some(now.clone()),
            read_only: true,
        };

        case.timeline.push(ChainEvent {
            id: Uuid::new_v4().to_string(),
            timestamp: now,
            action: "Evidence registered".to_string(),
            actor: current_actor(),
            detail: format!(
                "{} · {} bytes · SHA256 {}",
                record.name, record.size, record.sha256
            ),
        });
        case.evidence.push(record);
        self.save_case(&case)?;
        Ok(case)
    }

    pub fn verify_evidence(&self, case_id: &str, evidence_id: &str) -> Result<VerificationResult> {
        let mut case = self.get_case(case_id)?;
        let index = case
            .evidence
            .iter()
            .position(|item| item.id == evidence_id)
            .context("evidence not found")?;

        let expected = case.evidence[index].sha256.clone();
        let path = PathBuf::from(&case.evidence[index].path);
        let actual = hash_file_sha256(&path)?;
        let matches = expected.eq_ignore_ascii_case(&actual);
        let now = Utc::now().to_rfc3339();

        if matches {
            case.evidence[index].verified_at = Some(now.clone());
        }

        case.timeline.push(ChainEvent {
            id: Uuid::new_v4().to_string(),
            timestamp: now,
            action: if matches {
                "Evidence verified".to_string()
            } else {
                "Integrity mismatch".to_string()
            },
            actor: current_actor(),
            detail: if matches {
                format!("SHA-256 verified for {}", case.evidence[index].name)
            } else {
                format!(
                    "SHA-256 mismatch for {}. Expected {}, got {}",
                    case.evidence[index].name, expected, actual
                )
            },
        });

        self.save_case(&case)?;
        Ok(VerificationResult {
            matches,
            expected_sha256: expected,
            actual_sha256: actual,
            case_record: case,
        })
    }

    pub fn export_markdown_report(&self, case_id: &str) -> Result<PathBuf> {
        let case = self.get_case(case_id)?;
        let reports_dir = self.case_dir(case_id).join("reports");
        fs::create_dir_all(&reports_dir)?;

        let timestamp = Utc::now().format("%Y%m%d-%H%M%S");
        let target = reports_dir.join(format!("{}-report-{}.md", case.id, timestamp));
        let mut markdown = String::new();

        markdown.push_str(&format!("# Forensic Case Report — {}\n\n", case.name));
        markdown.push_str(&format!("- **Case ID:** {}\n", case.id));
        markdown.push_str(&format!("- **Created:** {}\n", case.created_at));
        markdown.push_str(&format!("- **Case root:** `{}`\n\n", case.root_dir));

        markdown.push_str("## Evidence\n\n");
        if case.evidence.is_empty() {
            markdown.push_str("No evidence registered.\n\n");
        } else {
            for evidence in &case.evidence {
                markdown.push_str(&format!(
                    "### {}\n\n- Path: `{}`\n- Size: {} bytes\n- SHA-256: `{}`\n- Added: {}\n- Last verified: {}\n- Read-only registration: {}\n\n",
                    evidence.name,
                    evidence.path,
                    evidence.size,
                    evidence.sha256,
                    evidence.added_at,
                    evidence.verified_at.as_deref().unwrap_or("never"),
                    evidence.read_only
                ));
            }
        }

        markdown.push_str("## Chain of Custody\n\n");
        for event in &case.timeline {
            markdown.push_str(&format!(
                "- **{}** — {} — {} — {}\n",
                event.timestamp, event.action, event.actor, event.detail
            ));
        }

        markdown.push_str("\n---\nGenerated by BlackArch Forensic Console.\n");
        fs::write(&target, markdown)?;
        Ok(target)
    }

    pub fn save_case(&self, case: &CaseRecord) -> Result<()> {
        let dir = self.case_dir(&case.id);
        fs::create_dir_all(&dir)?;
        let target = dir.join("case.json");
        let temp = dir.join("case.json.tmp");
        let json = serde_json::to_vec_pretty(case)?;
        fs::write(&temp, json)?;
        if target.exists() {
            fs::remove_file(&target)?;
        }
        fs::rename(temp, target)?;
        Ok(())
    }
}

fn current_actor() -> String {
    std::env::var("USERNAME")
        .or_else(|_| std::env::var("USER"))
        .unwrap_or_else(|_| "local-user".to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Write;

    #[test]
    fn evidence_round_trip_detects_mutation() {
        let temp = tempfile::tempdir().expect("temp dir");
        let repo = CaseRepository::new(temp.path().join("store"));
        let case = repo.create_case("DFIR regression test").expect("create case");

        let evidence_path = temp.path().join("sample.bin");
        fs::write(&evidence_path, b"original bytes").expect("seed evidence");
        let case = repo
            .add_evidence(&case.id, &evidence_path)
            .expect("add evidence");
        let evidence_id = case.evidence[0].id.clone();

        let verified = repo
            .verify_evidence(&case.id, &evidence_id)
            .expect("verify");
        assert!(verified.matches);

        let mut file = fs::OpenOptions::new()
            .append(true)
            .open(&evidence_path)
            .expect("open evidence");
        file.write_all(b"tampered").expect("modify evidence");

        let mismatch = repo
            .verify_evidence(&case.id, &evidence_id)
            .expect("verify mismatch");
        assert!(!mismatch.matches);
    }
}
