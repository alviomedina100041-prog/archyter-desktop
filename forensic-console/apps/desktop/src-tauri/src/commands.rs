use forensic_core::{
    list_directory, list_forensic_tools, probe_wsl, read_file_chunk, CaseRecord, CaseRepository,
    FileEntry, HexChunk, VerificationResult, WslStatus,
};
use std::path::PathBuf;

#[tauri::command]
pub fn list_cases() -> Result<Vec<CaseRecord>, String> {
    CaseRepository::default()
        .list_cases()
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn create_case(name: String) -> Result<CaseRecord, String> {
    CaseRepository::default()
        .create_case(&name)
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn add_evidence(case_id: String, path: String) -> Result<CaseRecord, String> {
    CaseRepository::default()
        .add_evidence(&case_id, &PathBuf::from(path))
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn verify_evidence(
    case_id: String,
    evidence_id: String,
) -> Result<VerificationResult, String> {
    CaseRepository::default()
        .verify_evidence(&case_id, &evidence_id)
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn list_dir(path: String) -> Result<Vec<FileEntry>, String> {
    list_directory(&PathBuf::from(path)).map_err(|error| error.to_string())
}

#[tauri::command]
pub fn read_hex_chunk(path: String, offset: u64, length: usize) -> Result<HexChunk, String> {
    read_file_chunk(&PathBuf::from(path), offset, length).map_err(|error| error.to_string())
}

#[tauri::command]
pub fn probe_wsl_status(distro: String) -> Result<WslStatus, String> {
    probe_wsl(&distro).map_err(|error| error.to_string())
}

#[tauri::command]
pub fn forensic_tools(distro: String) -> Result<Vec<String>, String> {
    list_forensic_tools(&distro).map_err(|error| error.to_string())
}


#[tauri::command]
pub fn export_case_report(case_id: String) -> Result<String, String> {
    CaseRepository::default()
        .export_markdown_report(&case_id)
        .map(|path| path.to_string_lossy().into_owned())
        .map_err(|error| error.to_string())
}
