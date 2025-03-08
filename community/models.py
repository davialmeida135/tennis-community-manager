from django.db import models
from users.models import User

class Community(models.Model):
    community_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    picture = models.ImageField(upload_to='community/', null=True, blank=True)

    def __str__(self):
        return self.name
    
class CommunityMembers(models.Model):
    ROLE_CHOICES = [
        ("member", "Member"),
        ("moderator", "Moderator"),
        ("admin", "Admin"),     
    ]

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="community_members")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="community_entries")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="member")

    def __str__(self):
        return f"{self.user.name} in {self.community.name}"