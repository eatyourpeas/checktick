# Branding and theme settings

This guide lists configuration variables you can set to customize branding, themes, and behavior. Values are read from Django settings and the SiteBranding record (set via the Profile page).

CheckTick uses **Tailwind CSS v4** with **daisyUI v5.4.7** for theming. Themes can be configured at the organization level via the Profile page, with per-survey overrides available when needed.

## Branding settings (environment variables)

- BRAND_TITLE (str) — Default site title. Example: "CheckTick"
- BRAND_ICON_URL (str) — URL or static path to the site icon shown in the navbar and as favicon if no uploaded icon.
- BRAND_ICON_URL_DARK (str) — Optional dark-mode icon URL. Shown when dark theme is active.
- BRAND_ICON_ALT (str) — Alt text for the brand icon. Defaults to BRAND_TITLE.
- BRAND_ICON_TITLE (str) — Title/tooltip for the brand icon. Defaults to BRAND_TITLE.
- BRAND_ICON_SIZE_CLASS (str) — Tailwind size classes for the icon. Example: "w-8 h-8".
- BRAND_ICON_SIZE (int or str) — Numeric size that maps to `w-{n} h-{n}`. Example: 6, 8. Ignored if BRAND_ICON_SIZE_CLASS is set.

## Theme settings (environment variables)

- BRAND_THEME (str) — Default logical theme name. Values: "checktick-light" or "checktick-dark". Default: "checktick-light".
- BRAND_THEME_PRESET_LIGHT (str) — daisyUI preset for light mode. Default: "wireframe". Available: light, cupcake, bumblebee, emerald, corporate, retro, cyberpunk, valentine, garden, lofi, pastel, fantasy, wireframe, cmyk, autumn, acid, lemonade, winter, nord, sunset.
- BRAND_THEME_PRESET_DARK (str) — daisyUI preset for dark mode. Default: "business". Available: dark, synthwave, halloween, forest, aqua, black, luxury, dracula, business, night, coffee, dim.
- BRAND_FONT_HEADING (str) — CSS font stack for headings.
- BRAND_FONT_BODY (str) — CSS font stack for body.
- BRAND_FONT_CSS_URL (str) — Optional font CSS href (e.g., Google Fonts).
- BRAND_THEME_CSS_LIGHT (str) — Custom DaisyUI variable overrides for light theme (advanced).
- BRAND_THEME_CSS_DARK (str) — Custom DaisyUI variable overrides for dark theme (advanced).

## Organization-level theming (SiteBranding model)

Organization admins can override environment defaults via the Profile page. Settings are stored in the `SiteBranding` database model:

- **default_theme** — Logical theme name (checktick-light or checktick-dark)
- **theme_preset_light** — daisyUI preset for light mode (20 options)
- **theme_preset_dark** — daisyUI preset for dark mode (12 options)
- **icon_file** / **icon_url** — Light mode icon (uploaded file takes precedence over URL)
- **icon_file_dark** / **icon_url_dark** — Dark mode icon
- **font_heading** / **font_body** / **font_css_url** — Font configuration
- **theme_light_css** / **theme_dark_css** — Custom CSS from daisyUI Theme Generator (optional, overrides presets)

**Precedence**: Database values → Environment variables → Built-in defaults

## How theming works

1. **Logical theme names** (checktick-light, checktick-dark) are used for:
   - User preference storage (localStorage)
   - Theme toggle UI
   - Database field values

2. **Actual daisyUI preset names** (wireframe, business, etc.) are applied to the DOM:
   - `<html data-theme="wireframe">` for light mode
   - `<html data-theme="business">` for dark mode
   - JavaScript maps logical names to presets based on SiteBranding settings

3. **Custom CSS overrides** from daisyUI Theme Generator can override preset colors while keeping the base theme structure.

## Survey style fields (per-survey)

- title — Optional page title override
- icon_url — Optional per-survey favicon/icon
- theme_name — DaisyUI theme name for the survey pages
- primary_color — Hex color (e.g., #ff3366); normalized to the correct color variables
- font_heading — CSS font stack
- font_body — CSS font stack
- font_css_url — Optional font CSS href
- theme_css_light — Light theme DaisyUI variable overrides (from builder)
- theme_css_dark — Dark theme DaisyUI variable overrides (from builder)

## Where to look in the code

- **Tailwind v4 entry point**: `checktick_app/static/css/daisyui_themes.css` (CSS-based config, no JS config file)
- **Theme utility**: `checktick_app/core/themes.py` (preset lists, parsing functions)
- **Base templates**: `checktick_app/templates/base.html`, `base_minimal.html`, `admin/base_site.html`
- **Branding context**: `checktick_app/context_processors.py` (builds the `brand` object)
- **Profile UI**: `checktick_app/core/templates/core/profile.html` (theme preset dropdowns)
- **Theme switcher JS**: `checktick_app/static/js/theme-toggle.js`, `admin-theme.js`
- **Survey dashboard style form**: `checktick_app/surveys/templates/surveys/dashboard.html`

## Rebuilding the CSS

Tailwind CSS v4 uses the `@tailwindcss/cli` package:

```bash
npm run build:css
```

Or in Docker:

```bash
docker compose exec web npm run build:css
```

The build process:

- Input: `checktick_app/static/css/daisyui_themes.css`
- Output: `checktick_app/static/build/styles.css` (minified)
- Build time: ~250ms
- All 39 daisyUI themes included (192KB minified)
