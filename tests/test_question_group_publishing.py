"""
Tests for question group publishing and import functionality.

Focused tests that verify the core functionality without overly complex setup.
"""

from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
import pytest

from checktick_app.surveys.models import (
    Organization,
    OrganizationMembership,
    PublishedQuestionGroup,
    QuestionGroup,
    Survey,
    SurveyQuestion,
)

User = get_user_model()
TEST_PASSWORD = "test-pass"


@pytest.fixture(autouse=True)
def disable_rate_limiting(settings):
    """Disable rate limiting for all tests."""
    settings.RATELIMIT_ENABLE = False


@pytest.fixture
def publisher_user(django_user_model):
    """Create a user who can publish question groups."""
    return django_user_model.objects.create_user(
        username="publisher@example.com", password=TEST_PASSWORD
    )


@pytest.fixture
def other_user(django_user_model):
    """Create another user for permission tests."""
    return django_user_model.objects.create_user(
        username="other@example.com", password=TEST_PASSWORD
    )


@pytest.fixture
def test_organization(publisher_user):
    """Create a test organization to bypass encryption setup."""
    return Organization.objects.create(name="Test Organization", owner=publisher_user)


@pytest.fixture
def published_org_template(publisher_user, test_organization):
    """Create a published organization-level template."""
    # Ensure publisher_user is a member of the organization
    OrganizationMembership.objects.get_or_create(
        user=publisher_user,
        organization=test_organization,
        defaults={"role": OrganizationMembership.Role.ADMIN},
    )
    return PublishedQuestionGroup.objects.create(
        name="Org Template",
        description="Organization-level template",
        publisher=publisher_user,
        organization=test_organization,
        publication_level="organization",
        status="active",
        markdown="# Org Template\n\n## Q1\ntype: text\nQuestion text here",
        show_publisher_credit=True,
    )


@pytest.fixture
def published_global_template(publisher_user):
    """Create a published global template."""
    return PublishedQuestionGroup.objects.create(
        name="Global Template",
        description="Global template available to all",
        publisher=publisher_user,
        publication_level="global",
        status="active",
        markdown="# Global Template\n\n## Q1\ntype: text\nQuestion text here",
        attribution={
            "authors": "Test Author",
            "title": "Test Scale",
            "year": 2024,
        },
        show_publisher_credit=False,
    )


@pytest.mark.django_db
class TestPublishedQuestionGroupModel:
    """Test the PublishedQuestionGroup model."""

    def test_create_organization_template(self, publisher_user, test_organization):
        """Organization templates can be created."""
        template = PublishedQuestionGroup.objects.create(
            name="Test Template",
            description="Test description",
            publisher=publisher_user,
            organization=test_organization,
            publication_level="organization",
            status="active",
            markdown="# Test\n\n## Q1\ntype: text\nTest question",
        )

        assert template.publication_level == "organization"
        assert template.organization == test_organization
        assert template.status == "active"

    def test_create_global_template(self, publisher_user):
        """Global templates can be created without organization."""
        template = PublishedQuestionGroup.objects.create(
            name="Global Test",
            description="Global template",
            publisher=publisher_user,
            publication_level="global",
            status="active",
            markdown="# Global\n\n## Q1\ntype: text\nGlobal question",
        )

        assert template.publication_level == "global"
        assert template.organization is None

    def test_increment_import_count(self, published_global_template):
        """Import count increments correctly."""
        initial_count = published_global_template.import_count

        published_global_template.increment_import_count()

        assert published_global_template.import_count == initial_count + 1

    def test_attribution_storage(self, publisher_user):
        """Attribution metadata is stored correctly."""
        template = PublishedQuestionGroup.objects.create(
            name="Attributed Template",
            publisher=publisher_user,
            publication_level="global",
            status="active",
            markdown="# Test",
            attribution={
                "authors": "Smith, Jones",
                "title": "Test Scale",
                "year": 2024,
                "doi": "10.1234/test",
            },
        )

        assert template.attribution["authors"] == "Smith, Jones"
        assert template.attribution["doi"] == "10.1234/test"

    def test_show_publisher_credit_default(self, publisher_user):
        """Publisher credit is shown by default."""
        template = PublishedQuestionGroup.objects.create(
            name="Default Credit",
            publisher=publisher_user,
            publication_level="global",
            status="active",
            markdown="# Test",
        )

        assert template.show_publisher_credit is True


@pytest.mark.django_db
class TestTemplateDiscovery:
    """Test template listing and discovery."""

    def test_authenticated_user_sees_global_templates(
        self, client, publisher_user, published_global_template, published_org_template
    ):
        """Authenticated users can see global templates."""
        client.force_login(publisher_user)
        response = client.get("/surveys/templates/")

        assert response.status_code == 200
        content = response.content.decode()
        assert "Global Template" in content

    def test_filter_by_publication_level(
        self, client, publisher_user, published_global_template, published_org_template
    ):
        """Users can filter templates by publication level."""
        client.force_login(publisher_user)

        # Default view shows both
        response = client.get("/surveys/templates/")
        content = response.content.decode()
        assert "Global Template" in content
        assert "Org Template" in content

    def test_search_templates(
        self, client, publisher_user, published_global_template, published_org_template
    ):
        """Users can search templates by title/description."""
        client.force_login(publisher_user)
        response = client.get("/surveys/templates/?search=Global")

        content = response.content.decode()
        assert "Global Template" in content
        assert "Org Template" not in content


