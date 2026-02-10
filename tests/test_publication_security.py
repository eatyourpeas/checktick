"""
Comprehensive security tests for all survey publication methods and visibility modes.

Tests authentication, authorization, rate limiting, and workflow validation for:
- PUBLIC visibility
- UNLISTED visibility
- TOKEN visibility
- AUTHENTICATED visibility
- Invitation sending endpoints
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
import pytest

from checktick_app.surveys.models import (
    Organization,
    QuestionGroup,
    Survey,
    SurveyAccessToken,
)

User = get_user_model()
TEST_PASSWORD = "testpass123"


@pytest.fixture
def owner(db):
    """Create a survey owner user."""
    return User.objects.create_user(
        username="owner", email="owner@test.com", password=TEST_PASSWORD
    )


@pytest.fixture
def organization(owner):
    """Create an organization owned by owner."""
    return Organization.objects.create(name="Test Org", owner=owner)


@pytest.fixture
def outsider(db):
    """Create a user not part of the organization."""
    return User.objects.create_user(
        username="outsider", email="outsider@test.com", password=TEST_PASSWORD
    )


@pytest.fixture
def base_survey(owner, organization):
    """Create a draft survey with questions."""
    import secrets

    # Use random slug to avoid conflicts between tests
    slug = f"test-survey-{secrets.token_hex(4)}"

    survey = Survey.objects.create(
        name="Test Survey",
        slug=slug,
        owner=owner,
        organization=organization,
        status=Survey.Status.DRAFT,
        visibility=Survey.Visibility.PUBLIC,
    )
    # Add question group to make survey valid
    group = QuestionGroup.objects.create(name="Questions", owner=owner)
    survey.question_groups.add(group)
    return survey


@pytest.fixture
def public_survey(base_survey):
    """Create a published PUBLIC survey."""
    base_survey.status = Survey.Status.PUBLISHED
    base_survey.visibility = Survey.Visibility.PUBLIC
    base_survey.published_at = timezone.now()
    base_survey.start_at = timezone.now()
    base_survey.no_patient_data_ack = True
    base_survey.save()
    return base_survey


@pytest.fixture
def unlisted_survey(base_survey):
    """Create a published UNLISTED survey."""
    import secrets

    base_survey.status = Survey.Status.PUBLISHED
    base_survey.visibility = Survey.Visibility.UNLISTED
    base_survey.published_at = timezone.now()
    base_survey.start_at = timezone.now()
    base_survey.no_patient_data_ack = True
    base_survey.unlisted_key = secrets.token_urlsafe(24)
    base_survey.save()
    return base_survey


@pytest.fixture
def token_survey(base_survey):
    """Create a published TOKEN survey."""
    base_survey.status = Survey.Status.PUBLISHED
    base_survey.visibility = Survey.Visibility.TOKEN
    base_survey.published_at = timezone.now()
    base_survey.start_at = timezone.now()
    base_survey.no_patient_data_ack = True
    base_survey.save()
    return base_survey


@pytest.fixture
def authenticated_survey(base_survey):
    """Create a published AUTHENTICATED survey."""
    base_survey.status = Survey.Status.PUBLISHED
    base_survey.visibility = Survey.Visibility.AUTHENTICATED
    base_survey.published_at = timezone.now()
    base_survey.start_at = timezone.now()
    base_survey.allow_any_authenticated = False  # Invite-only mode
    base_survey.save()
    return base_survey


@pytest.fixture
def valid_token(token_survey, owner):
    """Create a valid, unused access token."""
    return SurveyAccessToken.objects.create(
        survey=token_survey,
        token="valid-token-123",
        created_by=owner,
        note="Test token",
    )


@pytest.mark.django_db
class TestPublicVisibilitySecurity:
    """Test PUBLIC visibility mode security."""

    def test_public_survey_accessible_without_login(self, client, public_survey):
        """Public surveys accessible to anonymous users."""
        response = client.get(
            reverse("surveys:take", kwargs={"slug": public_survey.slug})
        )
        assert response.status_code == 200

    def test_public_survey_rate_limited(self, client, public_survey, settings):
        """Public survey endpoint has rate limiting."""
        # Configure in-memory cache
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }

        url = reverse("surveys:take", kwargs={"slug": public_survey.slug})

        # Make multiple requests to trigger rate limit (10/minute)
        for i in range(12):
            response = client.get(url)

        # After limit, should be blocked
        assert response.status_code in [429, 403]

    def test_public_survey_requires_no_patient_data_ack_if_collects_patient_data(
        self, client, owner, base_survey
    ):
        """Cannot publish public survey collecting patient data without acknowledgment."""
        from checktick_app.surveys.models import QuestionGroup

        # Add a patient demographics group to make it collect patient data
        patient_group = QuestionGroup.objects.create(
            name="Patient Details",
            owner=owner,
            schema={
                "template": "patient_details_encrypted",
                "fields": ["nhs_number", "first_name", "surname"],
            },
        )
        base_survey.question_groups.add(patient_group)

        client.force_login(owner)

        response = client.post(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug}),
            {
                "action": "publish",
                "visibility": Survey.Visibility.PUBLIC,
                "no_patient_data_ack": "",  # Not checked
            },
        )

        # Should stay on publish page with error
        assert response.status_code == 200
        base_survey.refresh_from_db()
        assert base_survey.status == Survey.Status.DRAFT

    def test_public_survey_owner_cannot_submit(self, client, owner, public_survey):
        """Survey owner cannot submit to their own public survey."""
        from django.core.cache import cache

        # Clear rate limit cache to avoid interference from previous tests
        cache.clear()

        client.force_login(owner)

        response = client.post(
            reverse("surveys:take", kwargs={"slug": public_survey.slug}),
            {},
        )

        # Should redirect to dashboard with message
        assert response.status_code == 302
        assert "dashboard" in response.url


@pytest.mark.django_db
class TestUnlistedVisibilitySecurity:
    """Test UNLISTED visibility mode security."""

    def test_unlisted_survey_requires_secret_key(self, client, unlisted_survey):
        """Unlisted surveys require the secret key in URL."""
        from django.core.cache import cache

        # Clear rate limit cache
        cache.clear()

        # Without key, should 404
        response = client.get(
            reverse("surveys:take", kwargs={"slug": unlisted_survey.slug})
        )
        assert response.status_code == 404

    def test_unlisted_survey_accessible_with_key(self, client, unlisted_survey):
        """Unlisted surveys accessible with correct key."""
        response = client.get(
            reverse(
                "surveys:take_unlisted",
                kwargs={
                    "slug": unlisted_survey.slug,
                    "key": unlisted_survey.unlisted_key,
                },
            )
        )
        assert response.status_code == 200

    def test_unlisted_survey_wrong_key_404(self, client, unlisted_survey):
        """Wrong unlisted key returns 404."""
        response = client.get(
            reverse(
                "surveys:take_unlisted",
                kwargs={"slug": unlisted_survey.slug, "key": "wrong-key"},
            )
        )
        assert response.status_code == 404

    def test_unlisted_survey_rate_limited(self, client, unlisted_survey, settings):
        """Unlisted survey endpoint has rate limiting."""
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }

        url = reverse(
            "surveys:take_unlisted",
            kwargs={"slug": unlisted_survey.slug, "key": unlisted_survey.unlisted_key},
        )

        # Make multiple requests (10/minute limit)
        for i in range(12):
            response = client.get(url)

        assert response.status_code in [429, 403]

    def test_unlisted_requires_no_patient_data_ack_if_collects_patient_data(
        self, client, owner, base_survey
    ):
        """Cannot publish unlisted survey collecting patient data without acknowledgment."""
        from checktick_app.surveys.models import QuestionGroup

        # Add patient demographics to require acknowledgment
        patient_group = QuestionGroup.objects.create(
            name="Patient Details",
            owner=owner,
            schema={
                "template": "patient_details_encrypted",
                "fields": ["nhs_number", "first_name", "surname"],
            },
        )
        base_survey.question_groups.add(patient_group)

        client.force_login(owner)

        response = client.post(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug}),
            {
                "action": "publish",
                "visibility": Survey.Visibility.UNLISTED,
                "no_patient_data_ack": "",  # Not checked
            },
        )

        assert response.status_code == 200
        base_survey.refresh_from_db()
        assert base_survey.status == Survey.Status.DRAFT


@pytest.mark.django_db
class TestTokenVisibilitySecurity:
    """Test TOKEN visibility mode security."""

    def test_token_survey_requires_valid_token(self, client, token_survey):
        """Token surveys require valid token in URL."""
        from django.core.cache import cache

        # Clear rate limit cache
        cache.clear()

        # Without token, should 404
        response = client.get(
            reverse("surveys:take", kwargs={"slug": token_survey.slug})
        )
        assert response.status_code == 404

    def test_token_survey_accessible_with_valid_token(
        self, client, token_survey, valid_token
    ):
        """Token surveys accessible with valid unused token."""
        response = client.get(
            reverse(
                "surveys:take_token",
                kwargs={"slug": token_survey.slug, "token": valid_token.token},
            )
        )
        assert response.status_code == 200

    def test_token_survey_invalid_token_404(self, client, token_survey):
        """Invalid token returns 404."""
        response = client.get(
            reverse(
                "surveys:take_token",
                kwargs={"slug": token_survey.slug, "token": "invalid-token"},
            )
        )
        assert response.status_code == 404

    def test_token_single_use_enforcement(self, client, token_survey, valid_token):
        """Tokens can only be used once."""
        # Mark token as used
        valid_token.used_at = timezone.now()
        valid_token.save()

        response = client.get(
            reverse(
                "surveys:take_token",
                kwargs={"slug": token_survey.slug, "token": valid_token.token},
            )
        )

        # Should redirect to closed page
        assert response.status_code == 302
        assert "/closed/" in response.url
        assert "token_used" in response.url

    def test_token_expiry_enforcement(self, client, token_survey, valid_token):
        """Expired tokens are rejected."""
        # Set expiry in the past
        valid_token.expires_at = timezone.now() - timezone.timedelta(days=1)
        valid_token.save()

        response = client.get(
            reverse(
                "surveys:take_token",
                kwargs={"slug": token_survey.slug, "token": valid_token.token},
            )
        )

        # Should redirect to closed page
        assert response.status_code == 302
        assert "/closed/" in response.url
        assert "token_expired" in response.url

    def test_token_survey_rate_limited(
        self, client, token_survey, valid_token, settings
    ):
        """Token survey endpoint has rate limiting."""
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }

        url = reverse(
            "surveys:take_token",
            kwargs={"slug": token_survey.slug, "token": valid_token.token},
        )

        # Make multiple requests (10/minute limit)
        for i in range(12):
            response = client.get(url)

        assert response.status_code in [429, 403]

    def test_token_requires_no_patient_data_ack_if_collects_patient_data(
        self, client, owner, base_survey
    ):
        """Cannot publish token survey collecting patient data without acknowledgment."""
        from checktick_app.surveys.models import QuestionGroup

        # Add patient demographics
        patient_group = QuestionGroup.objects.create(
            name="Patient Details",
            owner=owner,
            schema={
                "template": "patient_details_encrypted",
                "fields": ["nhs_number", "first_name", "surname"],
            },
        )
        base_survey.question_groups.add(patient_group)

        client.force_login(owner)

        response = client.post(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug}),
            {
                "action": "publish",
                "visibility": Survey.Visibility.TOKEN,
                "no_patient_data_ack": "",  # Not checked
            },
        )

        assert response.status_code == 200
        base_survey.refresh_from_db()
        assert base_survey.status == Survey.Status.DRAFT


@pytest.mark.django_db
class TestAuthenticatedVisibilitySecurity:
    """Test AUTHENTICATED visibility mode security."""

    def test_authenticated_survey_requires_login(self, client, authenticated_survey):
        """Authenticated surveys require user login."""
        from django.core.cache import cache

        # Clear rate limit cache
        cache.clear()

        response = client.get(
            reverse("surveys:take", kwargs={"slug": authenticated_survey.slug})
        )

        # Should redirect to login
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_authenticated_survey_allows_invited_user(
        self, client, authenticated_survey, owner
    ):
        """Invited users can access authenticated survey."""
        from django.core.cache import cache

        # Clear rate limit cache
        cache.clear()

        # Create invitation for test user
        invited_user = User.objects.create_user(
            username="invited", email="invited@test.com", password=TEST_PASSWORD
        )
        SurveyAccessToken.objects.create(
            survey=authenticated_survey,
            token="invite-token",
            created_by=owner,
            for_authenticated=True,
            note="Invited: invited@test.com",
        )

        client.force_login(invited_user)
        response = client.get(
            reverse("surveys:take", kwargs={"slug": authenticated_survey.slug})
        )

        assert response.status_code == 200

    def test_authenticated_survey_blocks_uninvited_user(
        self, client, authenticated_survey
    ):
        """Uninvited users cannot access invite-only authenticated survey."""
        from django.core.cache import cache

        # Clear rate limit cache
        cache.clear()

        uninvited_user = User.objects.create_user(
            username="uninvited", email="uninvited@test.com", password=TEST_PASSWORD
        )

        client.force_login(uninvited_user)
        response = client.get(
            reverse("surveys:take", kwargs={"slug": authenticated_survey.slug})
        )

        # Should redirect to closed page
        assert response.status_code == 302
        assert "/closed/" in response.url

    def test_authenticated_survey_allow_any_flag(self, client, authenticated_survey):
        """allow_any_authenticated flag allows any logged-in user."""
        from django.core.cache import cache

        # Clear rate limit cache
        cache.clear()

        # Enable allow_any_authenticated
        authenticated_survey.allow_any_authenticated = True
        authenticated_survey.save()

        any_user = User.objects.create_user(
            username="anyuser", email="anyuser@test.com", password=TEST_PASSWORD
        )

        client.force_login(any_user)
        response = client.get(
            reverse("surveys:take", kwargs={"slug": authenticated_survey.slug})
        )

        assert response.status_code == 200

    def test_authenticated_no_patient_data_validation(self, client, owner, base_survey):
        """Authenticated visibility does NOT require no_patient_data_ack."""
        client.force_login(owner)

        # Should allow publishing without no_patient_data_ack checkbox
        response = client.post(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug}),
            {
                "action": "publish",
                "visibility": Survey.Visibility.AUTHENTICATED,
                "no_patient_data_ack": "",  # Not checked - should be allowed
            },
        )

        # Should redirect to dashboard (success)
        assert response.status_code == 302
        assert "dashboard" in response.url
        base_survey.refresh_from_db()
        assert base_survey.status == Survey.Status.PUBLISHED


@pytest.mark.django_db
class TestInvitationEndpointsSecurity:
    """Test security of invitation sending endpoints."""

    def test_send_invites_async_requires_login(self, client, token_survey):
        """send_invites_async requires authentication."""
        response = client.post(
            reverse("surveys:send_invites_async", kwargs={"slug": token_survey.slug}),
            {"invite_emails": "user@example.com"},
        )

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_send_invites_async_requires_can_edit(self, client, token_survey, outsider):
        """send_invites_async requires edit permission."""
        client.force_login(outsider)

        response = client.post(
            reverse("surveys:send_invites_async", kwargs={"slug": token_survey.slug}),
            {"invite_emails": "user@example.com"},
        )

        assert response.status_code == 403

    def test_send_invites_async_rate_limited(
        self, client, owner, token_survey, settings
    ):
        """send_invites_async endpoint has rate limiting."""
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }

        client.force_login(owner)
        url = reverse("surveys:send_invites_async", kwargs={"slug": token_survey.slug})

        # Make multiple requests (20/hour limit)
        for i in range(22):
            response = client.post(url, {"invite_emails": f"user{i}@example.com"})

        # After limit, should be blocked
        assert response.status_code in [429, 403]

    def test_publish_settings_requires_login(self, client, base_survey):
        """Publish settings page requires authentication."""
        response = client.get(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug})
        )

        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_publish_settings_requires_can_edit(self, client, base_survey, outsider):
        """Publish settings requires edit permission."""
        client.force_login(outsider)

        response = client.get(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug})
        )

        assert response.status_code == 403


@pytest.mark.django_db
class TestCrossVisibilityWorkflows:
    """Test workflows when switching between visibility modes."""

    def test_switching_from_authenticated_to_public_requires_ack_if_collects_patient_data(
        self, client, owner, authenticated_survey
    ):
        """Switching from AUTHENTICATED to PUBLIC requires patient data ack if survey collects it."""
        from checktick_app.surveys.models import QuestionGroup

        # Add patient demographics
        patient_group = QuestionGroup.objects.create(
            name="Patient Details",
            owner=owner,
            schema={
                "template": "patient_details_encrypted",
                "fields": ["nhs_number", "first_name", "surname"],
            },
        )
        authenticated_survey.question_groups.add(patient_group)

        client.force_login(owner)

        # Try to change to PUBLIC without acknowledgment
        response = client.post(
            reverse(
                "surveys:publish_settings", kwargs={"slug": authenticated_survey.slug}
            ),
            {
                "action": "save",
                "visibility": Survey.Visibility.PUBLIC,
                "no_patient_data_ack": "",  # Not checked
            },
        )

        # Should stay on page with error
        assert response.status_code == 200
        authenticated_survey.refresh_from_db()
        # Visibility should not change
        assert authenticated_survey.visibility == Survey.Visibility.AUTHENTICATED

    def test_unlisted_key_generated_automatically(self, client, owner, base_survey):
        """Unlisted key is automatically generated when publishing."""
        client.force_login(owner)

        assert base_survey.unlisted_key is None

        response = client.post(
            reverse("surveys:publish_settings", kwargs={"slug": base_survey.slug}),
            {
                "action": "publish",
                "visibility": Survey.Visibility.UNLISTED,
                "no_patient_data_ack": "on",
            },
        )

        assert response.status_code == 302
        base_survey.refresh_from_db()
        assert base_survey.unlisted_key is not None
        assert len(base_survey.unlisted_key) > 20  # Should be random token
