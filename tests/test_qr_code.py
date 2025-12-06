"""Tests for QR code generation functionality."""

from django.test import override_settings
from django.urls import reverse
import pytest

from checktick_app.core.qr_utils import generate_qr_code_data_uri
from checktick_app.surveys.models import Survey


class TestQRCodeUtils:
    """Tests for QR code utility functions."""

    def test_generate_qr_code_returns_data_uri(self):
        """QR code should return a data URI string."""
        result = generate_qr_code_data_uri("https://example.com/survey")
        assert result.startswith("data:image/png;base64,")

    def test_generate_qr_code_different_urls_produce_different_codes(self):
        """Different URLs should produce different QR codes."""
        qr1 = generate_qr_code_data_uri("https://example.com/survey1")
        qr2 = generate_qr_code_data_uri("https://example.com/survey2")
        assert qr1 != qr2

    def test_generate_qr_code_custom_size(self):
        """QR codes with different sizes should produce different lengths."""
        qr_small = generate_qr_code_data_uri("https://example.com", size=100)
        qr_large = generate_qr_code_data_uri("https://example.com", size=300)
        # Larger size should produce longer base64 string
        assert len(qr_large) > len(qr_small)

    def test_generate_qr_code_with_long_url(self):
        """QR code should handle long URLs."""
        long_url = "https://example.com/surveys/" + "a" * 100 + "/take/"
        result = generate_qr_code_data_uri(long_url)
        assert result.startswith("data:image/png;base64,")


@pytest.mark.django_db
class TestQRCodeView:
    """Tests for QR code API endpoint."""

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="testuser", email="test@example.com"
        )

    @pytest.fixture
    def survey(self, user):
        return Survey.objects.create(
            name="Test Survey",
            slug="test-survey-qr",
            owner=user,
            status="published",
            visibility="public",
        )

    def test_qr_code_endpoint_requires_login(self, client, survey):
        """QR code endpoint should require authentication."""
        url = reverse("surveys:get_qr_code", kwargs={"slug": survey.slug})
        response = client.get(
            url, {"url": f"https://example.com/surveys/{survey.slug}/take/"}
        )
        assert response.status_code == 302  # Redirect to login

    @override_settings(SITE_URL="http://testserver")
    def test_qr_code_endpoint_returns_qr(self, client, user, survey):
        """QR code endpoint should return QR code data."""
        client.force_login(user)
        url = reverse("surveys:get_qr_code", kwargs={"slug": survey.slug})
        # Use testserver as the host since that's what Django test client uses
        survey_url = f"http://testserver/surveys/{survey.slug}/take/"
        response = client.get(url, {"url": survey_url})
        assert response.status_code == 200
        data = response.json()
        assert "qr_code" in data
        assert data["qr_code"].startswith("data:image/png;base64,")

    def test_qr_code_endpoint_requires_url_param(self, client, user, survey):
        """QR code endpoint should require URL parameter."""
        client.force_login(user)
        url = reverse("surveys:get_qr_code", kwargs={"slug": survey.slug})
        response = client.get(url)
        assert response.status_code == 400
        assert "error" in response.json()

    def test_qr_code_endpoint_validates_survey_url(self, client, user, survey):
        """QR code endpoint should reject URLs not for this survey."""
        client.force_login(user)
        url = reverse("surveys:get_qr_code", kwargs={"slug": survey.slug})
        # Try to get QR for a different survey
        response = client.get(
            url, {"url": "https://example.com/surveys/other-survey/take/"}
        )
        assert response.status_code == 400
        assert "error" in response.json()

    @override_settings(SITE_URL="https://example.com")
    def test_qr_code_endpoint_rejects_external_urls(self, client, user, survey):
        """QR code endpoint should reject URLs for external sites."""
        client.force_login(user)
        url = reverse("surveys:get_qr_code", kwargs={"slug": survey.slug})
        # Try to generate QR for an external site (with survey slug in path for bypass attempt)
        response = client.get(
            url, {"url": f"https://malicious.com/surveys/{survey.slug}/take/"}
        )
        assert response.status_code == 400
        assert "error" in response.json()
        assert "site" in response.json()["error"].lower()

    def test_qr_code_endpoint_rejects_invalid_url_format(self, client, user, survey):
        """QR code endpoint should reject malformed URLs that don't contain survey slug."""
        client.force_login(user)
        url = reverse("surveys:get_qr_code", kwargs={"slug": survey.slug})
        # URLs that don't contain survey slug should be rejected
        malformed_urls = [
            "not-a-url",
            "javascript:alert(1)",
            "file:///etc/passwd",
        ]
        for bad_url in malformed_urls:
            response = client.get(url, {"url": bad_url})
            # Should reject as not matching survey slug
            assert response.status_code == 400

    @pytest.fixture
    def private_survey(self, user):
        """Create a private survey for permission testing."""
        return Survey.objects.create(
            name="Private Survey",
            slug="private-survey-qr",
            owner=user,
            status="published",
            visibility="authenticated",  # Requires authentication and permission
        )

    @override_settings(SITE_URL="http://testserver")
    def test_qr_code_endpoint_requires_permission(
        self, client, django_user_model, private_survey
    ):
        """QR code endpoint should require view permission on private surveys."""
        # Create a different user without access
        other_user = django_user_model.objects.create_user(
            username="otheruser", email="other@example.com"
        )
        client.force_login(other_user)
        url = reverse("surveys:get_qr_code", kwargs={"slug": private_survey.slug})
        survey_url = f"http://testserver/surveys/{private_survey.slug}/take/"
        response = client.get(url, {"url": survey_url})
        # Should be denied access - 403 Forbidden
        assert response.status_code == 403


@pytest.mark.django_db
class TestQRCodeInEmails:
    """Tests for QR code inclusion in invitation emails."""

    @pytest.fixture
    def user(self, django_user_model):
        return django_user_model.objects.create_user(
            username="inviter", email="inviter@example.com"
        )

    @pytest.fixture
    def survey(self, user):
        return Survey.objects.create(
            name="Email Test Survey",
            slug="email-test-survey",
            owner=user,
            status="published",
            visibility="token",
        )

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_with_qr_code(self, user, survey):
        """Email invitation should include QR code when enabled."""
        from checktick_app.core.email_utils import send_survey_invite_email
        from checktick_app.core.qr_utils import generate_qr_code_data_uri

        qr_code = generate_qr_code_data_uri("https://example.com/survey/take/")

        # This should not raise an error
        result = send_survey_invite_email(
            to_email="recipient@example.com",
            survey=survey,
            token="test-token-123",
            contact_email=user.email,
            qr_code_data_uri=qr_code,
        )
        # If email sending is properly configured, this should succeed
        # In test environment with locmem backend, it returns True
        assert result is True

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_email_without_qr_code(self, user, survey):
        """Email invitation should work without QR code."""
        from checktick_app.core.email_utils import send_survey_invite_email

        result = send_survey_invite_email(
            to_email="recipient@example.com",
            survey=survey,
            token="test-token-456",
            contact_email=user.email,
            qr_code_data_uri=None,
        )
        assert result is True
