pub mod games;
pub mod story;
pub fn install() {
    story::install();
    games::install();
}

#[cfg(test)]
fn install_for_tests() {
    static INIT: std::sync::Once = std::sync::Once::new();
    INIT.call_once(install);
}

#[cfg(test)]
mod integration_tests {
    use ling_chat_main::ai_service::game_system::script_engine::{
        events, extension, schema, validate,
    };

    #[test]
    fn registered_events_are_visible_to_host_schema_and_factory() {
        super::install_for_tests();
        extension::register_events();
        let schema = schema::build_schema();
        for kind in [
            "force_choice",
            "console_window",
            "watch_file",
            "poem_game",
            "window_title",
        ] {
            assert!(
                schema.events.iter().any(|event| event.type_key == kind),
                "{kind}"
            );
            assert!(
                events::create_event(kind, serde_json::json!({})).is_some(),
                "{kind}"
            );
        }
    }

    #[test]
    fn host_validator_keeps_native_window_authorization_after_extraction() {
        super::install_for_tests();
        let root = tempfile::tempdir().unwrap();
        std::fs::create_dir(root.path().join("Chapters")).unwrap();
        std::fs::write(
            root.path().join("story_config.yaml"),
            "script_name: Example\nintro_chapter: start\n",
        )
        .unwrap();
        std::fs::write(
            root.path().join("Chapters/start.yaml"),
            "events:\n- type: console_window\n  text: hello\n- type: chapter_end\n  next: end\n",
        )
        .unwrap();
        let report = validate::validate(root.path(), root.path(), "example", &Default::default());
        assert!(report
            .diagnostics
            .iter()
            .any(|d| d.code == "console_window.not_authorized"));
    }
}
