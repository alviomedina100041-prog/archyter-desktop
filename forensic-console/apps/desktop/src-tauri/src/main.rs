mod commands;
mod terminal;

#[cfg_attr(not(debug_assertions), windows_subsystem = "windows")]
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .manage(terminal::TerminalState::default())
        .invoke_handler(tauri::generate_handler![
            commands::list_cases,
            commands::create_case,
            commands::add_evidence,
            commands::verify_evidence,
            commands::list_dir,
            commands::read_hex_chunk,
            commands::probe_wsl_status,
            commands::forensic_tools,
            terminal::terminal_start,
            terminal::terminal_write,
            terminal::terminal_resize,
            terminal::terminal_stop,
        ])
        .run(tauri::generate_context!())
        .expect("failed to run BlackArch Forensic Console");
}
