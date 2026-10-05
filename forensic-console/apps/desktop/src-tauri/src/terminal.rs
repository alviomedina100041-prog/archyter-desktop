use portable_pty::{native_pty_system, Child, CommandBuilder, MasterPty, PtySize};
use std::{
    io::{Read, Write},
    sync::{Arc, Mutex},
    thread,
};
use tauri::{AppHandle, Emitter, State};

struct TerminalSession {
    master: Mutex<Box<dyn MasterPty + Send>>,
    writer: Mutex<Box<dyn Write + Send>>,
    child: Mutex<Box<dyn Child + Send + Sync>>,
}

#[derive(Default)]
pub struct TerminalState {
    session: Mutex<Option<Arc<TerminalSession>>>,
}

fn valid_distro(distro: &str) -> bool {
    !distro.is_empty()
        && distro
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '.'))
}

#[tauri::command]
pub fn terminal_start(
    app: AppHandle,
    state: State<'_, TerminalState>,
    distro: String,
) -> Result<(), String> {
    if !valid_distro(&distro) {
        return Err("invalid WSL distro name".to_string());
    }

    {
        let mut slot = state.session.lock().map_err(|_| "terminal state poisoned")?;
        if let Some(existing) = slot.as_ref() {
            let mut child = existing.child.lock().map_err(|_| "terminal child poisoned")?;
            if child
                .try_wait()
                .map_err(|error| error.to_string())?
                .is_none()
            {
                return Ok(());
            }
        }
        *slot = None;
    }

    let pty_system = native_pty_system();
    let pair = pty_system
        .openpty(PtySize {
            rows: 36,
            cols: 120,
            pixel_width: 0,
            pixel_height: 0,
        })
        .map_err(|error| error.to_string())?;

    let mut cmd = CommandBuilder::new("wsl.exe");
    cmd.arg("-d");
    cmd.arg(&distro);
    cmd.arg("--cd");
    cmd.arg("~");
    cmd.arg("--");
    cmd.arg("env");
    cmd.arg("TERM=xterm-256color");
    cmd.arg("COLORTERM=truecolor");
    cmd.arg("bash");
    cmd.arg("-l");

    let child = pair
        .slave
        .spawn_command(cmd)
        .map_err(|error| error.to_string())?;
    let mut reader = pair
        .master
        .try_clone_reader()
        .map_err(|error| error.to_string())?;
    let writer = pair
        .master
        .take_writer()
        .map_err(|error| error.to_string())?;

    let session = Arc::new(TerminalSession {
        master: Mutex::new(pair.master),
        writer: Mutex::new(writer),
        child: Mutex::new(child),
    });

    {
        let mut slot = state.session.lock().map_err(|_| "terminal state poisoned")?;
        *slot = Some(session);
    }

    thread::spawn(move || {
        let mut buffer = [0_u8; 8192];
        loop {
            match reader.read(&mut buffer) {
                Ok(0) => break,
                Ok(count) => {
                    let chunk = String::from_utf8_lossy(&buffer[..count]).into_owned();
                    let _ = app.emit("terminal://output", chunk);
                }
                Err(error) => {
                    let _ = app.emit("terminal://error", error.to_string());
                    break;
                }
            }
        }
        let _ = app.emit("terminal://exit", ());
    });

    Ok(())
}

#[tauri::command]
pub fn terminal_write(state: State<'_, TerminalState>, data: String) -> Result<(), String> {
    let slot = state.session.lock().map_err(|_| "terminal state poisoned")?;
    let session = slot
        .as_ref()
        .cloned()
        .ok_or_else(|| "terminal is not running".to_string())?;
    drop(slot);

    let mut writer = session.writer.lock().map_err(|_| "terminal writer poisoned")?;
    writer
        .write_all(data.as_bytes())
        .and_then(|_| writer.flush())
        .map_err(|error| error.to_string())
}

#[tauri::command]
pub fn terminal_resize(
    state: State<'_, TerminalState>,
    cols: u16,
    rows: u16,
) -> Result<(), String> {
    let slot = state.session.lock().map_err(|_| "terminal state poisoned")?;
    let session = slot
        .as_ref()
        .cloned()
        .ok_or_else(|| "terminal is not running".to_string())?;
    drop(slot);

    let resize_result = {
        let master = session
            .master
            .lock()
            .map_err(|_| "terminal master poisoned")?;
        master
            .resize(PtySize {
                rows: rows.max(2),
                cols: cols.max(2),
                pixel_width: 0,
                pixel_height: 0,
            })
            .map_err(|error| error.to_string())
    };

    resize_result
}

#[tauri::command]
pub fn terminal_stop(state: State<'_, TerminalState>) -> Result<(), String> {
    let session = state
        .session
        .lock()
        .map_err(|_| "terminal state poisoned")?
        .take();

    if let Some(session) = session {
        let mut child = session.child.lock().map_err(|_| "terminal child poisoned")?;
        let _ = child.kill();
    }

    Ok(())
}
