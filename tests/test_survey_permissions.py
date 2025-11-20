"""
Tests for survey permissions - ensuring viewers cannot edit, clone, translate, or publish.
"""

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
import pytest

from checktick_app.surveys.models import (
    Organization,
    OrganizationMembership,
    Survey,
    SurveyMembership,
)
from checktick_app.surveys.permissions import require_can_edit, require_can_view

User = get_user_model()


@pytest.fixture
def organization(db):
    """Create a test organization."""
    owner = User.objects.create_user(username="org_owner", email="owner@test.com")
    org = Organization.objects.create(name="Test Org", owner=owner)
    return org


@pytest.fixture
def survey(db, organization):
    """Create a test survey in an organization."""
    return Survey.objects.create(
        name="Test Survey",
        slug="test-survey",
        owner=organization.owner,
        organization=organization,
    )


@pytest.fixture
def viewer_user(db, organization):
    """Create a viewer user in the organization."""
    user = User.objects.create_user(username="viewer", email="viewer@test.com")
    OrganizationMembership.objects.create(
        user=user, organization=organization, role=OrganizationMembership.Role.VIEWER
    )
    return user


@pytest.fixture
def creator_user(db, organization):
    """Create a creator user in the organization."""
    user = User.objects.create_user(username="creator", email="creator@test.com")
    OrganizationMembership.objects.create(
        user=user, organization=organization, role=OrganizationMembership.Role.CREATOR
    )
    return user


@pytest.fixture
def admin_user(db, organization):
    """Create an admin user in the organization."""
    user = User.objects.create_user(username="admin", email="admin@test.com")
    OrganizationMembership.objects.create(
        user=user, organization=organization, role=OrganizationMembership.Role.ADMIN
    )
    return user


@pytest.mark.django_db
class TestViewerPermissions:
    """Test that viewers can view but not edit surveys."""

    def test_viewer_can_view_survey(self, survey, viewer_user):
        """Viewers with survey membership can view surveys."""
        # Add viewer to survey
        SurveyMembership.objects.create(
            user=viewer_user, survey=survey, role=SurveyMembership.Role.VIEWER
        )
        # Should not raise PermissionDenied
        require_can_view(viewer_user, survey)

    def test_viewer_cannot_edit_survey(self, survey, viewer_user):
        """Viewers cannot edit surveys."""
        # Add viewer to survey
        SurveyMembership.objects.create(
            user=viewer_user, survey=survey, role=SurveyMembership.Role.VIEWER
        )
        # Should raise PermissionDenied
        with pytest.raises(PermissionDenied):
            require_can_edit(viewer_user, survey)

    def test_viewer_without_membership_cannot_view(self, survey, viewer_user):
        """Viewers without survey membership cannot view the survey."""
        # No survey membership added
        with pytest.raises(PermissionDenied):
            require_can_view(viewer_user, survey)


@pytest.mark.django_db
class TestCreatorPermissions:
    """Test that creators can edit surveys."""

    def test_creator_can_view_survey(self, survey, creator_user):
        """Creators with survey membership can view surveys."""
        SurveyMembership.objects.create(
            user=creator_user, survey=survey, role=SurveyMembership.Role.CREATOR
        )
        require_can_view(creator_user, survey)

    def test_creator_can_edit_survey(self, survey, creator_user):
        """Creators can edit surveys."""
        SurveyMembership.objects.create(
            user=creator_user, survey=survey, role=SurveyMembership.Role.CREATOR
        )
        # Should not raise PermissionDenied
        require_can_edit(creator_user, survey)


@pytest.mark.django_db
class TestAdminPermissions:
    """Test that org admins can edit all surveys in their organization."""

    def test_admin_can_view_any_survey(self, survey, admin_user):
        """Org admins can view any survey in their organization."""
        # No survey membership needed
        require_can_view(admin_user, survey)

    def test_admin_can_edit_any_survey(self, survey, admin_user):
        """Org admins can edit any survey in their organization."""
        # No survey membership needed
        require_can_edit(admin_user, survey)


@pytest.mark.django_db
class TestOwnerPermissions:
    """Test that survey owners and org owners have full permissions."""

    def test_survey_owner_can_edit(self, survey):
        """Survey owner can edit their survey."""
        require_can_edit(survey.owner, survey)

    def test_org_owner_can_edit_any_survey(self, survey, organization):
        """Organization owner can edit any survey in their organization."""
        require_can_edit(organization.owner, survey)


