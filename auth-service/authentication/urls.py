from django.urls import path

from authentication.views import LoginView, OtpView, RegisterView, UserView, VerifyView

urlpatterns = [
    path("register", RegisterView.as_view(), name="register"),
    path("login", LoginView.as_view(), name="login"),
    path("verify-otp", OtpView.as_view(), name="verify-otp"),
    path("verify", VerifyView.as_view(), name="verify"),
    path("<str:identifier>", UserView.as_view(), name="user"),
]
