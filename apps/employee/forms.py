from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from .models import Profile, WorkShift, WorkerArea, EmotionAnalysis


class WorkerAreaForm(forms.ModelForm):

    class Meta:
        model = WorkerArea
        # fields = '__all__'
        exclude = [ 'created_at', 'updated_at', 'created_by', 'updated_by']

        labels = {
            
        }

        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, regimen_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean(self):
        try:
            sc = WorkerArea.objects.get(
                name=self.cleaned_data["name"]
            )
            if not self.instance.pk:
                print("Ya existe")
                raise forms.ValidationError("Ya existe")
            elif self.instance.pk != sc.pk:
                print("Cambio no permitido")
                raise forms.ValidationError("Cambio no permitido")
        except WorkerArea.DoesNotExist:
            pass
        return self.cleaned_data


class WorkShiftForm(forms.ModelForm):

    class Meta:
        model = WorkShift
        # fields = '__all__'
        exclude = ['created_at', 'updated_at', 'created_by', 'updated_by']

        labels = {
            'start_time': _('Start Time'),
            'end_time': _('End Time'),
        }

        widgets = {
            'start_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',  # Utiliza el tipo 'time' para mostrar un selector de tiempo en HTML5
            }),
            'end_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',  # También utiliza el tipo 'time' aquí
            }),
        }

    def __init__(self, *args, regimen_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in iter(self.fields):
            if field not in ['start_time', 'end_time']:
                self.fields[field].widget.attrs.update({
                    'class': 'form-control'
                })

    def clean(self):
        try:
            sc = WorkShift.objects.get(
                name=self.cleaned_data["name"]
            )
            if not self.instance.pk:
                print("Ya existe")
                raise forms.ValidationError("Ya existe")
            elif self.instance.pk != sc.pk:
                print("Cambio no permitido")
                raise forms.ValidationError("Cambio no permitido")
        except WorkShift.DoesNotExist:
            pass
        return self.cleaned_data


'''
class EmployeeForm(forms.ModelForm):

    class Meta:
        model = User
        fields = '__all__'
        # exclude = []

        labels = {
            
        }

        widgets = {
            
        }

    def __init__(self, *args, regimen_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def clean(self):
        try:
            sc = User.objects.get(
                username=self.cleaned_data["username"]
            )
            if not self.instance.pk:
                print("Ya existe")
                raise forms.ValidationError("Ya existe")
            elif self.instance.pk != sc.pk:
                print("Cambio no permitido")
                raise forms.ValidationError("Cambio no permitido")
        except User.DoesNotExist:
            pass
        return self.cleaned_data
'''


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    last_name = forms.CharField(max_length=30, required=False, help_text='Optional.')
    email = forms.EmailField(max_length=254, help_text='Required. Inform a valid email address.')

    # Campos relacionados del perfil
    identity_document = forms.CharField(max_length=15, required=False, help_text='Optional.')
    birth_date = forms.DateField(required=False, help_text='Required. Format: YYYY-MM-DD')
    work_shift = forms.ModelChoiceField(queryset=WorkShift.objects.all(), required=True, help_text='Select the work shift.')
    worker_area = forms.ModelChoiceField(queryset=WorkerArea.objects.all(), required=True, help_text='Select the worker area.')

    class Meta:
        model = User
        # fields = ('username', 'birth_date', 'password1', 'password2', )
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'birth_date', 'work_shift', 'worker_area')


class UpdateUserForm(forms.ModelForm):
    username = forms.CharField(max_length=100, required=True,
                               widget=forms.TextInput(
                                   attrs={'class': 'form-control'}),
                               label=_('User name'))
    email = forms.EmailField(required=True,
                             widget=forms.TextInput(
                                 attrs={'class': 'form-control'}),
                             label=_('Email'))
    first_name = forms.CharField(max_length=100, required=True,
                                 widget=forms.TextInput(
                                     attrs={'class': 'form-control'}),
                                 label=_('First name'))
    last_name = forms.CharField(max_length=100, required=True,
                                widget=forms.TextInput(
                                    attrs={'class': 'form-control'}),
                                label=_('Last name'))

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']


class UpdateProfileForm(forms.ModelForm):
    identity_document = forms.CharField(max_length=15, required=False, 
                                        help_text='Optional.')
    birth_date = forms.DateField(required=False, 
                                 help_text='Required. Format: YYYY-MM-DD')
    image = forms.ImageField(widget=forms.FileInput(
        attrs={'class': 'form-control'}),
        label=_('Image'))
    bio = forms.CharField(widget=forms.Textarea(
        attrs={'class': 'form-control', 'rows': 3}),
        label=_('Bio'))
    work_shift = forms.ModelChoiceField(queryset=WorkShift.objects.all(), 
                                        required=True, help_text='Select the work shift.')
    worker_area = forms.ModelChoiceField(queryset=WorkerArea.objects.all(), 
                                         required=True, help_text='Select the worker area.')

    class Meta:
        model = Profile
        fields = ['identity_document', 'birth_date', 'image', 'bio', 'work_shift', 'worker_area']


class EmotionAnalysisForm(forms.ModelForm):

    class Meta:
        model = EmotionAnalysis
        exclude = [
            'analyzed_at', 
            'emotions_detected', 
            'created_at', 'updated_at', 'created_by', 'updated_by']

        labels = {
            'profile': _('Profile'),
            'video_file': _('Video file'),
            # 'recorded_at': _('Recording date and time')
        }

        widgets = {
            'recorded_at': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',  # HTML5 input type
                    'class': 'form-control datetimepicker',
                    'placeholder': _('Select date and time')
                }
            ),
            'video_file': forms.FileInput(
                attrs={
                    'accept': 'video/*',  # Allows only video formats
                    'class': 'form-control'
                }
            )
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['recorded_at'].widget = forms.DateTimeInput(
            format='%Y-%m-%dT%H:%M',
            attrs={'type': 'datetime-local'}
        )
        
        for field in iter(self.fields):
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })
