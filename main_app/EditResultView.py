from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Subject, Staff, Student, StudentResult, MarksCorrectionLog
from .forms import EditResultForm
from django.urls import reverse


class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        staff = get_object_or_404(Staff, admin=request.user)
        resultForm.fields['subject'].queryset = Subject.objects.filter(staff=staff)
        context = {
            'form': resultForm,
            'page_title': "Edit Student's Result"
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                test = form.cleaned_data.get('test')
                exam = form.cleaned_data.get('exam')
                # Validating
                result = StudentResult.objects.get(student=student, subject=subject)

                # Check if finalized - block edits for non-admin staff
                if result.is_finalized and not (request.user.is_superuser or str(getattr(request.user, 'user_type', '')) in ['1', '4']):
                    messages.error(request, "Marks for this subject have been finalized and locked. Edits are blocked.")
                    return redirect(reverse('edit_student_result'))

                prev_test = result.test
                prev_exam = result.exam

                result.exam = exam
                result.test = test
                result.save()

                # Audit log for marks correction
                MarksCorrectionLog.objects.create(
                    result=result,
                    changed_by=request.user if request.user.is_authenticated else None,
                    previous_test=prev_test,
                    new_test=result.test,
                    previous_exam=prev_exam,
                    new_exam=result.exam,
                    previous_assignment=result.assignment,
                    new_assignment=result.assignment,
                    previous_practical=result.practical,
                    new_practical=result.practical,
                    reason=request.POST.get('reason', 'Updated via Edit Result form')
                )

                messages.success(request, "Result Updated with audit log")
                return redirect(reverse('edit_student_result'))
            except Exception as e:
                messages.warning(request, f"Result Could Not Be Updated: {e}")
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "staff_template/edit_student_result.html", context)
