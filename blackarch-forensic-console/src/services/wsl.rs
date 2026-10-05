use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

#[derive(Debug, Clone)]
pub struct CommandResult {
    pub success: bool,
    pub status_code: Option<i32>,
    pub stdout: String,
    pub stderr: String,
    pub elapsed: Duration,
}

impl CommandResult {
    pub fn merged_text(&self) -> String {
        match (self.stdout.trim().is_empty(), self.stderr.trim().is_empty()) {
            (false, false) => format!("{}\n{}", self.stdout.trim_end(), self.stderr.trim_end()),
            (false, true) => self.stdout.trim_end().to_string(),
            (true, false) => self.stderr.trim_end().to_string(),
            (true, true) => String::new(),
        }
    }
}

/// Run a shell command inside the configured WSL distribution.
///
/// This accepts shell syntax because it backs the explicit interactive terminal.
/// Automated workflows should call dedicated services instead of interpolating untrusted data.
pub fn run_shell(distro: &str, shell_command: &str) -> std::io::Result<CommandResult> {
    let start = Instant::now();
    #[cfg(target_os = "windows")]
    let output = Command::new("wsl.exe")
        .arg("-d").arg(distro).arg("--").arg("bash").arg("-lc").arg(shell_command)
        .stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::piped()).output()?;

    #[cfg(not(target_os = "windows"))]
    let output = Command::new("bash")
        .arg("-lc").arg(shell_command)
        .stdin(Stdio::null()).stdout(Stdio::piped()).stderr(Stdio::piped()).output()?;

    Ok(CommandResult {
        success: output.status.success(),
        status_code: output.status.code(),
        stdout: String::from_utf8_lossy(&output.stdout).into_owned(),
        stderr: String::from_utf8_lossy(&output.stderr).into_owned(),
        elapsed: start.elapsed(),
    })
}

pub fn probe_blackarch(distro: &str) -> std::io::Result<CommandResult> {
    run_shell(
        distro,
        r#"printf 'OS='; . /etc/os-release 2>/dev/null; printf '%s\n' "${PRETTY_NAME:-Linux}"; printf 'KERNEL='; uname -r; printf 'USER='; id -un; printf 'TOOLS='; pacman -Qg blackarch-forensic 2>/dev/null | wc -l"#,
    )
}

pub fn open_interactive_terminal(distro: &str) -> std::io::Result<()> {
    #[cfg(target_os = "windows")]
    {
        Command::new("wt.exe").arg("wsl.exe").arg("-d").arg(distro).spawn()?;
        Ok(())
    }
    #[cfg(not(target_os = "windows"))]
    {
        let _ = distro;
        Ok(())
    }
}
