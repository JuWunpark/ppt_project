from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import SignUpForm
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from .forms import UserUpdateForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')  # 로그인 후 이동할 페이지
    else:
        form = SignUpForm()
    return render(request, 'blog/signup.html', {'form': form})

# def user_login(request):
#     if request.method == "POST":
#         form = AuthenticationForm(request, data=request.POST)
#         if form.is_valid():
#             user = form.get_user()
#             login(request, user)
#             return redirect('home')  # 로그인 후 이동할 페이지
#     else:
#         form = AuthenticationForm()
#     return render(request, 'blog/login.html', {'form': form})

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')  # 이미 로그인한 경우 홈으로 리디렉트

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # 로그인 후 이동할 페이지
    else:
        form = AuthenticationForm()
    return render(request, 'blog/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

@login_required #데코레이터로 로그인한 사용자만 수정 가능
def user_update(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # 회원정보 수정 후 이동할 페이지
    else:
        form = UserUpdateForm(instance=request.user) #현재 로그인한 사용자의 정보 가져오기
    return render(request, 'blog/user_update.html', {'form': form})

@login_required
def password_change(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # 비밀번호 변경 후 로그인 유지
            return redirect('home')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'blog/password_change.html', {'form': form})

def home(request):
    return render(request, 'home.html')