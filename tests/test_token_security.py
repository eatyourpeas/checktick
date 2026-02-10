"""
Comprehensive security tests for token management endpoints.

Tests authentication, authorization, rate limiting, and permission enforcement
for all token-related routes.
"""

from django.contrib.auth import get_user_model
from django.urls import reverse
import pytest

from checktick_app.surveys.models import (
    Organization,
    OrganizationMembership,
    QuestionGroup,
    Survey,
    SurveyAccessToken,
    SurveyMembership,
)

User = get_user_model()
TEST_PASSWORD = "testpass123"


@pytest.fixture
def survey_owner(db):
    """Create a survey owner user."""
    return User.objects.create_user(
        username="owner", email="owner@test.com", password=TEST_PASSWORD
    )


@pytest.fixture
def organization(survey_owner):
    """Create an organization owned by survey_owner."""
    return Organization.objects.create(name="Test Org", owner=survey_owner)


@pytest.fixture
def org_admin(db, organization):
    """Create an organization admin user."""
    user = User.objects.create_user(
        username="org_admin", email="admin@test.com", password=TEST_PASSWORD
    )
    OrganizationMembership.objects.create(
        user=user, organization=organization, role=OrganizationMembership.Role.ADMIN
    )
    return user


@pytest.fixture
def org_creator(db, organization):
    """Create an organization creator user."""
    user = User.objects.create_user(
        username="org_creator", email="creator@test.com", password=TEST_PASSWORD
    )
    OrganizationMembership.objects.create(
        user=user, organization=organization, role=OrganizationMembership.Role.CREATOR
    )
    return user


@pytest.fixture
def org_viewer(db, organization):
    """Create an organization viewer user (read-only)."""
    user = User.objects.create_user(
        username="org_viewer", email="viewer@test.com", password=TEST_PASSWORD
    )
    OrganizationMembership.objects.create(
        user=user, organization=organization, role=OrganizationMembership.Role.VIEWER
    )
    return user


@pytest.fixture
def outsider(db):
    """Create a user not part of the organization."""
    return User.objects.create_user(
        username="outsider", email="outsider@test.com", password=TEST_PASSWORD
    )


@pytest.fixture
def survey(survey_owner, organization):
    """Create a published token-based survey."""
    survey = Survey.objects.create(
        name="Test Survey",
        slug="test-survey",
        owner=survey_owner,
        organization=organization,
        status=Survey.Status.PUBLISHED,
        visibility=Survey.Visibility.TOKEN,
    )
    # Add question group to make survey valid
    group = QuestionGroup.objects.create(name="Questions", owner=survey_owner)
    survey.question_groups.add(group)
    return survey


@pytest.fixture
def survey_with_creator(survey, org_creator):
    """Survey where org_creator has explicit creator role."""
    SurveyMembership.objects.create(
        user=org_creator, survey=survey, role=SurveyMembership.Role.CREATOR
    )
    return survey


@pytest.fixture
def survey_with_viewer(survey, org_viewer):
    """Survey where org_viewer has explicit viewer role."""
    SurveyMembership.objects.create(
        user=org_viewer, survey=survey, role=SurveyMembership.Role.VIEWER
    )
    return survey


@pytest.fixture
def token(survey, survey_owner):
    """Create a test access token."""
    return SurveyAccessToken.objects.create(
        survey=survey,
        token="test-token-123",
        created_by=survey_owner,
        note="Invited: user@example.com",
    )


