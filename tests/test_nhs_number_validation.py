"""
Tests for NHS number validation endpoint.
"""

import pytest
from django.test import Client


@pytest.fixture
def client():
    return Client()


class TestNHSNumberValidation:
    """Tests for the NHS number HTMX validation endpoint."""

    def test_valid_nhs_number_returns_success(self, client, db):
        """Test that a valid NHS number returns success styling."""
        # 4505577104 is a valid NHS number (passes checksum)
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "4505577104"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "input-success" in content
        assert "450 557 7104" in content  # Formatted as 3 3 4

    def test_invalid_nhs_number_returns_error(self, client, db):
        """Test that an invalid NHS number returns error styling."""
        # 1234567890 is an invalid NHS number (fails checksum)
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "1234567890"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "input-error" in content
        assert "123 456 7890" in content  # Still formatted as 3 3 4

    def test_empty_nhs_number_returns_empty_input(self, client, db):
        """Test that an empty NHS number returns a clean input."""
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": ""},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "input-success" not in content
        assert "input-error" not in content
        assert 'placeholder="NHS number"' in content

    def test_nhs_number_with_spaces_is_normalised(self, client, db):
        """Test that NHS numbers with spaces are normalised."""
        # 4505577104 with spaces should still validate
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "450 557 7104"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "input-success" in content
        assert "450 557 7104" in content

    def test_short_nhs_number_returns_error(self, client, db):
        """Test that a too-short NHS number returns error."""
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "12345"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "input-error" in content

    def test_htmx_attributes_preserved_in_response(self, client, db):
        """Test that HTMX attributes are preserved in the response."""
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "4505577104"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert 'hx-post="/surveys/validate/nhs-number/"' in content
        assert 'hx-trigger="blur, keyup changed delay:500ms"' in content
        assert 'hx-target="closest label"' in content
        assert 'hx-swap="outerHTML"' in content

    def test_valid_nhs_number_shows_checkmark(self, client, db):
        """Test that a valid NHS number shows a checkmark icon."""
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "4505577104"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "text-success" in content
        assert "polyline" in content  # Checkmark SVG

    def test_invalid_nhs_number_shows_x_icon(self, client, db):
        """Test that an invalid NHS number shows an X icon."""
        response = client.post(
            "/surveys/validate/nhs-number/",
            {"nhs_number": "1234567890"},
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "text-error" in content
        assert '<line x1="18"' in content  # X icon SVG
