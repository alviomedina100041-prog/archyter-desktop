use crate::WslStatus;
use anyhow::{bail, Context, Result};
use std::process::Command;

fn validate_distro(distro: &str) -> Result<()> {
    if distro.is_empty()
        || !distro
            .chars()
            .all(|c| c.is_ascii_alphanumeric() || matches!(c, '-' | '_' | '.'))
    {
        bail!("invalid WSL distro name");
    }
    Ok(())
}

pub fn probe_wsl(distro: &str) -> Result<WslStatus> {
    validate_distro(distro)?;

    let script = r#"printf 'USER=%s\nKERNEL=%s\nHOME=%s\nTOOLS=%s\n' "$(whoami)" "$(uname -r)" "$HOME" "$(pacman -Qg blackarch-forensic 2>/dev/null | awk '{print $2}' | sort -u | wc -l)""#;
    let output = Command::new("wsl.exe")
        .args(["-d", distro, "--", "bash", "-lc", script])
        .output()
        .with_context(|| "failed to execute wsl.exe")?;

    if !output.status.success() {
        return Ok(WslStatus {
            online: false,
            distro: distro.to_string(),
            user: String::new(),
            kernel: String::new(),
            home: String::new(),
            forensic_tools: 0,
            message: String::from_utf8_lossy(&output.stderr).trim().to_string(),
        });
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut status = WslStatus {
        online: true,
        distro: distro.to_string(),
        user: String::new(),
        kernel: String::new(),
        home: String::new(),
        forensic_tools: 0,
        message: "WSL2 / BlackArch ready".to_string(),
    };

    for line in stdout.lines() {
        if let Some((key, value)) = line.split_once('=') {
            match key {
                "USER" => status.user = value.to_string(),
                "KERNEL" => status.kernel = value.to_string(),
                "HOME" => status.home = value.to_string(),
                "TOOLS" => status.forensic_tools = value.trim().parse().unwrap_or(0),
                _ => {}
            }
        }
    }

    Ok(status)
}

pub fn list_forensic_tools(distro: &str) -> Result<Vec<String>> {
    validate_distro(distro)?;
    let script =
        r#"pacman -Qg blackarch-forensic 2>/dev/null | awk '{print $2}' | sort -u"#;
    let output = Command::new("wsl.exe")
        .args(["-d", distro, "--", "bash", "-lc", script])
        .output()
        .with_context(|| "failed to query BlackArch forensic tools")?;

    if !output.status.success() {
        bail!("{}", String::from_utf8_lossy(&output.stderr).trim());
    }

    Ok(String::from_utf8_lossy(&output.stdout)
        .lines()
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .map(ToOwned::to_owned)
        .collect())
}
