from django.db import models
from django.conf import settings

from users.models import UserProfile

class Community(models.Model):
    community_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    picture = models.ImageField(upload_to='community/', null=True, blank=True)

    def __str__(self):
        return self.name
    
class CommunityUsers(models.Model):
    ROLE_CHOICES = [
        ("member", "Member"),
        ("moderator", "Moderator"),
        ("admin", "Admin"),   
        ("owner", "Owner"),
        ("pending_invitation", "Pending Invitation"),
        ("pending_request", "Pending Request"),   
    ]

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="community_users")
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="community_entries")
    role = models.CharField(max_length=25, choices=ROLE_CHOICES, default="member")
    
    class Meta:
        unique_together = ['community', 'user']  # Enforces uniqueness
        verbose_name_plural = "Community Users"
        
    def __str__(self):
        return f"{self.user.user.username} in {self.community.name} ({self.role})"