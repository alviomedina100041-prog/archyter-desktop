import { useEffect, useMemo, useState } from "react";
import { open } from "@tauri-apps/plugin-dialog";
import {
  Activity,
  Archive,
  Binary,
  Boxes,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Database,
  File,
  FileCheck2,
  FileClock,
  Folder,
  FolderOpen,
  Gauge,
  HardDrive,
  Hash,
  Laptop,
  ListTree,
  Plus,
  RefreshCw,
  Search,
  Settings,
  ShieldCheck,
  TerminalSquare,
  Wrench,
} from "lucide-react";
import { api } from "./api";
import { TerminalPanel } from "./components/TerminalPanel";
import type {
  CaseRecord,
  EvidenceRecord,
  FileEntry,
  WorkspaceModule,
  WslStatus,
} from "./types";

const EMPTY_WSL: WslStatus = {
  online: false,
  distro: "archlinux",
  user: "",
  kernel: "",
  home: "",
  forensicTools: 0,
  message: "Not checked",
};

const NAV: Array<{
  id: WorkspaceModule;
  label: string;
  icon: typeof Gauge;
}> = [
  { id: "dashboard", label: "Dashboard", icon: Gauge },
  { id: "cases", label: "Cases", icon: Archive },
  { id: "evidence", label: "Evidence", icon: HardDrive },
  { id: "files", label: "Files", icon: FolderOpen },
  { id: "tools", label: "Forensic Tools", icon: Wrench },
  { id: "settings", label: "Settings", icon: Settings },
];

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / 1024 ** index).toFixed(index === 0 ? 0 : 2)} ${units[index]}`;
}

function shortHash(hash: string): string {
  return hash.length > 22 ? `${hash.slice(0, 12)}…${hash.slice(-10)}` : hash;
}

function parentPath(path: string): string {
  const trimmed = path.replace(/[\\/]+$/, "");
  const parent = trimmed.replace(/[\\/][^\\/]+$/, "");
  return parent || trimmed;
}

export default function App() {
  const [module, setModule] = useState<WorkspaceModule>("dashboard");
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [activeCaseId, setActiveCaseId] = useState("");
  const [activeEvidenceId, setActiveEvidenceId] = useState("");
  const [wsl, setWsl] = useState<WslStatus>(EMPTY_WSL);
  const [tools, setTools] = useState<string[]>([]);
  const [toolQuery, setToolQuery] = useState("");
  const [filePath, setFilePath] = useState("");
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [newCaseOpen, setNewCaseOpen] = useState(false);
  const [newCaseName, setNewCaseName] = useState("");
  const [busy, setBusy] = useState("");
  const [notice, setNotice] = useState("");
  const [distro, setDistro] = useState(
    () => localStorage.getItem("blackarch.distro") || "archlinux",
  );
  const [draftDistro, setDraftDistro] = useState(distro);

  const activeCase = useMemo(
    () => cases.find((item) => item.id === activeCaseId) ?? cases[0],
    [cases, activeCaseId],
  );

  const activeEvidence = useMemo(
    () =>
      activeCase?.evidence.find((item) => item.id === activeEvidenceId) ??
      activeCase?.evidence[0],
    [activeCase, activeEvidenceId],
  );

  const filteredTools = useMemo(() => {
    const query = toolQuery.trim().toLowerCase();
    if (!query) return tools;
    return tools.filter((tool) => tool.toLowerCase().includes(query));
  }, [toolQuery, tools]);

  const replaceCase = (updated: CaseRecord) => {
    setCases((current) => {
      const found = current.some((item) => item.id === updated.id);
      return found
        ? current.map((item) => (item.id === updated.id ? updated : item))
        : [updated, ...current];
    });
    setActiveCaseId(updated.id);
  };

  const refreshWsl = async (target = distro) => {
    try {
      const status = await api.probeWsl(target);
      setWsl(status);
    } catch (reason) {
      setWsl({
        ...EMPTY_WSL,
        distro: target,
        message: String(reason),
      });
    }
  };

  const refreshTools = async (target = distro) => {
    try {
      setTools(await api.forensicTools(target));
    } catch {
      setTools([]);
    }
  };

  useEffect(() => {
    const bootstrap = async () => {
      try {
        const loaded = await api.listCases();
        setCases(loaded);
        if (loaded[0]) setActiveCaseId(loaded[0].id);
      } catch (reason) {
        setNotice(String(reason));
      }
      await Promise.all([refreshWsl(), refreshTools()]);
    };
    void bootstrap();

    const timer = window.setInterval(() => void refreshWsl(), 15000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (activeCase?.evidence[0] && !activeEvidenceId) {
      setActiveEvidenceId(activeCase.evidence[0].id);
    }
  }, [activeCase, activeEvidenceId]);

  const createCase = async () => {
    const name = newCaseName.trim();
    if (name.length < 3) return;
    setBusy("Creating forensic case…");
    try {
      const created = await api.createCase(name);
      replaceCase(created);
      setNewCaseName("");
      setNewCaseOpen(false);
      setModule("cases");
      setNotice(`Case ${created.id} created`);
    } catch (reason) {
      setNotice(String(reason));
    } finally {
      setBusy("");
    }
  };

  const addEvidence = async () => {
    if (!activeCase) {
      setNotice("Create or select a case before registering evidence.");
      return;
    }

    const selected = await open({
      title: "Register evidence (source remains untouched)",
      multiple: false,
      directory: false,
    });
    if (typeof selected !== "string") return;

    setBusy("Hashing evidence with SHA-256…");
    try {
      const updated = await api.addEvidence(activeCase.id, selected);
      replaceCase(updated);
      const newest = updated.evidence[updated.evidence.length - 1];
      if (newest) setActiveEvidenceId(newest.id);
      setModule("evidence");
      setNotice("Evidence registered and SHA-256 recorded.");
    } catch (reason) {
      setNotice(String(reason));
    } finally {
      setBusy("");
    }
  };

  const verifyEvidence = async () => {
    if (!activeCase || !activeEvidence) return;
    setBusy("Recalculating SHA-256…");
    try {
      const result = await api.verifyEvidence(activeCase.id, activeEvidence.id);
      replaceCase(result.caseRecord);
      setNotice(
        result.matches
          ? "Integrity verified: SHA-256 matches."
          : "INTEGRITY ALERT: evidence hash changed.",
      );
    } catch (reason) {
      setNotice(String(reason));
    } finally {
      setBusy("");
    }
  };

  const loadFolder = async (path: string) => {
    try {
      setFiles(await api.listDir(path));
      setFilePath(path);
      setModule("files");
    } catch (reason) {
      setNotice(String(reason));
    }
  };

  const chooseFolder = async () => {
    const selected = await open({
      title: "Open directory",
      multiple: false,
      directory: true,
    });
    if (typeof selected === "string") {
      await loadFolder(selected);
    }
  };

  const saveSettings = async () => {
    const next = draftDistro.trim() || "archlinux";
    localStorage.setItem("blackarch.distro", next);
    await api.terminalStop().catch(() => undefined);
    setDistro(next);
    await Promise.all([refreshWsl(next), refreshTools(next)]);
    setNotice(`WSL distro set to ${next}`);
  };

  const runToolHelp = async (tool: string) => {
    if (!/^[a-zA-Z0-9._+:-]+$/.test(tool)) return;
    try {
      await api.terminalWrite(`clear; printf '\\033[1;32mBlackArch tool: ${tool}\\033[0m\\n'; ${tool} --help\\r`);
      setNotice(`${tool} --help sent to the live terminal`);
    } catch (reason) {
      setNotice(String(reason));
    }
  };

  const renderExplorer = () => {
    if (module === "tools") {
      return (
        <>
          <div className="explorer-toolbar">
            <div className="search-box">
              <Search size={14} />
              <input
                value={toolQuery}
                onChange={(event) => setToolQuery(event.target.value)}
                placeholder="Search 163 forensic tools"
              />
            </div>
          </div>
          <div className="scroll-region tool-list">
            {filteredTools.map((tool) => (
              <button className="tool-row" key={tool} onClick={() => void runToolHelp(tool)}>
                <Wrench size={14} />
                <span>{tool}</span>
                <TerminalSquare size={13} className="row-action" />
              </button>
            ))}
            {!filteredTools.length && (
              <div className="empty-state">No tools found in blackarch-forensic.</div>
            )}
          </div>
        </>
      );
    }

    if (module === "files") {
      return (
        <>
          <div className="explorer-toolbar">
            <button className="secondary-button" onClick={() => void chooseFolder()}>
              <FolderOpen size={14} />
              Open folder
            </button>
            {filePath && parentPath(filePath) !== filePath && (
              <button
                className="icon-button"
                title="Parent directory"
                onClick={() => void loadFolder(parentPath(filePath))}
              >
                <ChevronLeft size={15} />
              </button>
            )}
          </div>
          <div className="current-path" title={filePath}>
            {filePath || "Choose a directory to inspect"}
          </div>
          <div className="scroll-region file-list">
            {files.map((entry) => (
              <button
                key={entry.path}
                className="file-row"
                onDoubleClick={() => entry.isDir && void loadFolder(entry.path)}
                onClick={() => setNotice(entry.path)}
              >
                {entry.isDir ? <Folder size={15} /> : <File size={15} />}
                <span className="file-name">{entry.name}</span>
                <span className="file-size">{entry.isDir ? "" : formatBytes(entry.size)}</span>
                {entry.isDir && <ChevronRight size={13} />}
              </button>
            ))}
          </div>
        </>
      );
    }

    if (module === "settings") {
      return (
        <div className="settings-pane">
          <label>
            WSL distro
            <input
              value={draftDistro}
              onChange={(event) => setDraftDistro(event.target.value)}
              spellCheck={false}
            />
          </label>
          <p>
            The terminal opens a real PTY backed by <code>wsl.exe -d DISTRO</code>.
          </p>
          <button className="primary-button" onClick={() => void saveSettings()}>
            <RefreshCw size={14} />
            Save & reconnect
          </button>
        </div>
      );
    }

    return (
      <>
        <div className="explorer-toolbar">
          <button className="primary-button" onClick={() => setNewCaseOpen(true)}>
            <Plus size={14} />
            New case
          </button>
          <button className="secondary-button" onClick={() => void addEvidence()}>
            <FileCheck2 size={14} />
            Add evidence
          </button>
        </div>
        <div className="scroll-region case-tree">
          {cases.map((caseItem) => (
            <div className="case-group" key={caseItem.id}>
              <button
                className={caseItem.id === activeCase?.id ? "tree-row active" : "tree-row"}
                onClick={() => {
                  setActiveCaseId(caseItem.id);
                  setActiveEvidenceId(caseItem.evidence[0]?.id ?? "");
                }}
              >
                <Archive size={15} />
                <div>
                  <strong>{caseItem.name}</strong>
                  <span>{caseItem.id}</span>
                </div>
                <span className="count-badge">{caseItem.evidence.length}</span>
              </button>
              {caseItem.id === activeCase?.id &&
                caseItem.evidence.map((evidence) => (
                  <button
                    key={evidence.id}
                    className={
                      evidence.id === activeEvidence?.id
                        ? "tree-row evidence-row active-evidence"
                        : "tree-row evidence-row"
                    }
                    onClick={() => {
                      setActiveEvidenceId(evidence.id);
                      setModule("evidence");
                    }}
                  >
                    <HardDrive size={14} />
                    <span className="truncate">{evidence.name}</span>
                    {evidence.verifiedAt && <CheckCircle2 size={13} className="ok-icon" />}
                  </button>
                ))}
            </div>
          ))}
          {!cases.length && (
            <div className="empty-state">
              <Archive size={28} />
              <strong>No forensic cases yet</strong>
              <span>Create a case before registering evidence.</span>
            </div>
          )}
        </div>
      </>
    );
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark"><ShieldCheck size={23} /></div>
          <div>
            <strong>BLACKARCH FORENSIC CONSOLE</strong>
            <span>WSL2 DFIR Workspace</span>
          </div>
        </div>
        <div className="topbar-status">
          <button className="status-chip" onClick={() => void refreshWsl()}>
            <span className={wsl.online ? "status-dot online" : "status-dot"} />
            <span>WSL2: {distro}</span>
            <b>{wsl.online ? "Online" : "Offline"}</b>
          </button>
          <div className="case-chip">
            <Archive size={14} />
            <span>{activeCase ? activeCase.id : "No active case"}</span>
          </div>
        </div>
      </header>

      <aside className="sidebar">
        <nav>
          {NAV.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                className={module === item.id ? "nav-item active" : "nav-item"}
                onClick={() => setModule(item.id)}
                title={item.label}
              >
                <Icon size={19} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
        <div className="sidebar-health">
          <div className="health-title">
            <Activity size={15} />
            <span>Live environment</span>
          </div>
          <dl>
            <div><dt>Distro</dt><dd>{wsl.distro}</dd></div>
            <div><dt>User</dt><dd>{wsl.user || "—"}</dd></div>
            <div><dt>Kernel</dt><dd title={wsl.kernel}>{wsl.kernel || "—"}</dd></div>
            <div><dt>Tools</dt><dd>{wsl.forensicTools}</dd></div>
          </dl>
        </div>
      </aside>

      <main className="workspace">
        <section className="explorer panel">
          <div className="panel-heading">
            <div className="heading-title">
              <ListTree size={16} />
              <span>
                {module === "tools"
                  ? "BlackArch Tools"
                  : module === "files"
                    ? "File Explorer"
                    : module === "settings"
                      ? "Environment"
                      : "Case Explorer"}
              </span>
            </div>
          </div>
          {renderExplorer()}
        </section>

        <section className="center-stack">
          <TerminalPanel distro={distro} />
          <section className="timeline-panel panel">
            <div className="panel-heading">
              <div className="heading-title">
                <FileClock size={16} />
                <span>Chain of Custody / Timeline</span>
              </div>
              <span className="muted">{activeCase?.timeline.length ?? 0} events</span>
            </div>
            <div className="timeline-list">
              {activeCase?.timeline
                .slice()
                .reverse()
                .slice(0, 8)
                .map((event) => (
                  <div className="timeline-event" key={event.id}>
                    <span className={event.action.includes("mismatch") ? "event-dot danger" : "event-dot"} />
                    <time>{new Date(event.timestamp).toLocaleString()}</time>
                    <strong>{event.action}</strong>
                    <span className="timeline-detail" title={event.detail}>{event.detail}</span>
                  </div>
                ))}
              {!activeCase && <div className="empty-inline">Create a case to start custody tracking.</div>}
            </div>
          </section>
        </section>

        <aside className="inspector panel">
          <div className="panel-heading">
            <div className="heading-title">
              <Binary size={16} />
              <span>Evidence Inspector</span>
            </div>
          </div>

          {activeEvidence ? (
            <div className="inspector-content">
              <div className="evidence-title">
                <HardDrive size={28} />
                <div>
                  <strong>{activeEvidence.name}</strong>
                  <span>{activeEvidence.readOnly ? "Registered read-only" : "Writable source"}</span>
                </div>
                <span className={activeEvidence.verifiedAt ? "verified-pill" : "warning-pill"}>
                  {activeEvidence.verifiedAt ? "Verified" : "Unverified"}
                </span>
              </div>

              <dl className="metadata-list">
                <div><dt>Case</dt><dd>{activeCase?.id}</dd></div>
                <div><dt>Size</dt><dd>{formatBytes(activeEvidence.size)}</dd></div>
                <div><dt>Path</dt><dd title={activeEvidence.path}>{activeEvidence.path}</dd></div>
                <div><dt>Added</dt><dd>{new Date(activeEvidence.addedAt).toLocaleString()}</dd></div>
                <div><dt>Verified</dt><dd>{activeEvidence.verifiedAt ? new Date(activeEvidence.verifiedAt).toLocaleString() : "Never"}</dd></div>
              </dl>

              <div className="hash-card">
                <div className="hash-title"><Hash size={15} /> SHA-256</div>
                <code title={activeEvidence.sha256}>{shortHash(activeEvidence.sha256)}</code>
                <button
                  className="secondary-button full-width"
                  disabled={Boolean(busy)}
                  onClick={() => void verifyEvidence()}
                >
                  <ShieldCheck size={14} />
                  Verify integrity now
                </button>
              </div>
            </div>
          ) : (
            <div className="inspector-content">
              <div className="empty-state inspector-empty">
                <HardDrive size={30} />
                <strong>No evidence selected</strong>
                <span>Register a file to calculate and preserve its SHA-256.</span>
              </div>
            </div>
          )}

          <div className="environment-card">
            <div className="environment-title">
              <Laptop size={15} />
              <span>WSL environment</span>
            </div>
            <div className="environment-line">
              {wsl.online ? <CheckCircle2 size={14} /> : <CircleAlert size={14} />}
              <span>{wsl.message}</span>
            </div>
            <div className="environment-line">
              <Boxes size={14} />
              <span>{wsl.forensicTools} blackarch-forensic packages detected</span>
            </div>
            <div className="environment-line">
              <Database size={14} />
              <span>{wsl.home || "WSL home unavailable"}</span>
            </div>
          </div>
        </aside>
      </main>

      {(busy || notice) && (
        <div className={busy ? "toast busy" : "toast"} onClick={() => !busy && setNotice("")}>
          {busy && <RefreshCw className="spin" size={15} />}
          <span>{busy || notice}</span>
        </div>
      )}

      {newCaseOpen && (
        <div className="modal-backdrop" onMouseDown={() => setNewCaseOpen(false)}>
          <div className="modal" onMouseDown={(event) => event.stopPropagation()}>
            <div className="modal-icon"><ShieldCheck size={24} /></div>
            <h2>Create forensic case</h2>
            <p>A local case record and chain-of-custody journal will be created.</p>
            <label>
              Case name
              <input
                autoFocus
                value={newCaseName}
                onChange={(event) => setNewCaseName(event.target.value)}
                onKeyDown={(event) => event.key === "Enter" && void createCase()}
                placeholder="e.g. ERP Server Incident 2026-014"
              />
            </label>
            <div className="modal-actions">
              <button className="secondary-button" onClick={() => setNewCaseOpen(false)}>Cancel</button>
              <button className="primary-button" onClick={() => void createCase()} disabled={newCaseName.trim().length < 3}>
                <Plus size={14} />
                Create case
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
