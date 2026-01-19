from django.db import models
from django.contrib.auth.models import User
import random

class PasswordResetOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def is_valid(self):
        # OTP valid for 10 minutes
        from django.utils import timezone
        import datetime
        return self.created_at >= timezone.now() - datetime.timedelta(minutes=10)

    def __str__(self):
        return f"{self.user.username} - {self.otp_code}"
