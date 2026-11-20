from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class':      'form-control',
            'placeholder': 'Username or Matric Number',
            'autofocus':   True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class':       'form-control',
            'placeholder': 'Password',
        })
    )


class RegisterForm(UserCreationForm):

    DEPARTMENT_CHOICES = [
        ('', '— Select Department —'),
        ('Cyber Security Science',  'Cyber Security Science'),
        ('Software Engineering',    'Software Engineering'),
        ('Artificial Intelligence', 'Artificial Intelligence'),
        ('Information Technology',  'Information Technology'),
    ]

    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First name',
        })
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last name',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com',
        })
    )
    matric_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'e.g. 24A/UE/BCSX/1003',
        })
    )
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class':       'form-control',
            'placeholder': 'e.g. 08012345678',
        })
    )

    class Meta:
        model  = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'matric_number',
            'department',
            'phone',
            'username',
            'password1',
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': 'Choose a username',
        })
        self.fields['password1'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': 'Create a password',
        })
        self.fields['password2'].widget.attrs.update({
            'class':       'form-control',
            'placeholder': 'Confirm your password',
        })


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model  = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'department',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control'
            }),
        }