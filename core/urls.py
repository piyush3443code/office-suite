from django.urls import path
from .views import SignUpView, home, ForgotPasswordView, VerifyOTPView, ResetPasswordView, node_monitor

urlpatterns = [
    path('signup/', SignUpView.as_view(), name='signup'),
    path('', home, name='home'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot_password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('node-monitor/', node_monitor, name='node_monitor'),
]
