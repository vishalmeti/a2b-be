"""
URL configuration for borrow_anything project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

# Import Simple JWT views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    # TokenVerifyView, # Optional: If you want an endpoint to verify tokens
)

urlpatterns = [
    path("admin/", admin.site.urls),
    # API v1 URLs
    path(
        "api/v1/",
        include(
            [
                # App URLs
                # path('items/', include('apps.items.urls')), # Assuming you add this later
                # ... other app urls ...
                # Authentication URLs using Simple JWT
                path(
                    "auth/token/",
                    TokenObtainPairView.as_view(),
                    name="token_obtain_pair",
                ),  # POST username/password -> returns access/refresh tokens
                path(
                    "auth/token/refresh/",
                    TokenRefreshView.as_view(),
                    name="token_refresh",
                ),  # POST refresh_token -> returns new access token
                # path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'), # Optional: POST token -> verifies if token is valid
                path("users/", include("apps.users.urls")),
            ]
        ),
    ),
]