@pytest.mark.django_db
class TestTokenManagementAuthentication:
    """Test that all token endpoints require authentication."""

    def test_tokens_page_requires_login(self, client, survey):
        """Token management page requires login."""
        response = client.get(reverse("surveys:tokens", kwargs={"slug": survey.slug}))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_tokens_export_requires_login(self, client, survey):
        """Token export requires login."""
        response = client.get(
            reverse("surveys:tokens_export_csv", kwargs={"slug": survey.slug})
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_invites_pending_requires_login(self, client, survey):
        """Invites pending page requires login."""
        response = client.get(
            reverse("surveys:invites_pending", kwargs={"slug": survey.slug})
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_invite_resend_requires_login(self, client, survey, token):
        """Invite resend requires login."""
        response = client.post(
            reverse(
                "surveys:invite_resend",
                kwargs={"slug": survey.slug, "token_id": token.id},
            )
        )
        assert response.status_code == 302
        assert "/accounts/login/" in response.url


@pytest.mark.django_db
class TestTokenManagementAuthorization:
    """Test permission enforcement for token endpoints."""

    # GET /surveys/<slug>/tokens/ - requires can_edit

    def test_owner_can_access_tokens(self, client, survey, survey_owner):
        """Survey owner can access token management."""
        client.force_login(survey_owner)
        response = client.get(reverse("surveys:tokens", kwargs={"slug": survey.slug}))
        assert response.status_code == 200

    def test_org_admin_can_access_tokens(self, client, survey, org_admin):
        """Org admin can access token management."""
        client.force_login(org_admin)
        response = client.get(reverse("surveys:tokens", kwargs={"slug": survey.slug}))
        assert response.status_code == 200

    def test_creator_can_access_tokens(self, client, survey_with_creator, org_creator):
        """Survey creator can access token management."""
        client.force_login(org_creator)
        response = client.get(
            reverse("surveys:tokens", kwargs={"slug": survey_with_creator.slug})
        )
        assert response.status_code == 200

    def test_viewer_cannot_access_tokens(self, client, survey_with_viewer, org_viewer):
        """Viewer cannot access token management (403)."""
        client.force_login(org_viewer)
        response = client.get(
            reverse("surveys:tokens", kwargs={"slug": survey_with_viewer.slug})
        )
        assert response.status_code == 403

    def test_outsider_cannot_access_tokens(self, client, survey, outsider):
        """Non-member cannot access token management (403)."""
        client.force_login(outsider)
        response = client.get(reverse("surveys:tokens", kwargs={"slug": survey.slug}))
        assert response.status_code == 403

    # POST /surveys/<slug>/tokens/ - token creation

    def test_owner_can_create_tokens(self, client, survey, survey_owner):
        """Survey owner can create tokens."""
        client.force_login(survey_owner)
        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey.slug}),
            {"count": "5", "note": "Test batch"},
        )
        assert response.status_code == 302
        assert SurveyAccessToken.objects.filter(survey=survey).count() == 5

    def test_org_admin_can_create_tokens(self, client, survey, org_admin):
        """Org admin can create tokens."""
        client.force_login(org_admin)
        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey.slug}),
            {"count": "3", "note": "Admin batch"},
        )
        assert response.status_code == 302
        assert SurveyAccessToken.objects.filter(survey=survey).count() == 3

    def test_creator_can_create_tokens(self, client, survey_with_creator, org_creator):
        """Survey creator can create tokens."""
        client.force_login(org_creator)
        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey_with_creator.slug}),
            {"count": "2", "note": "Creator batch"},
        )
        assert response.status_code == 302
        assert SurveyAccessToken.objects.filter(survey=survey_with_creator).count() == 2

    def test_viewer_cannot_create_tokens(self, client, survey_with_viewer, org_viewer):
        """Viewer cannot create tokens (403)."""
        client.force_login(org_viewer)
        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey_with_viewer.slug}),
            {"count": "5"},
        )
        assert response.status_code == 403
        assert SurveyAccessToken.objects.filter(survey=survey_with_viewer).count() == 0

    def test_outsider_cannot_create_tokens(self, client, survey, outsider):
        """Non-member cannot create tokens (403)."""
        client.force_login(outsider)
        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey.slug}), {"count": "5"}
        )
        assert response.status_code == 403
        assert SurveyAccessToken.objects.filter(survey=survey).count() == 0

    # GET /surveys/<slug>/tokens/export.csv

    def test_owner_can_export_tokens(self, client, survey, survey_owner, token):
        """Survey owner can export tokens."""
        client.force_login(survey_owner)
        response = client.get(
            reverse("surveys:tokens_export_csv", kwargs={"slug": survey.slug})
        )
        assert response.status_code == 200
        assert response["Content-Type"] == "text/csv"

    def test_viewer_cannot_export_tokens(
        self, client, survey_with_viewer, org_viewer, token
    ):
        """Viewer cannot export tokens (403)."""
        client.force_login(org_viewer)
        response = client.get(
            reverse(
                "surveys:tokens_export_csv", kwargs={"slug": survey_with_viewer.slug}
            )
        )
        assert response.status_code == 403

    # GET /surveys/<slug>/invites/pending/

    def test_owner_can_view_invites_pending(self, client, survey, survey_owner):
        """Survey owner can view pending invites."""
        client.force_login(survey_owner)
        response = client.get(
            reverse("surveys:invites_pending", kwargs={"slug": survey.slug})
        )
        assert response.status_code == 200

    def test_viewer_can_view_invites_pending(
        self, client, survey_with_viewer, org_viewer
    ):
        """Viewer CAN view pending invites (uses require_can_view, not require_can_edit)."""
        client.force_login(org_viewer)
        response = client.get(
            reverse("surveys:invites_pending", kwargs={"slug": survey_with_viewer.slug})
        )
        assert response.status_code == 200

    def test_outsider_cannot_view_invites_pending(self, client, survey, outsider):
        """Non-member cannot view pending invites (403)."""
        client.force_login(outsider)
        response = client.get(
            reverse("surveys:invites_pending", kwargs={"slug": survey.slug})
        )
        assert response.status_code == 403

    # POST /surveys/<slug>/invites/<token_id>/resend/

    def test_owner_can_resend_invite(self, client, survey, survey_owner, token):
        """Survey owner can resend invites."""
        client.force_login(survey_owner)
        response = client.post(
            reverse(
                "surveys:invite_resend",
                kwargs={"slug": survey.slug, "token_id": token.id},
            )
        )
        # Should redirect back to invites_pending
        assert response.status_code == 302
        assert "invites/pending" in response.url

    def test_viewer_cannot_resend_invite(
        self, client, survey_with_viewer, org_viewer, token
    ):
        """Viewer cannot resend invites (403)."""
        # Update token to belong to survey_with_viewer
        token.survey = survey_with_viewer
        token.save()

        client.force_login(org_viewer)
        response = client.post(
            reverse(
                "surveys:invite_resend",
                kwargs={"slug": survey_with_viewer.slug, "token_id": token.id},
            )
        )
        assert response.status_code == 403

    def test_outsider_cannot_resend_invite(self, client, survey, outsider, token):
        """Non-member cannot resend invites (403)."""
        client.force_login(outsider)
        response = client.post(
            reverse(
                "surveys:invite_resend",
                kwargs={"slug": survey.slug, "token_id": token.id},
            )
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestTokenManagementRateLimiting:
    """Test rate limiting on token POST endpoints."""

    def test_token_creation_rate_limited(self, client, survey, survey_owner, settings):
        """Token creation POST endpoint is rate limited (60/hour)."""
        # Configure in-memory cache for testing
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }

        client.force_login(survey_owner)

        # Make multiple requests up to the limit
        url = reverse("surveys:tokens", kwargs={"slug": survey.slug})

        # First request should succeed
        response = client.post(url, {"count": "1"})
        assert response.status_code == 302

        # Simulate many rapid requests by calling the endpoint multiple times
        # The exact limit is 60/hour, but we'll test that blocking occurs
        for i in range(61):
            response = client.post(url, {"count": "1"})

        # After exceeding rate limit, should get 429 or 403
        # (depends on django-ratelimit configuration)
        assert response.status_code in [429, 403]

    def test_invite_resend_rate_limited(
        self, client, survey, survey_owner, token, settings
    ):
        """Invite resend POST endpoint is rate limited (30/hour)."""
        # Configure in-memory cache for testing
        settings.CACHES = {
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            }
        }

        client.force_login(survey_owner)

        url = reverse(
            "surveys:invite_resend",
            kwargs={"slug": survey.slug, "token_id": token.id},
        )

        # First request should succeed
        response = client.post(url)
        assert response.status_code == 302

        # Simulate many rapid requests
        for i in range(31):
            response = client.post(url)

        # After exceeding rate limit, should be blocked
        assert response.status_code in [429, 403]


