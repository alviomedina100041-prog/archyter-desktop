use std::path::Path;
use std::process::Command;

pub fn sha256_file(path: &Path) -> Result<String, String> {
    if !path.exists() {
        return Err(format!("Evidence does not exist: {}", path.display()));
    }

    #[cfg(target_os = "windows")]
    {
        let output = Command::new("certutil.exe")
            .arg("-hashfile")
            .arg(path)
            .arg("SHA256")
            .output()
            .map_err(|e| format!("Unable to start certutil: {e}"))?;

        if !output.status.success() {
            return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
        }

        let text = String::from_utf8_lossy(&output.stdout);
        for line in text.lines() {
            let compact: String = line.chars().filter(|c| c.is_ascii_hexdigit()).collect();
            if compact.len() == 64 {
                return Ok(compact.to_ascii_lowercase());
            }
        }
        Err("certutil completed but no SHA256 digest was found in its output".into())
    }

    #[cfg(not(target_os = "windows"))]
    {
        let output = Command::new("sha256sum")
            .arg(path)
            .output()
            .map_err(|e| format!("Unable to start sha256sum: {e}"))?;
        if !output.status.success() {
            return Err(String::from_utf8_lossy(&output.stderr).trim().to_string());
        }
        let text = String::from_utf8_lossy(&output.stdout);
        text.split_whitespace()
            .next()
            .filter(|v| v.len() == 64 && v.chars().all(|c| c.is_ascii_hexdigit()))
            .map(|v| v.to_ascii_lowercase())
            .ok_or_else(|| "sha256sum returned an unexpected result".into())
    }
}

pub fn verify(expected: &str, actual: &str) -> bool {
    normalize_hash(expected) == normalize_hash(actual)
}

fn normalize_hash(v: &str) -> String {
    v.chars().filter(|c| c.is_ascii_hexdigit()).collect::<String>().to_ascii_lowercase()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn verification_ignores_case_and_spaces() {
        assert!(verify("AA BB cc", "aabbcc"));
    }
}
