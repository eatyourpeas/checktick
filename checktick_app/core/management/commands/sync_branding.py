"""
Management command to sync branding settings from environment variables to database.

This ensures that deployment configuration always takes precedence over stale database values.
Run this command on each deployment/startup.

The sync_branding command updates SiteBranding (platform-level settings) only.
Organization-level themes are stored in the Organization model and are NOT affected.

Precedence:
- Platform: env vars → SiteBranding database → built-in defaults
- Organization: Organization model overrides platform for org members
- Survey: Survey model overrides organization for survey pages
"""

from django.conf import settings
from django.core.management.base import BaseCommand

from checktick_app.core.models import SiteBranding


class Command(BaseCommand):
    help = "Sync branding settings from environment variables to database"

    def handle(self, *args, **options):
        sb, created = SiteBranding.objects.get_or_create(pk=1)

        if created:
            self.stdout.write("Created new SiteBranding record")
        else:
            self.stdout.write("Updating existing SiteBranding record")

        # Track what changed
        changes = []

        # Sync font settings
        # These always sync from settings (which includes env var overrides and defaults)
        env_font_heading = getattr(settings, "BRAND_FONT_HEADING", "")
        env_font_body = getattr(settings, "BRAND_FONT_BODY", "")
        env_font_css_url = getattr(settings, "BRAND_FONT_CSS_URL", "")

        # For fonts, always sync the value from settings (env or default)
        if env_font_heading != sb.font_heading:
            sb.font_heading = env_font_heading
            changes.append(f"font_heading: {env_font_heading[:50]}...")

        if env_font_body != sb.font_body:
            sb.font_body = env_font_body
            changes.append(f"font_body: {env_font_body[:50]}...")

        # Font CSS URL - sync even if empty (to clear old Google Fonts URLs)
        if env_font_css_url != sb.font_css_url:
            sb.font_css_url = env_font_css_url
            changes.append(
                f"font_css_url: '{env_font_css_url[:50] if env_font_css_url else '(empty - using local fonts)'}'"
            )

        # Sync theme settings - always sync from settings
        env_theme = getattr(settings, "BRAND_THEME", "checktick-light")
        env_preset_light = getattr(settings, "BRAND_THEME_PRESET_LIGHT", "lofi")
        env_preset_dark = getattr(settings, "BRAND_THEME_PRESET_DARK", "dim")

        if env_theme != sb.default_theme:
            sb.default_theme = env_theme
            changes.append(f"default_theme: {env_theme}")

        if env_preset_light != sb.theme_preset_light:
            sb.theme_preset_light = env_preset_light
            changes.append(f"theme_preset_light: {env_preset_light}")

        if env_preset_dark != sb.theme_preset_dark:
            sb.theme_preset_dark = env_preset_dark
            changes.append(f"theme_preset_dark: {env_preset_dark}")

        # Sync icon URLs (only if explicitly set - empty means "use default icon")
        env_icon_url = getattr(settings, "BRAND_ICON_URL", "")
        env_icon_url_dark = getattr(settings, "BRAND_ICON_URL_DARK", "")

        if env_icon_url and env_icon_url != sb.icon_url:
            sb.icon_url = env_icon_url
            changes.append(f"icon_url: {env_icon_url}")

        if env_icon_url_dark and env_icon_url_dark != sb.icon_url_dark:
            sb.icon_url_dark = env_icon_url_dark
            changes.append(f"icon_url_dark: {env_icon_url_dark}")

        if changes:
            sb.save()
            self.stdout.write(
                self.style.SUCCESS(f"Updated branding: {', '.join(changes)}")
            )
        else:
            self.stdout.write("No branding changes needed")
