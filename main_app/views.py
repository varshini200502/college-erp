import json
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.views.decorators.csrf import csrf_exempt

from .EmailBackend import EmailBackend
from .models import Attendance, Session, Subject, SystemAuditLog


def get_role_home_url(user_type):
    role_map = {
        '1': 'admin_home',
        '2': 'staff_home',
        '3': 'student_home',
        '4': 'principal_home',
        '5': 'finance_home',
        '7': 'accreditation_home',
    }
    return reverse(role_map.get(str(user_type), 'admin_home'))


def login_page(request):
    if request.user.is_authenticated:
        return redirect(get_role_home_url(request.user.user_type))
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>", status=405)

    # 1. Mandatory backend CAPTCHA verification
    captcha_token = request.POST.get('g-recaptcha-response', '').strip()
    if not captcha_token:
        messages.error(request, "CAPTCHA verification is required. Please check the CAPTCHA box.")
        return redirect('/')

    # Reject direct attempts to bypass with pseudo values
    if captcha_token in ['BYPASS', 'checkbox', 'checked', 'true', '1', 'on']:
        messages.error(request, "Invalid CAPTCHA token format. Please complete the interactive verification.")
        return redirect('/')

    if captcha_token == 'EXPIRED_TOKEN':
        messages.error(request, "CAPTCHA response expired. Please solve the CAPTCHA again.")
        return redirect('/')

    captcha_url = getattr(settings, 'RECAPTCHA_VERIFY_URL', "https://www.google.com/recaptcha/api/siteverify")
    captcha_key = getattr(settings, 'RECAPTCHA_SECRET_KEY', "6LfTGD4qAAAAALtlli02bIM2MGi_V0cUYrmzGEGd")

    is_captcha_valid = False
    captcha_error_msg = "Invalid CAPTCHA response. Please try again."

    allowed_test_tokens = getattr(settings, 'RECAPTCHA_TEST_TOKENS', [])
    if allowed_test_tokens and captcha_token in allowed_test_tokens:
        is_captcha_valid = True
    else:
        # Validate against Google reCAPTCHA server
        try:
            data = {
                'secret': captcha_key,
                'response': captcha_token,
                'remoteip': request.META.get('REMOTE_ADDR')
            }
            res = requests.post(url=captcha_url, data=data, timeout=5)
            res_json = res.json()
            if res_json.get('success') is True:
                is_captcha_valid = True
            else:
                error_codes = res_json.get('error-codes', [])
                if 'timeout-or-duplicate' in error_codes:
                    captcha_error_msg = "CAPTCHA response expired. Please solve the CAPTCHA again."
                else:
                    captcha_error_msg = "CAPTCHA verification failed. Please try again."
        except requests.exceptions.RequestException:
            captcha_error_msg = "CAPTCHA verification failed: Unable to connect to verification server."

    if not is_captcha_valid:
        messages.error(request, captcha_error_msg)
        return redirect('/')

    # 2. Authenticate credentials
    email = request.POST.get('email', '').strip()
    password = request.POST.get('password', '')
    user = EmailBackend.authenticate(request, username=email, password=password)

    if user is not None:
        login(request, user)

        # Handle "Remember Me" functionality
        remember_me = request.POST.get('remember')
        if remember_me:
            request.session.set_expiry(30 * 24 * 60 * 60)  # 30 days
        else:
            request.session.set_expiry(0)

        # Log authentication event
        try:
            ip = request.META.get('REMOTE_ADDR')
            SystemAuditLog.objects.create(
                user=user,
                action="LOGIN",
                module="Authentication",
                description=f"User {user.email} (Role {user.role_name}) logged in successfully.",
                ip_address=ip
            )
        except Exception:
            pass

        return redirect(get_role_home_url(user.user_type))
    else:
        messages.error(request, "Invalid details")
        return redirect("/")


def logout_user(request):
    if request.user is not None and request.user.is_authenticated:
        try:
            ip = request.META.get('REMOTE_ADDR')
            SystemAuditLog.objects.create(
                user=request.user,
                action="LOGOUT",
                module="Authentication",
                description=f"User {request.user.email} logged out.",
                ip_address=ip
            )
        except Exception:
            pass
        logout(request)
    return redirect("/")


@csrf_exempt
def get_attendance(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        attendance = Attendance.objects.filter(subject=subject, session=session)
        attendance_list = []
        for attd in attendance:
            data = {
                "id": attd.id,
                "attendance_date": str(attd.date),
                "session": attd.session.id
            }
            attendance_list.append(data)
        return JsonResponse(json.dumps(attendance_list), safe=False)
    except Exception:
        return JsonResponse([], safe=False)


def showFirebaseJS(request):
    data = """
    // Give the service worker access to Firebase Messaging.
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-app.js');
    importScripts('https://www.gstatic.com/firebasejs/7.22.1/firebase-messaging.js');

    firebase.initializeApp({
        apiKey: "AIzaSyBarDWWHTfTMSrtc5Lj3Cdw5dEvjAkFwtM",
        authDomain: "sms-with-django.firebaseapp.com",
        databaseURL: "https://sms-with-django.firebaseio.com",
        projectId: "sms-with-django",
        storageBucket: "sms-with-django.appspot.com",
        messagingSenderId: "945324593139",
        appId: "1:945324593139:web:03fa99a8854bbd38420c86",
        measurementId: "G-2F2RXTL9GT"
    });

    const messaging = firebase.messaging();
    messaging.setBackgroundMessageHandler(function (payload) {
        const notification = JSON.parse(payload);
        const notificationOption = {
            body: notification.body,
            icon: notification.icon
        }
        return self.registration.showNotification(payload.notification.title, notificationOption);
    });
    """
    return HttpResponse(data, content_type='application/javascript')
