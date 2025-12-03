"""Signal handlers for core app models."""

import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UserProfile

User = get_user_model()
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile automatically when a new user is created."""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Ensure UserProfile exists and is saved when user is saved."""
    if not hasattr(instance, "profile"):
        UserProfile.objects.create(user=instance)
    else:
        instance.profile.save()


@receiver(post_save, sender=User)
def process_pending_invitations(sender, instance, created, **kwargs):
    """Process any pending team/org invitations for newly created users.

    When a user signs up, check if they have any pending invitations
    and automatically add them to the relevant teams/organizations.
    """
    if not created:
        return

    # Import here to avoid circular imports
    from checktick_app.surveys.models import OrgInvitation, TeamInvitation

    email = instance.email.lower() if instance.email else ""
    if not email:
        return

    # Process team invitations
    team_invites = TeamInvitation.objects.filter(
        email__iexact=email,
        accepted_at__isnull=True,
    ).select_related("team")

    for invite in team_invites:
        if invite.is_valid():
            try:
                membership = invite.accept(instance)
                logger.info(
                    f"Accepted team invitation for {email} to team {invite.team.name} "
                    f"with role {membership.role}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to process team invitation {invite.id} for {email}: {e}"
                )

    # Process organization invitations
    org_invites = OrgInvitation.objects.filter(
        email__iexact=email,
        accepted_at__isnull=True,
    ).select_related("organization")

    for invite in org_invites:
        if invite.is_valid():
            try:
                membership = invite.accept(instance)
                logger.info(
                    f"Accepted org invitation for {email} to org {invite.organization.name} "
                    f"with role {membership.role}"
                )
            except Exception as e:
                logger.error(
                    f"Failed to process org invitation {invite.id} for {email}: {e}"
                )
