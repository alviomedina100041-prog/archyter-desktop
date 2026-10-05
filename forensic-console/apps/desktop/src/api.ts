import { invoke } from "@tauri-apps/api/core";
import type {
  CaseRecord,
  FileEntry,
  VerificationResult,
  WslStatus,
} from "./types";

export const api = {
  listCases: () => invoke<CaseRecord[]>("list_cases"),
  createCase: (name: string) => invoke<CaseRecord>("create_case", { name }),
  addEvidence: (caseId: string, path: string) =>
    invoke<CaseRecord>("add_evidence", { caseId, path }),
  verifyEvidence: (caseId: string, evidenceId: string) =>
    invoke<VerificationResult>("verify_evidence", { caseId, evidenceId }),
  listDir: (path: string) => invoke<FileEntry[]>("list_dir", { path }),
  probeWsl: (distro: string) =>
    invoke<WslStatus>("probe_wsl_status", { distro }),
  forensicTools: (distro: string) =>
    invoke<string[]>("forensic_tools", { distro }),
  terminalWrite: (data: string) => invoke<void>("terminal_write", { data }),
  terminalStop: () => invoke<void>("terminal_stop"),
};
