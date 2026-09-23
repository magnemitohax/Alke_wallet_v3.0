from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth (login/logout) provistos por django.contrib.auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # App principal
    path('', RedirectView.as_view(pattern_name='cliente_list', permanent=False)),
    path('', include('gestion.urls')),
]
