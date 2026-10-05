export interface ChainEvent {
  id: string;
  timestamp: string;
  action: string;
  actor: string;
  detail: string;
}

export interface EvidenceRecord {
  id: string;
  name: string;
  path: string;
  size: number;
  sha256: string;
  addedAt: string;
  verifiedAt: string | null;
  readOnly: boolean;
}

export interface CaseRecord {
  id: string;
  name: string;
  createdAt: string;
  rootDir: string;
  evidence: EvidenceRecord[];
  timeline: ChainEvent[];
}

export interface VerificationResult {
  matches: boolean;
  expectedSha256: string;
  actualSha256: string;
  caseRecord: CaseRecord;
}

export interface FileEntry {
  name: string;
  path: string;
  isDir: boolean;
  size: number;
}

export interface HexChunk {
  offset: number;
  bytes: number[];
  eof: boolean;
}

export interface WslStatus {
  online: boolean;
  distro: string;
  user: string;
  kernel: string;
  home: string;
  forensicTools: number;
  message: string;
}

export type WorkspaceModule =
  | "dashboard"
  | "cases"
  | "evidence"
  | "files"
  | "tools"
  | "settings";
