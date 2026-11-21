from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def role_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []
    # normalize roles to strings
    allowed_roles = [str(r) for r in allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(reverse('login_page'))
            user_type = str(getattr(request.user, 'user_type', ''))
            if user_type in allowed_roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You do not have permission to access this resource.")
            # redirect to their respective home
            if user_type == '1':
                return redirect(reverse('admin_home'))
            elif user_type == '2':
                return redirect(reverse('staff_home'))
            elif user_type == '3':
                return redirect(reverse('student_home'))
            elif user_type == '4':
                return redirect(reverse('principal_home'))
            elif user_type == '5':
                return redirect(reverse('finance_home'))
            elif user_type == '7':
                return redirect(reverse('accreditation_home'))
            elif user_type == '8':
                return redirect(reverse('registrar_home'))
            elif user_type == '6':
                return redirect(reverse('admin_home'))
            return redirect(reverse('login_page'))
        return wrapper
    return decorator


def admin_required(view_func):
    return role_required(['1'])(view_func)


def principal_required(view_func):
    return role_required(['4'])(view_func)


def staff_required(view_func):
    return role_required(['2'])(view_func)


def student_required(view_func):
    return role_required(['3'])(view_func)


def finance_required(view_func):
    return role_required(['5', '4'])(view_func)


def hr_required(view_func):
    return role_required(['6', '4'])(view_func)


def accreditation_required(view_func):
    return role_required(['7', '4'])(view_func)


def registrar_required(view_func):
    return role_required(['8', '4'])(view_func)
