from django.contrib.auth import views as auth_views
from django.urls import path
from . import views
from .views import (
    Sign_in_home, password_change, signup, user_login, user_logout,
    home, prompt, profile, profile_view, download_slide)

# app_name = 'blog'
urlpatterns = [
    path('', home, name='home'),
    path('signup/', signup, name='signup'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('main/', Sign_in_home, name='sign_in'),
    path('password_change/', password_change, name='password_change'),
    path('prompt/', prompt, name='prompt'),
    # path("chat/", chat_view, name="chat"),
    path('result/', views.display_slides, name='result'),
    # path('export/', export, name='export'),
    path('profile/', profile_view, name='profile'),
    path('delete_user_history/', views.delete_user_history, name='delete_user_history'),
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    # path('slides/', views.display_slides, name='display_slides'),
    # path('slides_list/', views.slides_list_view, name='slides_list'),
    # path('/result/logout/', views.router, name='/result/logout'),
    # path('download_slide/<str:presentation_id>/', download_slide, name='download_slide'),  # 다운로드 경로 추가
    # 오타 수정 및 매개변수 추가
    path('download_slide/<str:presentation_id>/', download_slide, name='download_slide')
]