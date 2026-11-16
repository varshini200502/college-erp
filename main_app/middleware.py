from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.shortcuts import redirect
from django.db.utils import OperationalError, ProgrammingError


class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        auth_allowed_paths = {
            reverse('login_page'),
            reverse('user_login'),
            reverse('user_logout'),
        }

        try:
            user = request.user
            user_type = str(getattr(user, 'user_type', ''))
        except (OperationalError, ProgrammingError):
            if (
                request.path in auth_allowed_paths
                or modulename.startswith('django.contrib.auth')
                or request.path.startswith('/admin/')
            ):
                return None
            return redirect(reverse('login_page'))

        if user.is_authenticated:
            # Check user role and restrict access to unauthorized module endpoints
            # Admin (1) & Principal (4) have broad administrative access
            if user_type in ['1', '4']:
                if modulename == 'main_app.student_views':
                    target = 'principal_home' if user_type == '4' else 'admin_home'
                    return redirect(reverse(target))
            elif user_type == '2':  # Staff / Faculty
                if modulename in ['main_app.student_views', 'main_app.hod_views', 'main_app.principal_views', 'main_app.finance_views', 'main_app.hr_views']:
                    return redirect(reverse('staff_home'))
            elif user_type == '3':  # Student
                # Allow student to download their own fee receipt
                if request.path.startswith('/finance/receipt/'):
                    return None
                if modulename in ['main_app.hod_views', 'main_app.staff_views', 'main_app.principal_views', 'main_app.finance_views', 'main_app.hr_views', 'main_app.accreditation_views']:
                    return redirect(reverse('student_home'))
            elif user_type == '5':  # Finance
                if modulename in ['main_app.student_views', 'main_app.staff_views', 'main_app.hr_views']:
                    return redirect(reverse('finance_home'))
            elif user_type == '7':  # Accreditation
                if modulename in ['main_app.student_views', 'main_app.staff_views', 'main_app.finance_views', 'main_app.hr_views']:
                    return redirect(reverse('accreditation_home'))
            elif user_type == '6':  # Deprecated HR role
                return redirect(reverse('login_page'))
        else:
            if (
                request.path in auth_allowed_paths
                or modulename == 'django.contrib.auth.views'
                or request.path.startswith('/admin/')
                or request.path.startswith('/static/')
                or request.path.startswith('/media/')
                or request.path == reverse('showFirebaseJS')
            ):
                return None
            else:
                return redirect(reverse('login_page'))