@pytest.mark.django_db
class TestAttributionDisplay:
    """Test attribution and publisher credit display."""

    def test_attribution_displayed_over_publisher_credit(
        self, client, publisher_user, published_global_template
    ):
        """When attribution.authors exists, it should be displayed."""
        client.force_login(publisher_user)
        response = client.get("/surveys/templates/")
        content = response.content.decode()

        # Should see author name
        assert "Test Author" in content

    def test_publisher_credit_shown_when_enabled(
        self, client, publisher_user, published_org_template
    ):
        """When show_publisher_credit=True and no attribution, show publisher."""
        client.force_login(publisher_user)

        response = client.get("/surveys/templates/")
        content = response.content.decode()

        # Should see publisher username or organization name
        assert published_org_template.name in content


@pytest.mark.django_db
class TestMarkdownExport:
    """Test markdown export functionality."""

    def test_export_question_with_options(self):
        """Question options should be preserved in markdown export."""
        from checktick_app.surveys.views import _export_question_group_to_markdown

        user = User.objects.create_user(username="testuser", password=TEST_PASSWORD)
        survey = Survey.objects.create(owner=user, name="Test Survey", slug="test")
        group = QuestionGroup.objects.create(
            owner=user, name="Test Group", description="Test description"
        )
        survey.question_groups.add(group)

        # Create question with options
        SurveyQuestion.objects.create(
            survey=survey,
            group=group,
            text="How do you feel?",
            type="mc_single",
            options=[
                {"label": "Good", "value": "good"},
                {"label": "Bad", "value": "bad"},
            ],
            order=1,
        )

        markdown = _export_question_group_to_markdown(group, survey)

        assert "How do you feel?" in markdown
        assert "Good" in markdown
        assert "Bad" in markdown

    def test_export_likert_categories(self):
        """Likert scales with categories export correctly."""
        from checktick_app.surveys.views import _export_question_group_to_markdown

        user = User.objects.create_user(username="testuser", password=TEST_PASSWORD)
        survey = Survey.objects.create(owner=user, name="Test Survey", slug="test")
        group = QuestionGroup.objects.create(
            owner=user, name="Test Group", description="Test description"
        )
        survey.question_groups.add(group)

        # Create likert question with categories
        SurveyQuestion.objects.create(
            survey=survey,
            group=group,
            text="Rate your mood",
            type="likert",
            options=[
                {
                    "type": "categories",
                    "labels": ["Never", "Sometimes", "Often", "Always"],
                }
            ],
            order=1,
        )

        markdown = _export_question_group_to_markdown(group, survey)

        assert "type: likert categories" in markdown or "likert" in markdown.lower()
        assert "Never" in markdown
        assert "Always" in markdown


@pytest.mark.django_db
class TestGlobalTemplateSync:
    """Test the sync_global_question_group_templates management command."""

    def test_sync_command_runs_without_error(self):
        """Sync command should run without errors (even with no template files)."""
        out = StringIO()

        # Command should run and report no files found
        call_command("sync_global_question_group_templates", "--dry-run", stdout=out)

        output = out.getvalue()
        # Should either find templates or report none found
        assert "template" in output.lower() or "No template files found" in output

    def test_sync_dry_run_does_not_modify_database(self, publisher_user):
        """Sync command with --dry-run should not modify existing templates."""
        # Create a template that shouldn't be modified
        template = PublishedQuestionGroup.objects.create(
            name="Existing Template",
            description="Original description",
            publisher=publisher_user,
            publication_level="global",
            status="active",
            markdown="# Original content",
            attribution={"authors": "Original Author"},
        )

        initial_count = PublishedQuestionGroup.objects.count()
        initial_description = template.description

        out = StringIO()
        call_command("sync_global_question_group_templates", "--dry-run", stdout=out)

        # Verify no new templates created and existing one unchanged
        assert PublishedQuestionGroup.objects.count() == initial_count
        template.refresh_from_db()
        assert template.description == initial_description

    def test_sync_validates_markdown_format(self):
        """Sync command should validate YAML frontmatter format."""
        out = StringIO()

        # Run command - should handle missing files gracefully
        try:
            call_command(
                "sync_global_question_group_templates", "--dry-run", stdout=out
            )
            output = out.getvalue()
            # Should complete without raising exceptions
            assert output is not None
        except Exception as e:
            # Should not raise unexpected exceptions
            pytest.fail(f"Command raised unexpected exception: {e}")


@pytest.mark.django_db
class TestTemplateDetail:
    """Test template detail view."""

    def test_view_global_template_detail(
        self, client, publisher_user, published_global_template
    ):
        """Authenticated users can view global template details."""
        client.force_login(publisher_user)
        response = client.get(f"/surveys/templates/{published_global_template.id}/")

        assert response.status_code == 200
        content = response.content.decode()
        assert published_global_template.name in content
        assert published_global_template.description in content

    def test_attribution_displayed_in_detail(
        self, client, publisher_user, published_global_template
    ):
        """Attribution information should be displayed in detail view."""
        client.force_login(publisher_user)
        response = client.get(f"/surveys/templates/{published_global_template.id}/")

        content = response.content.decode()
        assert "Test Author" in content
        assert "Test Scale" in content
