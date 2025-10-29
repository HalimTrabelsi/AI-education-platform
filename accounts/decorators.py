from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages

def role_required(*roles):
 
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                messages.warning(request, "Please log in first.")
                return redirect('accounts:login')
            if hasattr(user, 'role') and user.role in roles:
                return view_func(request, *args, **kwargs)
            messages.error(request, "You are not authorized to access this page.")
            return redirect('index')
        return _wrapped_view
    return decorator
