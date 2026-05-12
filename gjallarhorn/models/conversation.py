"""Conversation and Message models."""

from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """Chat conversation between user and Gjallarhorn agent."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    project = models.ForeignKey("ingestion.Project", on_delete=models.CASCADE, null=False)
    title = models.CharField(max_length=255, blank=True, default="")
    agent_identity = models.CharField(max_length=32, default="gjallarhorn")
    conversation_type = models.CharField(max_length=32)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "project"],
                name="uniq_conversation_user_project",
            ),
        ]

    def __str__(self):
        return f"Conversation {self.pk} — {self.user.email} / {self.project.slug}"


class Message(models.Model):
    """Single message in a conversation."""

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Message {self.pk} — {self.role} @ {self.created_at:%Y-%m-%d %H:%M}"
