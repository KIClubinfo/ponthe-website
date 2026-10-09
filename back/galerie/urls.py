"""
URL configuration for galerie project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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

import django_cas_ng.views
from django.contrib import admin
from django.urls import include, path

from . import views

admin.site.login = views.admin_login

urlpatterns = [
    path("", views.index, name="index"),
    path("", views.root_redirect),
    path("admin/", admin.site.urls),
    path("gallery/<slug:slug>", views.gallery, name="gallery"),
    path("galleries/", views.galleries, name="galleries"),
    path("expositions/", views.expositions, name="expositions"),
    path("material/", views.material, name="material"),
    path("gestion/", include("gestion.urls")),
    path("api/", include("api.urls")),
    path("login/", views.LoginView.as_view(), name="login"),
    path("", include("django.contrib.auth.urls")),
    path(
        "accounts/login/", django_cas_ng.views.LoginView.as_view(), name="cas_ng_login"
    ),
    path(
        "accounts/logout/",
        django_cas_ng.views.LogoutView.as_view(),
        name="cas_ng_logout",
    ),
    path("add_promo/", views.add_promo, name="add_promo"),
]

# In debug mode too: the files used to be served straight from the folder
# then, private galleries included, with no access check at all.
urlpatterns.append(path("media/<path:path>", views.media))
