// Prevents additional console window on Windows in release, DO NOT REMOVE!!
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use tauri::{
    menu::{Menu, MenuItem},
    tray::{MouseButton, MouseButtonState, TrayIconBuilder, TrayIconEvent},
    Manager,
};

fn main() {
    tauri::Builder::default()
        .setup(|app| {
            // Build Context Menu for Windows System Tray
            let quit_item = MenuItem::with_id(app, "quit", "Quit AitMate", true, None::<&str>)?;
            let show_item = MenuItem::with_id(app, "show", "Open Quick Assistant (Alt+A)", true, None::<&str>)?;
            let tray_menu = Menu::with_items(app, &[&show_item, &quit_item])?;

            // Register System Tray Icon
            let _tray = TrayIconBuilder::new()
                .menu(&tray_menu)
                .show_menu_on_left_click(false)
                .tooltip("AitMate Desktop AI Assistant")
                .on_menu_event(|app, event| match event.id.as_ref() {
                    "quit" => {
                        app.exit(0);
                    }
                    "show" => {
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                    _ => {}
                })
                .on_tray_icon_event(|tray, event| {
                    if let TrayIconEvent::Click {
                        button: MouseButton::Left,
                        button_state: MouseButtonState::Up,
                        ..
                    } = event
                    {
                        let app = tray.app_handle();
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.show();
                            let _ = window.set_focus();
                        }
                    }
                })
                .build(app)?;

            Ok(())
        })
        .on_window_event(|window, event| match event {
            tauri::WindowEvent::CloseRequested { api, .. } => {
                // Keep app alive in background: Hide to tray instead of quitting!
                api.prevent_close();
                let _ = window.hide();
            }
            _ => {}
        })
        .run(tauri::generate_context!())
        .expect("error while running AitMate desktop application");
}
