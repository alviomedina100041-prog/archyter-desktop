use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct ChainEvent {
    pub id: String,
    pub timestamp: String,
    pub action: String,
    pub actor: String,
    pub detail: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct EvidenceRecord {
    pub id: String,
    pub name: String,
    pub path: String,
    pub size: u64,
    pub sha256: String,
    pub added_at: String,
    pub verified_at: Option<String>,
    pub read_only: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct CaseRecord {
    pub id: String,
    pub name: String,
    pub created_at: String,
    pub root_dir: String,
    pub evidence: Vec<EvidenceRecord>,
    pub timeline: Vec<ChainEvent>,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct VerificationResult {
    pub matches: bool,
    pub expected_sha256: String,
    pub actual_sha256: String,
    pub case_record: CaseRecord,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct FileEntry {
    pub name: String,
    pub path: String,
    pub is_dir: bool,
    pub size: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "camelCase")]
pub struct WslStatus {
    pub online: bool,
    pub distro: String,
    pub user: String,
    pub kernel: String,
    pub home: String,
    pub forensic_tools: u32,
    pub message: String,
}
