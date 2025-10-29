from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

def role_required(*roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role in roles:
                return view_func(request, *args, **kwargs)
            return redirect("accounts:login")
        return wrapper
    return decorator
