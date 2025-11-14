from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.forms import TextInput, EmailInput, NumberInput, PasswordInput
from .models import CustomUser
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import PasswordChangeForm #비밀번호 변경
from django.contrib.auth.models import User


class LoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'input-field', 'placeholder': 'Enter your username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Enter your password'})
    )

class SignUpForm(UserCreationForm):
    nickname = forms.CharField(
        max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'input-field'})
    )
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={'class': 'input-field'})
    )

    class Meta:
        model = CustomUser  # ✅ CustomUser 모델 사용
        fields = ['username', 'nickname', 'email', 'password1', 'password2']  # ✅ 'nickname'과 'email' 추가
        widgets = {
            'username': TextInput(attrs={'class': "sign-up input", 'placeholder': 'Name'}),
            'nickname': TextInput(attrs={'class': "sign-up input", 'placeholder': 'Nickname'}),  # ✅ nickname 위젯 추가
            'email': EmailInput(attrs={'class': "sign-up input", 'placeholder': 'Email'}),  # ✅ email 위젯 추가
            'password1': PasswordInput(attrs={'class': "sign-up input", 'placeholder': 'Password'}),
            'password2': PasswordInput(attrs={'class': "sign-up input", 'placeholder': 'Password (again)'}),
        }

    def clean_email(self):  # ✅ 이메일 중복 방지
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

### 🔹 회원 정보 수정 폼
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['id','username', 'email']  # 원하는 필드만 수정 가능
        widgets = {

            'username': TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            # 'id': forms.HiddenInput(),  # id는 숨김 필드로 처리 (사용자가 수정하지 않도록)
            'id': TextInput(attrs={'class': 'form-control'})  # id는 숨김 필드로 처리 (사용자가 수정하지 않도록)
        }



### 🔹 비밀번호 변경 폼
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Current Password'})
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'New Password'})
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input-field', 'placeholder': 'Confirm New Password'})
    )
class UserUpdateForm(UserChangeForm):
    password = None  # 비밀번호 변경 없이 다른 정보만 수정

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'nickname')  # 사용자 이름, 이메일, 닉네임을 수정할 수 있도록 필드 지정
        widgets = {
            'username': forms.TextInput(attrs={  # 사용자 이름 입력 필드 스타일 설정
                'class': 'input',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={  # 이메일 입력 필드 스타일 설정
                'class': 'input',
                'placeholder': 'Email'
            }),
            'nickname': forms.TextInput(attrs={  # 닉네임 입력 필드 스타일 설정
                'class': 'input',
                'placeholder': 'Nickname'
            })
        }

    def clean_email(self):  # 이메일 중복 방지 (중복된 이메일 입력 시 ValidationError 발생)
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():  # 이미 사용 중인 이메일이 있으면 오류 발생
            raise forms.ValidationError("이미 사용 중인 이메일입니다.")
        return email

    def save(self, commit=True):  # 사용자 정보를 저장할 때 커스텀 처리
        user = super().save(commit=False)  # 부모 클래스의 save 메서드를 사용하여 사용자 객체 가져오기
        if commit:
            user.save()  # 변경 사항을 DB에 저장
        return user

    class Meta:  # ✅ 올바른 들여쓰기 (4칸)
        model = CustomUser
        fields = ('username', 'email', 'nickname')