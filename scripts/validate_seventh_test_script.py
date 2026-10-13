#!/usr/bin/env python3
"""Validate the DDLC-style LingChat script graph, media contract, and poem pool."""

from __future__ import annotations

import argparse
import tomllib
import sys
from pathlib import Path
from typing import Any

import yaml

EVENT_TYPES = {
    "achievement",
    "ai_dialogue",
    "ambient",
    "background",
    "background_effect",
    "chapter_end",
    "console_window",
    "character_file",
    "choices",
    "dialogue",
    "force_choice",
    "free_dialogue",
    "glitch_window",
    "horror_log",
    "input",
    "jumpscare",
    "main_menu_effect",
    "modify_character",
    "music",
    "narration",
    "player",
    "poem_game",
    "present_pic",
    "random_var",
    "set_variable",
    "sound",
    "voice_shift",
    "wait",
    "watch_file",
    "window_title",
}
MEDIA_FIELDS = {
    "imagePath",
    "musicPath",
    "glitchMusicPath",
    "soundPath",
    "ambientPath",
    "backgroundPath",
    "warmStickerPath",
    "scriptStickerPath",
    "voidStickerPath",
}
POEM_MODES = {"normal", "act2", "act2_final"}
COMPATIBILITY_CHAPTERS = {"special_poem_a2b"}


def load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("root must be a mapping")
    return data


WINDOWS_DEVICE_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
WINDOWS_UNSAFE_NAME_CHARS = set('<>:"/\\|?*')


def valid_chr_name(name: str) -> bool:
    if not 1 <= len(name) <= 64 or not name.lower().endswith(".chr"):
        return False
    if Path(name).name != name or name[0] == " " or name[-1] in {" ", "."}:
        return False
    if any(char in WINDOWS_UNSAFE_NAME_CHARS or ord(char) < 32 for char in name):
        return False
    stem = name[:-4]
    if not stem or stem[-1] in {" ", "."}:
        return False
    return stem.split(".", 1)[0].upper() not in WINDOWS_DEVICE_NAMES


