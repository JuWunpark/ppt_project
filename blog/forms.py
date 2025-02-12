from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import PasswordChangeForm #비밀번호 변경

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'nickname', 'password1', 'password2')


    def clean_email(self): #이메일중복방지
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

class UserUpdateForm(UserChangeForm):
    password = None  # 비밀번호 변경 없이 다른 정보만 수정

    class Meta:  # ✅ 올바른 들여쓰기 (4칸)
        model = CustomUser
        fields = ('username', 'email', 'nickname')