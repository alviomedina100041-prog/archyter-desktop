import { useEffect, useRef, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import { listen, type UnlistenFn } from "@tauri-apps/api/event";
import { FitAddon } from "@xterm/addon-fit";
import { Terminal } from "@xterm/xterm";
import { RotateCcw, TerminalSquare } from "lucide-react";

interface Props {
  distro: string;
}

export function TerminalPanel({ distro }: Props) {
  const hostRef = useRef<HTMLDivElement>(null);
  const terminalRef = useRef<Terminal | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!hostRef.current) return;

    let disposed = false;
    let unlistenOutput: UnlistenFn | undefined;
    let unlistenExit: UnlistenFn | undefined;
    let unlistenError: UnlistenFn | undefined;

    const terminal = new Terminal({
      cursorBlink: true,
      cursorStyle: "block",
      fontFamily: '"Cascadia Mono", "Cascadia Code", "JetBrains Mono", Consolas, monospace',
      fontSize: 13,
      lineHeight: 1.18,
      scrollback: 20000,
      convertEol: false,
      allowProposedApi: false,
      theme: {
        background: "#03090d",
        foreground: "#d4e4e8",
        cursor: "#16f2a1",
        cursorAccent: "#03090d",
        selectionBackground: "#164e3f88",
        black: "#071014",
        red: "#ff5c6c",
        green: "#18e59a",
        yellow: "#eabf54",
        blue: "#5aa9ff",
        magenta: "#d58bff",
        cyan: "#42d9e8",
        white: "#d4e4e8",
        brightBlack: "#5f737c",
        brightGreen: "#5fffc2",
        brightCyan: "#8cf5ff",
      },
    });

    const fit = new FitAddon();
    terminal.loadAddon(fit);
    terminal.open(hostRef.current);
    terminalRef.current = terminal;

    const resize = () => {
      try {
        fit.fit();
        void invoke("terminal_resize", {
          cols: terminal.cols,
          rows: terminal.rows,
        });
      } catch {
        // Layout may be between frames while the window is resizing.
      }
    };

    const observer = new ResizeObserver(() => requestAnimationFrame(resize));
    observer.observe(hostRef.current);

    const input = terminal.onData((data) => {
      void invoke("terminal_write", { data }).catch((reason) => {
        setError(String(reason));
      });
    });

    const boot = async () => {
      unlistenOutput = await listen<string>("terminal://output", (event) => {
        terminal.write(event.payload);
      });
      unlistenExit = await listen("terminal://exit", () => {
        setConnected(false);
        terminal.writeln("\r\n\x1b[33m[terminal process exited]\x1b[0m");
      });
      unlistenError = await listen<string>("terminal://error", (event) => {
        setError(event.payload);
      });

      try {
        await invoke("terminal_start", { distro });
        if (!disposed) {
          setConnected(true);
          setError("");
          requestAnimationFrame(() => {
            resize();
            terminal.focus();
          });
        }
      } catch (reason) {
        setError(String(reason));
        terminal.writeln("\r\n\x1b[31mFailed to start WSL terminal\x1b[0m");
      }
    };

    void boot();

    return () => {
      disposed = true;
      observer.disconnect();
      input.dispose();
      unlistenOutput?.();
      unlistenExit?.();
      unlistenError?.();
      terminal.dispose();
      terminalRef.current = null;
      void invoke("terminal_stop");
    };
  }, [distro]);

  const reconnect = async () => {
    setConnected(false);
    setError("");
    try {
      await invoke("terminal_stop");
      await invoke("terminal_start", { distro });
      setConnected(true);
      terminalRef.current?.focus();
    } catch (reason) {
      setError(String(reason));
    }
  };

  return (
    <section className="terminal-panel panel">
      <div className="panel-heading terminal-heading">
        <div className="heading-title">
          <TerminalSquare size={16} />
          <span>BlackArch Terminal</span>
          <span className={connected ? "terminal-live" : "terminal-offline"}>
            {connected ? "PTY connected" : "offline"}
          </span>
        </div>
        <button className="icon-button" onClick={() => void reconnect()} title="Reconnect terminal">
          <RotateCcw size={15} />
        </button>
      </div>
      <div className="terminal-host" ref={hostRef} onClick={() => terminalRef.current?.focus()} />
      {error && <div className="terminal-error">{error}</div>}
    </section>
  );
}