def value_string(value: Any) -> str:
    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def evaluate_condition(condition: str, variables: dict[str, Any]) -> bool:
    """Mirror the small condition grammar used by the Rust script engine."""

    condition = condition.strip()
    if not condition:
        return True
    if "||" in condition:
        return any(evaluate_condition(part, variables) for part in condition.split("||"))
    if "&&" in condition:
        return all(evaluate_condition(part, variables) for part in condition.split("&&"))
    for operator in (">=", "<=", ">", "<"):
        if operator in condition:
            name, expected = condition.split(operator, 1)
            current = variables.get(name.strip())
            try:
                left = float(current)
                right = float(expected.strip())
            except (TypeError, ValueError):
                return False
            return {
                ">=": left >= right,
                "<=": left <= right,
                ">": left > right,
                "<": left < right,
            }[operator]
    if "!=" in condition:
        name, expected = condition.split("!=", 1)
        if name.strip() not in variables:
            return True
        return value_string(variables[name.strip()]) != expected.strip().strip("\"'")
    if "==" in condition:
        name, expected = condition.split("==", 1)
        if name.strip() not in variables:
            return False
        return value_string(variables[name.strip()]) == expected.strip().strip("\"'")
    value = variables.get(condition)
    return value is not None and (value if isinstance(value, bool) else True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "script_root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "packages/seventh-test-script/scripts/seventh-test-script",
    )
    parser.add_argument("--global-data", type=Path)
    args = parser.parse_args()

    root = args.script_root.resolve()
    chapters_dir = root / "Chapters"
    errors: list[str] = []
    warnings: list[str] = []

    try:
        config = load_yaml(root / "story_config.yaml")
        word_data = load_yaml(root / "poem_words.yaml")
    except Exception as exc:
        print(f"configuration parse failed: {exc}", file=sys.stderr)
        return 1

    try:
        manifest = tomllib.loads((root.parent.parent / "manifest.toml").read_text(encoding="utf-8"))
        if manifest.get("story_api_version") != 1 or manifest.get("resources") != ["scripts"]:
            errors.append("manifest.toml must declare native story API v1 and scripts-only resources")
    except Exception as exc:
        errors.append(f"unified story manifest is invalid: {exc}")

    chapters: dict[str, dict[str, Any]] = {}
    for path in sorted(chapters_dir.glob("*.yaml")):
        try:
            chapters[path.stem] = load_yaml(path)
        except Exception as exc:
            errors.append(f"{path.name}: YAML parse failed: {exc}")

    intro = config.get("intro_chapter")
    if intro not in chapters:
        errors.append(f"intro_chapter does not exist: {intro!r}")

    if config.get("main_character") != "DeepSeek":
        errors.append("story_config.main_character must be DeepSeek")
    if args.global_data:
        # 主角色库在 <bin>/data/game_data/characters/ 下（与引擎 characters_dir() 一致）
        deepseek_settings = (
            args.global_data / "game_data" / "characters" / "DeepSeek" / "settings.yml"
        )
        if not deepseek_settings.is_file():
            errors.append(
                "global character required by main_character is missing: "
                f"{deepseek_settings}"
            )

    roster_console = next(
        (
            event
            for event in chapters.get("a1_day1", {}).get("events", [])
            if isinstance(event, dict)
            and event.get("type") == "console_window"
            and "characters: 2" in str(event.get("text", ""))
        ),
        None,
    )
    if not roster_console or roster_console.get("style") != "blood_cmd":
        errors.append("a1_day1 RUNTIME roster console must use style: blood_cmd")

    weekend_effects = [
        event
        for event in chapters.get("a1_weekend", {}).get("events", [])
        if isinstance(event, dict) and event.get("type") == "background_effect"
    ]
    persistent_blood = next(
        (event for event in weekend_effects if "BloodUI" in str(event.get("effect", ""))),
        None,
    )
    if not persistent_blood or "duration" in persistent_blood:
        errors.append("a1_weekend BloodUI must stay persistent through the final narration")
    if not weekend_effects or str(weekend_effects[-1].get("effect", "")).lower() != "none":
        errors.append("a1_weekend must clear BloodUI before chapter_end")

    force_choices = [
        (chapter_id, event)
        for chapter_id, chapter in chapters.items()
        for event in chapter.get("events", [])
        if isinstance(event, dict) and event.get("type") == "force_choice"
    ]
    required_rigged_chapters = {
        "a1_day1", "a1_weekend", "a2_day1", "a2_day3", "a3_space",
        "a4_turn", "a4_final_release", "a4_final_loop",
    }
    if not required_rigged_chapters.issubset({name for name, _ in force_choices}):
        errors.append("RigMouse is missing from an opening, middle or terminal scene")
    for chapter_id, event in force_choices:
        forced = event.get("forced")
        options = event.get("options")
        matching = (
            [option for option in options if isinstance(option, dict) and option.get("text") == forced]
            if isinstance(options, list)
            else []
        )
        if not isinstance(options, list) or len(options) < 3 or len(matching) != 1:
            errors.append(
                f"{chapter_id}: force_choice needs 3+ options and exactly one forced text match"
            )

    delete_prompt_events = chapters.get("a3_delete_prompt", {}).get("events", [])
    anchor_indexes = [
        index
        for index, event in enumerate(delete_prompt_events)
        if isinstance(event, dict)
        and event.get("type") == "character_file"
        and event.get("action") == "ensure"
        and event.get("file") == "ql.chr"
        and event.get("condition") == "delete_permission == true"
    ]
    stop_indexes = [
        index
        for index, event in enumerate(delete_prompt_events)
        if isinstance(event, dict)
        and event.get("type") == "watch_file"
        and event.get("action") == "stop"
    ]
    open_indexes = [
        index
        for index, event in enumerate(delete_prompt_events)
        if isinstance(event, dict)
        and event.get("type") == "character_file"
        and event.get("action") == "open_folder"
    ]
    if not all([anchor_indexes, stop_indexes, open_indexes]) or not (
        min(anchor_indexes) < min(stop_indexes) < min(open_indexes)
    ):
        errors.append(
            "a3_delete_prompt must stage ql.chr before stopping MAIN.chr watch and opening the folder"
        )

    a2_end_events = chapters.get("a2_end", {}).get("events", [])
    ql_delete_indexes = [
        index
        for index, event in enumerate(a2_end_events)
        if isinstance(event, dict)
        and event.get("type") == "character_file"
        and event.get("action") == "delete"
        and event.get("file") == "ql.chr"
    ]
    ql_anchor_indexes = [
        index
        for index, event in enumerate(a2_end_events)
        if isinstance(event, dict)
        and event.get("type") == "character_file"
        and event.get("action") == "ensure"
        and event.get("file") == "ql.chr"
    ]
    a2_menu_indexes = [
        index
        for index, event in enumerate(a2_end_events)
        if isinstance(event, dict) and event.get("type") == "main_menu_effect"
    ]
    if not all([ql_delete_indexes, ql_anchor_indexes, a2_menu_indexes]) or not (
        min(ql_delete_indexes) < max(ql_anchor_indexes) < min(a2_menu_indexes)
    ):
        errors.append(
            "a2_end must restage ql.chr after the deletion beat and before the Act 3 menu"
        )

    boot_events = chapters.get("a1_boot", {}).get("events", [])
    boot_route = next(
        (
            event
            for event in boot_events
            if isinstance(event, dict)
            and event.get("type") == "chapter_end"
            and event.get("end_type") == "branching"
        ),
        None,
    )
    route_cases = [
        ({"playthrough": 1, "current_act": 1}, "a0_marker_migration"),
        (
            {"playthrough": 1, "current_act": 1, "marker_schema_version": 1},
            "a1_guard",
        ),
        (
            {"playthrough": 7, "current_act": 2, "marker_schema_version": 1},
            "a2_guard",
        ),
        (
            {"playthrough": 7, "current_act": 3, "marker_schema_version": 1},
            "a3_guard",
        ),
        (
            {"playthrough": 7, "current_act": 4, "marker_schema_version": 1},
            "a4_legacy_recovery",
        ),
        (
            {
                "playthrough": 7,
                "current_act": 4,
                "last_ending": "release",
                "marker_schema_version": 1,
            },
            "a4_main",
        ),
        (
            {
                "playthrough": 7,
                "current_act": 4,
                "last_ending": "loop",
                "marker_schema_version": 1,
            },
            "a4_loop_guard",
        ),
        (
            {
                "playthrough": 7,
                "current_act": 4,
                "last_ending": "loop",
                "act4_done": True,
                "marker_schema_version": 1,
            },
            "a5_lingering",
        ),
        ({"playthrough": 5, "marker_schema_version": 1}, "a4_legacy_recovery"),
        ({"playthrough": 4, "marker_schema_version": 1}, "a4_legacy_recovery"),
        (
            {
                "playthrough": 4,
                "last_ending": "release",
                "marker_schema_version": 1,
            },
            "a4_main",
        ),
        (
            {
                "playthrough": 4,
                "last_ending": "loop",
                "marker_schema_version": 1,
            },
            "a4_loop_guard",
        ),
        (
            {
                "playthrough": 4,
                "last_ending": "watcher",
                "marker_schema_version": 1,
            },
            "a5_lingering",
        ),
        (
            {
                "playthrough": 3,
                "current_act": 3,
                "marker_schema_version": 1,
                "marker_checkpoint": "act2_to_act3",
            },
            "a0_checkpoint_recovery",
        ),
    ]
    if not isinstance(boot_route, dict):
        errors.append("a1_boot: missing branching route event")
    else:
        for variables, expected in route_cases:
            actual = None
            for option in boot_route.get("options", []):
                if not isinstance(option, dict):
                    continue
                condition = option.get("condition")
                if option.get("default") is True or (
                    isinstance(condition, str) and evaluate_condition(condition, variables)
                ):
                    actual = option.get("next")
                    break
            if actual != expected:
                errors.append(
                    f"a1_boot route mismatch for {variables}: expected {expected!r}, got {actual!r}"
                )

    settings = config.get("script_settings")
    if not isinstance(settings, dict):
        errors.append("script_settings must be a mapping")
        settings = {}
    persistent_vars = settings.get("persistent_vars", [])
    if not isinstance(persistent_vars, list) or not {
        "marker_schema_version",
        "marker_checkpoint",
    }.issubset(set(persistent_vars)):
        errors.append(
            "persistent_vars must include marker_schema_version and marker_checkpoint"
        )

    entry_error = settings.get("entry_error", {})
    if (
        not isinstance(entry_error, dict)
        or entry_error.get("variable") != "act4_done"
        or "act4_done" not in persistent_vars
        or "SCRIPT_CORRUPTED" not in str(entry_error.get("message", ""))
    ):
        errors.append("terminal entry_error must use persisted act4_done and show SCRIPT_CORRUPTED")
    for ending in ("a4_final_release", "a4_final_loop", "a5_lingering"):
        events = chapters.get(ending, {}).get("events", [])
        assignments = [action.get("content") for event in events
                       for option in event.get("options", [])
                       for action in option.get("actions", [])
                       if action.get("type") == "set_var"]
        if "act4_done = true" not in assignments or "current_act = 5" not in assignments:
            errors.append(f"{ending}: terminal error state must be committed")
        if not any(event.get("type") == "main_menu_effect" and event.get("theme") == "blood"
                   for event in events):
            errors.append(f"{ending}: damaged red menu must persist after completion")
        if any(event.get("musicPath") == "Twilight.ogg" for event in events):
            errors.append(f"{ending}: the new corruption ending must not resume the farewell cue")

    declared_character_files = settings.get("character_files", [])
    if not isinstance(declared_character_files, list) or not all(
        isinstance(name, str) for name in declared_character_files
    ):
        errors.append("script_settings.character_files must be a string list")
        declared_character_files = []
    if len(declared_character_files) != len(set(declared_character_files)):
        errors.append("script_settings.character_files contains duplicates")
    for name in declared_character_files:
        if not valid_chr_name(name):
            errors.append(f"invalid declared character marker: {name!r}")
            continue
        template = root / "CharacterFiles" / name
        if not template.is_file():
            errors.append(f"missing CharacterFiles template: {name!r}")
        elif template.stat().st_size > 64 * 1024:
            errors.append(f"CharacterFiles template exceeds 64 KiB: {name!r}")

    role_avatar_dirs: dict[str, Path] = {}
    for role_settings_path in (root / "characters").glob("*/settings.yml"):
        try:
            role_settings = load_yaml(role_settings_path)
        except Exception as exc:
            errors.append(f"{role_settings_path.name}: role settings parse failed: {exc}")
            continue
        role_key = role_settings.get("script_role_key")
        if isinstance(role_key, str):
            role_avatar_dirs[role_key] = role_settings_path.parent / "avatar"

    available_media = {
        path.name
        for path in (root / "Assets").rglob("*")
        if path.is_file()
    }
    if args.global_data and args.global_data.exists():
        available_media.update(
            path.name for path in args.global_data.rglob("*") if path.is_file()
        )

    references: list[tuple[str, str]] = []
    poem_events: list[tuple[str, dict[str, Any]]] = []
    terminal_chapters: set[str] = set()
    uses_glitch_windows = False
    for chapter_id, chapter in chapters.items():
        events = chapter.get("events")
        if not isinstance(events, list):
            errors.append(f"{chapter_id}: events must be a list")
            continue
        for index, event in enumerate(events, start=1):
            if not isinstance(event, dict):
                errors.append(f"{chapter_id} event {index}: event must be a mapping")
                continue
            event_type = event.get("type")
            if event_type not in EVENT_TYPES:
                errors.append(f"{chapter_id} event {index}: unknown type {event_type!r}")
            direct_next = event.get("next_chapter")
            if isinstance(direct_next, str):
                if direct_next == "end":
                    terminal_chapters.add(chapter_id)
                else:
                    references.append((chapter_id, direct_next))
            options = event.get("options")
            if event_type == "chapter_end" and isinstance(options, list):
                for option in options:
                    target = option.get("next") if isinstance(option, dict) else None
                    if isinstance(target, str):
                        if target == "end":
                            terminal_chapters.add(chapter_id)
                        else:
                            references.append((chapter_id, target))
            # watch_file 的 on_missing 也是章节引用；stop 事件可省略 file/目标。
            if event_type == "watch_file":
                watch_action = event.get("action", "start")
                if watch_action not in {"start", "stop"}:
                    errors.append(
                        f"{chapter_id} event {index}: invalid watch_file action {watch_action!r}"
                    )
                if watch_action == "start":
                    watch_file = event.get("file")
                    watch_target = event.get("on_missing")
                    if watch_file not in declared_character_files:
                        errors.append(
                            f"{chapter_id} event {index}: watch_file marker must be declared"
                        )
                    if not isinstance(watch_target, str) or not watch_target:
                        errors.append(
                            f"{chapter_id} event {index}: watch_file start requires on_missing"
                        )
                    else:
                        references.append((chapter_id, watch_target))
            for field in MEDIA_FIELDS:
                value = event.get(field)
                if not isinstance(value, str) or value in {"", "none", "None"}:
                    continue
                if Path(value).name not in available_media:
                    errors.append(
                        f"{chapter_id} event {index}: missing media {field}={value!r}"
                    )
            if event_type in {"dialogue", "modify_character"}:
                role_key = event.get("character")
                emotion = event.get("emotion")
                avatar_dir = role_avatar_dirs.get(role_key) if isinstance(role_key, str) else None
                if avatar_dir is not None and isinstance(emotion, str):
                    if not (avatar_dir / f"{emotion}.webp").is_file():
                        errors.append(
                            f"{chapter_id} event {index}: missing {role_key} emotion {emotion!r}"
                        )

            if event_type == "character_file":
                action = event.get("action")
                if action not in {"ensure", "exists", "delete", "open_folder"}:
                    errors.append(
                        f"{chapter_id} event {index}: invalid character_file action {action!r}"
                    )
                file_name = event.get("file")
                if action != "open_folder":
                    if file_name not in declared_character_files:
                        errors.append(
                            f"{chapter_id} event {index}: undeclared character marker {file_name!r}"
                        )
                if action == "exists":
                    result_var = event.get("resultVar")
                    if (
                        not isinstance(result_var, str)
                        or not 1 <= len(result_var) <= 128
                        or any(ord(char) < 32 for char in result_var)
                    ):
                        errors.append(
                            f"{chapter_id} event {index}: exists must provide a safe 1..128 character resultVar"
                        )

            if event_type == "main_menu_effect":
                if event.get("theme") not in {"normal", "blood", "ghost"}:
                    errors.append(
                        f"{chapter_id} event {index}: invalid main-menu theme {event.get('theme')!r}"
                    )
                message = event.get("message", "")
                if (
                    not isinstance(message, str)
                    or len(message) > 160
                    or any(ord(char) < 32 and char not in "\n\t" for char in message)
                ):
                    errors.append(
                        f"{chapter_id} event {index}: menu message must be safe plain text of at most 160 characters"
                    )

            if event_type in ("glitch_window", "console_window"):
                uses_glitch_windows = True
                if event_type == "glitch_window" and event.get("style") not in {"terminal", "error"}:
                    errors.append(
                        f"{chapter_id} event {index}: invalid glitch-window style {event.get('style')!r}"
                    )
                if event_type == "console_window" and event.get("style", "console") not in {
                    "console",
                    "blood_cmd",
                    "error",
                    "warning",
                    "notepad",
                }:
                    errors.append(
                        f"{chapter_id} event {index}: invalid native-window style {event.get('style')!r}"
                    )
                count = event.get("count", 1)
                lifetime = event.get("lifetime", 6.0)
                interval = event.get("interval", 0.18)
                window_label = "glitch-window" if event_type == "glitch_window" else "native-window"
                min_lifetime = 0.5 if event_type == "glitch_window" else 1.0
                if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 4:
                    errors.append(
                        f"{chapter_id} event {index}: {window_label} count must be 1..4"
                    )
                if (
                    isinstance(lifetime, bool)
                    or not isinstance(lifetime, (int, float))
                    or not min_lifetime <= lifetime <= 12.0
                ):
                    errors.append(
                        f"{chapter_id} event {index}: {window_label} lifetime must be {min_lifetime:g}..12"
                    )
                if (
                    isinstance(interval, bool)
                    or not isinstance(interval, (int, float))
                    or not 0.05 <= interval <= 1.0
                ):
                    errors.append(
                        f"{chapter_id} event {index}: {window_label} interval must be 0.05..1"
                    )
                title = event.get("title", "LingChat Runtime")
                text = event.get("text", "PROCESS STATE DESYNCHRONIZED")
                if (
                    not isinstance(title, str)
                    or not 1 <= len(title.strip()) <= 80
                    or any(ord(char) < 32 for char in title)
                    or not isinstance(text, str)
                    or len(text) > 1200
                    or any(ord(char) < 32 and char not in "\n\t" for char in text)
                ):
                    errors.append(
                        f"{chapter_id} event {index}: {window_label} text exceeds safe engine bounds"
                    )

            if event_type == "poem_game":
                poem_events.append((chapter_id, event))

    # 主动请求删除与“不速之删”必须稳定分流：玩家先在阻塞选项中授权，
    # 然后条件式停止 watcher，最后才打开角色目录。
    prompt_events = chapters.get("a3_delete_prompt", {}).get("events", [])
    if isinstance(prompt_events, list):
        permission_indices = []
        for index, event in enumerate(prompt_events):
            if not isinstance(event, dict) or event.get("type") != "choices":
                continue
            for option in event.get("options", []):
                if not isinstance(option, dict):
                    continue
                if any(
                    isinstance(action, dict)
                    and action.get("type") == "set_var"
                    and action.get("content") == "delete_permission = true"
                    for action in option.get("actions", [])
                ):
                    permission_indices.append(index)
                    break
        stop_indices = [
            index
            for index, event in enumerate(prompt_events)
            if isinstance(event, dict)
            and event.get("type") == "watch_file"
            and event.get("action") == "stop"
            and event.get("condition") == "delete_permission == true"
        ]
        open_indices = [
            index
            for index, event in enumerate(prompt_events)
            if isinstance(event, dict)
            and event.get("type") == "character_file"
            and event.get("action") == "open_folder"
            and event.get("condition") == "delete_permission == true"
        ]
        if (
            not permission_indices
            or not stop_indices
            or not open_indices
            or min(permission_indices) > min(stop_indices)
            or min(stop_indices) > min(open_indices)
        ):
            errors.append(
                "a3_delete_prompt must await delete permission, stop watch_file, then open the folder"
            )

    def event_sets(event: dict[str, Any], assignment: str) -> bool:
        options = event.get("options")
        if not isinstance(options, list):
            return False
        for option in options:
            if not isinstance(option, dict):
                continue
            actions = option.get("actions")
            if isinstance(actions, list) and any(
                isinstance(action, dict)
                and action.get("type") == "set_var"
                and action.get("content") == assignment
                for action in actions
            ):
                return True
        return False

    def require_resumable_transition(
        chapter_id: str,
        checkpoint_assignment: str,
        deleted_file: str,
        act_assignment: str,
        clear_assignment: str = "marker_checkpoint = none",
    ) -> None:
        events = chapters.get(chapter_id, {}).get("events", [])
        if not isinstance(events, list):
            return
        checkpoint_indexes = [
            index
            for index, event in enumerate(events)
            if isinstance(event, dict) and event_sets(event, checkpoint_assignment)
        ]
        delete_indexes = [
            index
            for index, event in enumerate(events)
            if isinstance(event, dict)
            and event.get("type") == "character_file"
            and event.get("action") == "delete"
            and event.get("file") == deleted_file
        ]
        act_indexes = [
            index
            for index, event in enumerate(events)
            if isinstance(event, dict) and event_sets(event, act_assignment)
        ]
        menu_indexes = [
            index
            for index, event in enumerate(events)
            if isinstance(event, dict) and event.get("type") == "main_menu_effect"
        ]
        clear_indexes = [
            index
            for index, event in enumerate(events)
            if isinstance(event, dict) and event_sets(event, clear_assignment)
        ]
        if not all(
            [checkpoint_indexes, delete_indexes, act_indexes, menu_indexes, clear_indexes]
        ) or not (
            max(checkpoint_indexes)
            < min(delete_indexes)
            < min(act_indexes)
            < min(menu_indexes)
            < min(clear_indexes)
        ):
            errors.append(
                f"{chapter_id}: destructive marker transition is not checkpoint/delete/state/menu/clear ordered"
            )

    require_resumable_transition(
        "a1_end", "marker_checkpoint = act1_to_act2", "MAIN.chr", "current_act = 2"
    )
    require_resumable_transition(
        "a2_end", "marker_checkpoint = act2_to_act3", "ql.chr", "current_act = 3"
    )

    legacy_events = chapters.get("a4_legacy_recovery", {}).get("events", [])
    if isinstance(legacy_events, list):
        choice_indexes = [
            index
            for index, event in enumerate(legacy_events)
            if isinstance(event, dict)
            and event.get("type") == "choices"
            and event_sets(event, "marker_checkpoint = legacy_release")
            and event_sets(event, "marker_checkpoint = legacy_loop")
        ]
        delete_indexes = [
            index
            for index, event in enumerate(legacy_events)
            if isinstance(event, dict)
            and event.get("type") == "character_file"
            and event.get("action") == "delete"
        ]
        state_indexes = [
            index
            for index, event in enumerate(legacy_events)
            if isinstance(event, dict)
            and event_sets(event, "marker_schema_version = 1")
        ]
        clear_indexes = [
            index
            for index, event in enumerate(legacy_events)
            if isinstance(event, dict)
            and event_sets(event, "marker_checkpoint = none")
        ]
        if not all([choice_indexes, delete_indexes, state_indexes, clear_indexes]) or not (
            max(choice_indexes)
            < min(delete_indexes)
            < min(state_indexes)
            < min(clear_indexes)
        ):
            errors.append(
                "a4_legacy_recovery: legacy choice is not a resumable marker transaction"
            )

    migration_events = chapters.get("a0_marker_migration", {}).get("events", [])
    if isinstance(migration_events, list):
        classifier = migration_events[0] if migration_events else {}
        classifier_options = classifier.get("options") if isinstance(classifier, dict) else None

        def classify_marker_state(initial: dict[str, Any]) -> dict[str, Any]:
            variables = dict(initial)
            if not isinstance(classifier_options, list):
                return variables
            for option in classifier_options:
                if not isinstance(option, dict) or not evaluate_condition(
                    str(option.get("condition", "")), variables
                ):
                    continue
                for action in option.get("actions", []):
                    if not isinstance(action, dict) or action.get("type") != "set_var":
                        continue
                    content = action.get("content")
                    if not isinstance(content, str) or "=" not in content:
                        continue
                    name, raw_value = (part.strip() for part in content.split("=", 1))
                    try:
                        value: Any = int(raw_value)
                    except ValueError:
                        value = raw_value
                    variables[name] = value
            return variables

        migration_cases = [
            ({"current_act": 2}, "act2", 2),
            ({"current_act": 4}, "both", 4),
            ({"current_act": 5}, "both", 5),
            ({"playthrough": 2}, "act2", 2),
            ({"playthrough": 4, "last_ending": "release"}, "release", 4),
            ({"playthrough": 4, "last_ending": "loop"}, "loop", 4),
        ]
        for initial, expected_target, expected_act in migration_cases:
            migrated = classify_marker_state(initial)
            if (
                migrated.get("marker_target") != expected_target
                or migrated.get("current_act") != expected_act
            ):
                errors.append(
                    f"a0_marker_migration classifier mismatch for {initial}: {migrated}"
                )

        migration_deletes = [
            index
            for index, event in enumerate(migration_events)
            if isinstance(event, dict)
            and event.get("type") == "character_file"
            and event.get("action") == "delete"
        ]
        migration_commits = [
            index
            for index, event in enumerate(migration_events)
            if isinstance(event, dict)
            and event_sets(event, "marker_schema_version = 1")
        ]
        if not migration_deletes or not migration_commits or not (
            max(migration_deletes) < min(migration_commits)
        ):
            errors.append("a0_marker_migration: schema commit must follow marker normalization")

    for source, target in references:
        if target not in chapters:
            errors.append(f"{source}: missing chapter target {target!r}")

    if uses_glitch_windows:
        if config.get("content_warning") != "horror":
            errors.append("glitch_window/console_window requires content_warning: horror")
        if settings.get("allow_system_effects") is not True:
            errors.append("glitch_window/console_window requires script_settings.allow_system_effects: true")

    adjacency: dict[str, set[str]] = {chapter_id: set() for chapter_id in chapters}
    for source, target in references:
        if target in chapters:
            adjacency[source].add(target)

    reachable: set[str] = set()
    stack = [intro] if isinstance(intro, str) and intro in chapters else []
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        stack.extend(adjacency[current] - reachable)

    reverse: dict[str, set[str]] = {chapter_id: set() for chapter_id in chapters}
    for source, targets in adjacency.items():
        for target in targets:
            reverse[target].add(source)
    can_terminate = set(terminal_chapters)
    stack = list(terminal_chapters)
    while stack:
        current = stack.pop()
        for source in reverse.get(current, set()):
            if source not in can_terminate:
                can_terminate.add(source)
                stack.append(source)
    for chapter_id in sorted(reachable - can_terminate):
        errors.append(f"reachable chapter has no path to end: {chapter_id}")

    words = word_data.get("words")
    if not isinstance(words, list):
        errors.append("poem_words.yaml: words must be a list")
        words = []
    texts = [entry.get("text") for entry in words if isinstance(entry, dict)]
    if len(texts) != len(set(texts)):
        errors.append("poem_words.yaml: normal words contain duplicates")
    required_words = max(
        (int(event.get("rounds", 20)) * 10 for _, event in poem_events), default=0
    )
    if len(words) < required_words:
        errors.append(
            f"poem_words.yaml: need {required_words} unique normal words, found {len(words)}"
        )

    for chapter_id, event in poem_events:
        mode = event.get("mode")
        if mode not in POEM_MODES:
            errors.append(f"{chapter_id}: poem_game has invalid mode {mode!r}")
        if not isinstance(event.get("glitch"), bool):
            errors.append(f"{chapter_id}: poem_game must set glitch explicitly")
        for field in ("warmStickerPath", "scriptStickerPath"):
            sticker = event.get(field)
            if isinstance(sticker, str) and sticker.lower().endswith(".png"):
                hop = f"{sticker[:-4]}-跳.png"
                if Path(hop).name not in available_media:
                    errors.append(f"{chapter_id}: missing derived hop sticker {hop!r}")
        void_sticker = event.get("voidStickerPath")
        if isinstance(void_sticker, str):
            broken = "写诗Q版-崩坏.png"
            if broken not in available_media:
                errors.append(f"{chapter_id}: missing broken sticker {broken!r}")

    for chapter_id in sorted(set(chapters) - reachable):
        if chapter_id not in COMPATIBILITY_CHAPTERS:
            warnings.append(f"unreachable chapter: {chapter_id}")

    if errors:
        print("VALIDATION FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1

    print(
        "VALIDATION OK: "
        f"chapters={len(chapters)} refs={len(references)} "
        f"terminal_chapters={len(terminal_chapters)} "
        f"poem_words={len(words)} poem_games={len(poem_events)}"
    )
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
