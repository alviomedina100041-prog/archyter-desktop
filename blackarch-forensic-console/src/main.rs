#![cfg_attr(target_os = "windows", windows_subsystem = "windows")]

#[cfg(target_os = "windows")]
mod windows_app;

#[cfg(target_os = "windows")]
fn main() {
    if let Err(error) = windows_app::run() {
        // GUI subsystem has no console. Emit to a crash note beside cwd.
        let _ = std::fs::write("blackarch-forensic-console-error.txt", format!("{error}\n"));
    }
}

#[cfg(not(target_os = "windows"))]
fn main() {
    println!("BlackArch Forensic Console is a Windows 11 + WSL2 desktop application.");
    println!("Core library modules can still be tested on this platform with \`cargo test --lib\`.");
}
