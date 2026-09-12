#!/usr/bin/env python3
"""
Scanner de cadenas de interfaz (UI) para Warp.
Identifica literales de texto hardcodeados utilizados en constructores visuales,
menús, paleta de comandos y configuración.
"""

import os
import re
import json
import argparse
from pathlib import Path

# Patrones específicos de llamadas de UI donde residen textos visibles
UI_PATTERNS = [
    # BindingDescription / Atajos / Paleta
    (r'BindingDescription::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*\)', 'BindingDescription::new'),
    (r'\.with_custom_description\(\s*[^,]+,\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*\)', 'with_custom_description'),
    (r'FixedBinding::empty\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?', 'FixedBinding::empty'),
    (r'ToggleSettingActionPair::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 'ToggleSettingActionPair'),
    
    # Menús y elementos de menú
    (r'MenuItemFields::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*\)', 'MenuItemFields::new'),
    (r'MenuItemFields::new_with_label\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 'MenuItemFields::new_with_label'),
    (r'MenuItemFields::new_with_custom_label\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 'MenuItemFields::new_with_custom_label'),
    (r'DropdownItem::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 'DropdownItem::new'),

    # Categorías y Títulos de Configuración
    (r'Category::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 'Category::new'),
    (r'render_body_item(?:<[^>]+>)?\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?', 'render_body_item'),
    (r'render_body_item_label\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?', 'render_body_item_label'),
    (r'HeaderContent::simple\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"\s*\)', 'HeaderContent::simple'),
    (r'search_terms\(&self\)\s*->\s*&str\s*{\s*"([^"\\]*(?:\\.[^"\\]*)*)"', 'search_terms'),

    # Elementos de texto visuales
    (r'\.(?:span|h[1-5]|heading)\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*\)', 'ui_builder.text'),
    (r'\.(?:tool_tip|autosuggestion_tool_tip)\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*\)', 'ui_builder.tooltip'),
    (r'\.link\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*,', 'ui_builder.link'),
    (r'\.(?:primary_button|button|text_button|copy_button)\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?\s*,', 'ui_builder.button'),

    # Diálogos y modales
    (r'Dialog::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?', 'Dialog::new'),
    (r'Toast::new\(\s*"([^"\\]*(?:\\.[^"\\]*)*)"(?:\.to_string\(\)|\.to_owned\(\)|\.into\(\))?', 'Toast::new'),
]

# Exclusiones de cadenas no traducibles
IGNORE_STARTSWITH = (
    'http://', 'https://', 'warp://', 'ws://', 'wss://',
    'bundled/', 'bundled\\', 'svg/', 'icons/', '/', '\\',
    '--', '-', '_',
)

IGNORE_ENDSWITH = (
    '.svg', '.png', '.jpg', '.jpeg', '.json', '.graphql', '.sql', '.toml', '.txt',
    '.rs', '.wgsl', '.sh', '.bash', '.zsh', '.fish', '.ps1'
)

def is_translatable(text: str) -> bool:
    s = text.strip()
    if not s:
        return False
    if len(s) <= 1:
        return False
    if s.isdigit():
        return False
    for prefix in IGNORE_STARTSWITH:
        if s.startswith(prefix):
            return False
    for suffix in IGNORE_ENDSWITH:
        if s.endswith(suffix):
            return False
    # No contiene letras
    if not any(c.isalpha() for c in s):
        return False
    return True

def scan_file(filepath: Path):
    try:
        content = filepath.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        return []

    lines = content.splitlines()
    matches = []

    for pattern_str, caller_type in UI_PATTERNS:
        compiled = re.compile(pattern_str)
        for line_num, line in enumerate(lines, start=1):
            # Omitir líneas de logging o telemetría obvia
            stripped = line.strip()
            if stripped.startswith(('log::', 'safe_log::', 'eprintln!', 'println!', 'debug!', 'info!', 'warn!', 'error!', 'trace!')):
                continue
            if 'TelemetryEvent' in line or 'send_telemetry' in line:
                continue
            if '#[serde(' in line:
                continue

            for match in compiled.finditer(line):
                text = match.group(1)
                if is_translatable(text):
                    matches.append({
                        'file': str(filepath).replace('\\', '/'),
                        'line': line_num,
                        'pattern': caller_type,
                        'text_en': text,
                        'source_line': stripped
                    })
    return matches

def main():
    parser = argparse.ArgumentParser(description='Warp UI String Scanner')
    parser.add_argument('--dirs', nargs='+', default=['app/src', 'crates/onboarding', 'crates/ui_components', 'crates/warp_tui'],
                        help='Directorios a escanear')
    parser.add_argument('--output', default='i18n/extracted_strings.json', help='Ruta del archivo JSON de salida')
    args = parser.parse_args()

    root_dir = Path(os.getcwd())
    all_results = []
    unique_strings = set()

    for target_dir in args.dirs:
        full_path = root_dir / target_dir
        if not full_path.exists():
            continue
        for root, _, files in os.walk(full_path):
            for file in files:
                if file.endswith('.rs') and not file.endswith('_tests.rs') and not file == 'mod_test.rs':
                    file_path = Path(root) / file
                    res = scan_file(file_path)
                    all_results.extend(res)
                    for item in res:
                        unique_strings.add(item['text_en'])

    output_path = root_dir / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    summary = {
        'total_occurrences': len(all_results),
        'total_unique_strings': len(unique_strings),
        'strings': all_results
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Escaneo completado con éxito.")
    print(f"Total de apariciones de cadenas UI encontradas: {len(all_results)}")
    print(f"Cadenas de texto únicas: {len(unique_strings)}")
    print(f"Resultados guardados en: {args.output}")

if __name__ == '__main__':
    main()