@pytest.mark.django_db
class TestTokenManagementEdgeCases:
    """Test edge cases and security constraints."""

    def test_cannot_access_another_orgs_tokens(
        self, client, survey, survey_owner, outsider
    ):
        """Users cannot access tokens from surveys in other organizations."""
        # Create another org with outsider
        other_org = Organization.objects.create(name="Other Org", owner=outsider)
        OrganizationMembership.objects.create(
            user=outsider,
            organization=other_org,
            role=OrganizationMembership.Role.ADMIN,
        )

        # Outsider should not be able to access survey's tokens
        client.force_login(outsider)
        response = client.get(reverse("surveys:tokens", kwargs={"slug": survey.slug}))
        assert response.status_code == 403

    def test_cannot_resend_token_from_different_survey(
        self, client, survey, survey_owner, token
    ):
        """Cannot resend a token by manipulating token_id to reference another survey's token."""
        # Create another survey
        other_survey = Survey.objects.create(
            name="Other Survey",
            slug="other-survey",
            owner=survey_owner,
            organization=survey.organization,
            status=Survey.Status.PUBLISHED,
            visibility=Survey.Visibility.TOKEN,
        )
        other_token = SurveyAccessToken.objects.create(
            survey=other_survey,
            token="other-token",
            created_by=survey_owner,
            note="Invited: other@example.com",
        )

        client.force_login(survey_owner)

        # Try to resend other_token using survey slug (should fail)
        response = client.post(
            reverse(
                "surveys:invite_resend",
                kwargs={"slug": survey.slug, "token_id": other_token.id},
            )
        )

        # Should get 404 because token doesn't belong to this survey
        assert response.status_code == 404

    def test_token_creation_validates_count_limits(self, client, survey, survey_owner):
        """Token creation enforces maximum count limit (1000)."""
        client.force_login(survey_owner)

        # Try to create more than 1000 tokens
        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey.slug}),
            {"count": "5000"},  # Exceeds limit
        )

        assert response.status_code == 302
        # Should only create 1000 tokens max
        assert SurveyAccessToken.objects.filter(survey=survey).count() == 1000

    def test_token_creation_handles_invalid_count(self, client, survey, survey_owner):
        """Token creation handles invalid count gracefully."""
        client.force_login(survey_owner)

        response = client.post(
            reverse("surveys:tokens", kwargs={"slug": survey.slug}),
            {"count": "invalid"},  # Not a number
        )

        assert response.status_code == 302
        # Should create 0 tokens
        assert SurveyAccessToken.objects.filter(survey=survey).count() == 0
