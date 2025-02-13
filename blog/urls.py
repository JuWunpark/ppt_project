from django.urls import path
from .views import user_update
from .views import password_change
from .views import signup, user_login, user_logout
from . import views

urlpatterns = [
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('update/', user_update, name='user_update'),

    path('password_change/', password_change, name='password_change'),

    path('', views.home, name='home'),

    path('prompt/', views.prompt, name='prompt'),

    path('export/', views.export, name='export'),

    path('export/', views.export, name='export'),

]

