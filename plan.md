# Plan: Add Portuguese/Polish Language Toggle

## Context

The app needs to support Portuguese and Polish as language options. The user wants a simple button to switch between them. There are ~200+ user-facing strings spread across 6 Python files + 2 src modules with UI text.

## Approach: Single Translation Dictionary File + Session State Toggle

Create one `src/i18n.py` file containing all translations as a nested dictionary, and a helper function `t(key)` that returns the string for the current language. Add a language toggle in the sidebar that persists in `st.session_state`.

### Why this approach
- **Simplest possible**: No external libraries, no JSON files, no gettext
- **One file to maintain**: All translations in one place
- **Minimal changes to existing files**: Replace hardcoded strings with `t("key")` calls
- **Instant switch**: Language stored in `session_state`, toggle causes `st.rerun()`

## Files to Create

### `src/i18n.py` (~300 lines)
- Dictionary with structure: `TRANSLATIONS = {"pt": {"key": "value"}, "pl": {"key": "value"}}`
- `t(key)` function that reads `st.session_state.get("language", "pt")` and returns the translated string
- Keys organized by page/section (e.g., `"login_title"`, `"upload_title"`, `"measurement_save_btn"`)
- Only translate **core UI text** (labels, buttons, messages, titles). Skip long markdown content in expanders (tips, FAQs, setup instructions) — those are developer/admin-facing and rarely read.

### Strings to translate (core UI only, ~80 keys):
- Page titles and subtitles
- Button labels
- Form field labels, placeholders, and help text
- Success/error/info messages
- Metric labels (Weight, Height, etc.)
- Sort/filter options
- Sidebar navigation text
- Footer tips

### Strings to skip (keep in English):
- Setup instructions expander ("First time here?")
- Troubleshooting expanders
- Tips for accurate measurements
- Growth chart tips
- Sharing FAQ
- Sharing instructions ("How to Share This Link")
- SUPABASE_SETUP references
- Debug info

## Files to Modify

### `Timeline.py`
- Import `t` from `src/i18n` and add language toggle in sidebar
- Replace hardcoded strings in `show_login_page()`, `show_sidebar()`, `show_timeline()`, `show_viewer_login()`, `show_viewer_sidebar()`
- Add language picker: `st.sidebar.selectbox` or flag buttons at top of sidebar (before auth check so viewers also see it)

### `pages/1_📸_Upload_Photo.py`
- Import `t`, replace strings in upload form, preview, status messages

### `pages/2_📏_Add_Measurement.py`
- Import `t`, replace strings in form, stats dashboard, measurement history

### `pages/3_📊_Growth_Chart.py`
- Import `t`, replace strings in chart labels, controls, statistics

### `pages/4_🔗_Sharing.py`
- Import `t`, replace strings in link display, generator form

### `src/database.py`
- Replace error/success messages in `add_measurement()`, `delete_measurement()`, `update_measurement()` with `t()` calls

### `src/storage.py`
- Replace success/error messages in `upload_photo()`, `delete_photo()` with `t()` calls

### `src/validators.py`
- Replace validation error messages with `t()` calls

### `src/auth.py`
- Replace error messages with `t()` calls

### `src/database.py` — `format_age()`
- Translate age strings: "days old", "weeks old", "months old", "years old"

## Language Toggle Placement

In the sidebar (visible on all pages), before everything else:
```python
lang_options = {"🇧🇷 Português": "pt", "🇵🇱 Polski": "pl"}
selected = st.sidebar.selectbox("🌐", list(lang_options.keys()), label_visibility="collapsed")
st.session_state["language"] = lang_options[selected]
```

This goes in each page file at the top (after `st.set_page_config`), or better: in a shared helper called from each page.

## Implementation Order

1. Create `src/i18n.py` with all translations and the `t()` helper
2. Add language toggle to `Timeline.py` sidebar (both admin and viewer sidebars)
3. Update `Timeline.py` strings
4. Update `pages/1_📸_Upload_Photo.py`
5. Update `pages/2_📏_Add_Measurement.py`
6. Update `pages/3_📊_Growth_Chart.py`
7. Update `pages/4_🔗_Sharing.py`
8. Update `src/auth.py`, `src/database.py`, `src/storage.py`, `src/validators.py`

## Verification

1. Run app locally, toggle language, verify all visible text changes
2. Check that forms, buttons, and messages display correctly in both languages
3. Verify viewer mode also shows the toggle and translates properly
4. Test that language choice persists across page navigation