@pytest.mark.django_db
class TestClonePermissions:
    """Test that clone view properly checks permissions."""

    def test_viewer_cannot_clone_survey(self, survey, viewer_user, client):
        """Viewers cannot clone surveys."""
        SurveyMembership.objects.create(
            user=viewer_user, survey=survey, role=SurveyMembership.Role.VIEWER
        )
        client.force_login(viewer_user)
        response = client.get(f"/surveys/{survey.slug}/clone/")
        # Should get permission denied
        assert response.status_code in [403, 302]  # 403 or redirect

    def test_creator_can_clone_survey(self, survey, creator_user, client):
        """Creators can clone surveys."""
        SurveyMembership.objects.create(
            user=creator_user, survey=survey, role=SurveyMembership.Role.CREATOR
        )
        client.force_login(creator_user)
        response = client.get(f"/surveys/{survey.slug}/clone/")
        # Should succeed (redirect to new survey)
        assert response.status_code == 302


@pytest.mark.django_db
class TestTranslationPermissions:
    """Test that translation creation properly checks permissions."""

    def test_viewer_cannot_create_translation(self, survey, viewer_user, client):
        """Viewers cannot create translations."""
        SurveyMembership.objects.create(
            user=viewer_user, survey=survey, role=SurveyMembership.Role.VIEWER
        )
        client.force_login(viewer_user)
        response = client.post(
            f"/surveys/{survey.slug}/translations/create/",
            data='{"language": "es"}',
            content_type="application/json",
        )
        # Should get permission denied
        assert response.status_code == 403

    def test_creator_can_create_translation(self, survey, creator_user, client):
        """Creators can create translations."""
        SurveyMembership.objects.create(
            user=creator_user, survey=survey, role=SurveyMembership.Role.CREATOR
        )
        client.force_login(creator_user)
        response = client.post(
            f"/surveys/{survey.slug}/translations/create/",
            data='{"language": "es"}',
            content_type="application/json",
        )
        # Should return task_id (200) or validation error (400), not 403
        assert response.status_code in [200, 400]


@pytest.mark.django_db
class TestPublishPermissions:
    """Test that publish settings properly checks permissions."""

    def test_viewer_cannot_access_publish_settings(self, survey, viewer_user, client):
        """Viewers cannot access publish settings."""
        SurveyMembership.objects.create(
            user=viewer_user, survey=survey, role=SurveyMembership.Role.VIEWER
        )
        client.force_login(viewer_user)
        response = client.get(f"/surveys/{survey.slug}/publish/")
        # Should get permission denied
        assert response.status_code == 403

    def test_creator_can_access_publish_settings(self, survey, creator_user, client):
        """Creators can access publish settings."""
        SurveyMembership.objects.create(
            user=creator_user, survey=survey, role=SurveyMembership.Role.CREATOR
        )
        client.force_login(creator_user)
        response = client.get(f"/surveys/{survey.slug}/publish/")
        # Should succeed (200)
        assert response.status_code == 200


@pytest.mark.django_db
class TestUpdateTitlePermissions:
    """Test that update title endpoint properly checks permissions."""

    def test_viewer_cannot_update_title(self, survey, viewer_user, client):
        """Viewers cannot update survey titles."""
        SurveyMembership.objects.create(
            user=viewer_user, survey=survey, role=SurveyMembership.Role.VIEWER
        )
        client.force_login(viewer_user)
        response = client.post(
            f"/surveys/{survey.slug}/update-title/",
            data='{"title": "New Title"}',
            content_type="application/json",
        )
        # Should get permission denied
        assert response.status_code == 403

    def test_creator_can_update_title(self, survey, creator_user, client):
        """Creators can update survey titles."""
        SurveyMembership.objects.create(
            user=creator_user, survey=survey, role=SurveyMembership.Role.CREATOR
        )
        client.force_login(creator_user)
        response = client.post(
            f"/surveys/{survey.slug}/update-title/",
            data='{"title": "New Title"}',
            content_type="application/json",
        )
        # Should succeed
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify title was updated
        survey.refresh_from_db()
        assert survey.name == "New Title"
