from django import forms
from django.forms.widgets import DateInput, TextInput

from .models import *
from . import models


class FormSettings(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(FormSettings, self).__init__(*args, **kwargs)
        # Here make some changes such as:
        for field in self.visible_fields():
            field.field.widget.attrs['class'] = 'form-control'


class CustomUserForm(FormSettings):
    email = forms.EmailField(required=True)
    gender = forms.ChoiceField(choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea, required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput(),
    }
    profile_pic = forms.ImageField(required=False)

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)

        if kwargs.get('instance'):
            instance = kwargs.get('instance').admin.__dict__
            self.fields['password'].required = False
            for field in CustomUserForm.Meta.fields:
                self.fields[field].initial = instance.get(field)
            if self.instance.pk is not None:
                self.fields['password'].widget.attrs['placeholder'] = "Fill this only if you wish to update password"

    def clean_email(self, *args, **kwargs):
        formEmail = self.cleaned_data['email'].lower()
        if self.instance.pk is None:  # Insert
            if CustomUser.objects.filter(email=formEmail).exists():
                raise forms.ValidationError(
                    "The given email is already registered")
        else:  # Update
            dbEmail = self.Meta.model.objects.get(
                id=self.instance.pk).admin.email.lower()
            if dbEmail != formEmail:  # There has been changes
                if CustomUser.objects.filter(email=formEmail).exists():
                    raise forms.ValidationError("The given email is already registered")

        return formEmail

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'gender',  'password','profile_pic', 'address' ]


class StudentForm(CustomUserForm):
    roll_number = forms.CharField(required=False)
    admission_number = forms.CharField(required=False)
    date_of_birth = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    phone = forms.CharField(required=False)
    parent_name = forms.CharField(required=False)
    parent_phone = forms.CharField(required=False)
    current_semester = forms.IntegerField(min_value=1, max_value=8, initial=1, required=False)
    section = forms.CharField(initial="A", required=False)
    status = forms.ChoiceField(choices=Student.STATUS_CHOICES, initial="Active", required=False)

    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            st = kwargs.get('instance')
            self.fields['roll_number'].initial = st.roll_number
            self.fields['admission_number'].initial = st.admission_number
            self.fields['date_of_birth'].initial = st.date_of_birth
            self.fields['phone'].initial = st.phone
            self.fields['parent_name'].initial = st.parent_name
            self.fields['parent_phone'].initial = st.parent_phone
            self.fields['current_semester'].initial = st.current_semester
            self.fields['section'].initial = st.section
            self.fields['status'].initial = st.status

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields + [
            'course', 'session', 'roll_number', 'admission_number',
            'date_of_birth', 'phone', 'parent_name', 'parent_phone',
            'current_semester', 'section', 'status'
        ]


class AdminForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(AdminForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Admin
        fields = CustomUserForm.Meta.fields


class StaffForm(CustomUserForm):
    faculty_id = forms.CharField(required=False)
    designation = forms.CharField(initial="Assistant Professor", required=False)
    department = forms.CharField(required=False)
    date_of_joining = forms.DateField(widget=DateInput(attrs={'type': 'date'}), required=False)
    employment_status = forms.ChoiceField(choices=Staff.EMPLOYMENT_STATUS, initial="Active", required=False)
    total_experience_years = forms.FloatField(initial=0.0, required=False)
    highest_qualification = forms.CharField(required=False)
    specialization = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        super(StaffForm, self).__init__(*args, **kwargs)
        if kwargs.get('instance'):
            sf = kwargs.get('instance')
            self.fields['faculty_id'].initial = sf.faculty_id
            self.fields['designation'].initial = sf.designation
            self.fields['department'].initial = sf.department or (sf.course.name if sf.course else "")
            self.fields['date_of_joining'].initial = sf.date_of_joining
            self.fields['employment_status'].initial = sf.employment_status
            self.fields['total_experience_years'].initial = sf.total_experience_years
            self.fields['highest_qualification'].initial = sf.highest_qualification
            self.fields['specialization'].initial = sf.specialization

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields + [
            'course', 'faculty_id', 'designation', 'department',
            'date_of_joining', 'employment_status', 'total_experience_years',
            'highest_qualification', 'specialization'
        ]


class CourseForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)

    class Meta:
        fields = ['name']
        model = Course


class SubjectForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(SubjectForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Subject
        fields = ['name', 'staff', 'course']


class SessionForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(SessionForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Session
        fields = '__all__'
        widgets = {
            'start_year': DateInput(attrs={'type': 'date'}),
            'end_year': DateInput(attrs={'type': 'date'}),
        }


class LeaveReportStaffForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStaff
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStaffForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStaffForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStaff
        fields = ['feedback']


class LeaveReportStudentForm(FormSettings):
    def __init__(self, *args, **kwargs):
        super(LeaveReportStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaveReportStudent
        fields = ['date', 'message']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class FeedbackStudentForm(FormSettings):

    def __init__(self, *args, **kwargs):
        super(FeedbackStudentForm, self).__init__(*args, **kwargs)

    class Meta:
        model = FeedbackStudent
        fields = ['feedback']


class StudentEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StudentEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Student
        fields = CustomUserForm.Meta.fields 


class StaffEditForm(CustomUserForm):
    def __init__(self, *args, **kwargs):
        super(StaffEditForm, self).__init__(*args, **kwargs)

    class Meta(CustomUserForm.Meta):
        model = Staff
        fields = CustomUserForm.Meta.fields


class EditResultForm(FormSettings):
    session_list = Session.objects.all()
    session_year = forms.ModelChoiceField(
        label="Session Year", queryset=session_list, required=True)

    def __init__(self, *args, **kwargs):
        super(EditResultForm, self).__init__(*args, **kwargs)

    class Meta:
        model = StudentResult
        fields = ['session_year', 'subject', 'student', 'test', 'exam']

#todos
# class TodoForm(forms.ModelForm):
#     class Meta:
#         model=Todo
#         fields=["title","is_finished"]

#issue book

class IssueBookForm(forms.Form):
    isbn2 = forms.ModelChoiceField(queryset=models.Book.objects.all(), empty_label="Book Name [ISBN]", to_field_name="isbn", label="Book (Name and ISBN)")
    name2 = forms.ModelChoiceField(queryset=models.Student.objects.all(), empty_label="Name ", to_field_name="", label="Student Details")
    
    isbn2.widget.attrs.update({'class': 'form-control'})
    name2.widget.attrs.update({'class':'form-control'})
