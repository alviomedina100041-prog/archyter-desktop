use std::{env, fs, path::PathBuf, process::Command};

fn main() {
    println!("cargo:rerun-if-changed=assets/blackarch.ico");
    println!("cargo:rerun-if-changed=assets/app.manifest");

    if env::var("CARGO_CFG_TARGET_OS").as_deref() != Ok("windows") {
        return;
    }

    let out = PathBuf::from(env::var("OUT_DIR").expect("OUT_DIR"));
    let rc = out.join("blackarch_forensic_console.rc");
    let manifest = fs::canonicalize("assets/app.manifest").unwrap_or_else(|_| PathBuf::from("assets/app.manifest"));
    let icon = fs::canonicalize("assets/blackarch.ico").unwrap_or_else(|_| PathBuf::from("assets/blackarch.ico"));
    let body = format!(
        "1 ICON \"{}\"\n1 24 \"{}\"\n",
        icon.display().to_string().replace('\\', "\\\\"),
        manifest.display().to_string().replace('\\', "\\\\")
    );
    if fs::write(&rc, body).is_err() { return; }

    let target_env = env::var("CARGO_CFG_TARGET_ENV").unwrap_or_default();
    if target_env == "msvc" {
        let res = out.join("blackarch_forensic_console.res");
        let status = Command::new("rc.exe")
            .arg("/nologo")
            .arg(format!("/fo{}", res.display()))
            .arg(&rc)
            .status();
        if matches!(status, Ok(s) if s.success()) {
            println!("cargo:rustc-link-arg={}", res.display());
        } else {
            println!("cargo:warning=rc.exe unavailable; build will continue without embedded EXE icon/manifest");
        }
    } else {
        let obj = out.join("blackarch_forensic_console_res.o");
        let status = Command::new("windres")
            .arg(&rc)
            .arg(&obj)
            .status();
        if matches!(status, Ok(s) if s.success()) {
            println!("cargo:rustc-link-arg={}", obj.display());
        } else {
            println!("cargo:warning=windres unavailable; build will continue without embedded EXE icon/manifest");
        }
    }
}
