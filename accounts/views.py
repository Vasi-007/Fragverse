from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Profile
from .forms import EmailOrUsernameAuthenticationForm, ProfileForm, RegisterForm


def register(request):
    """Handle user registration with enhanced form"""
    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.save()
        # Show success message
        messages.success(request, f'Account created successfully! Please log in.')
        return redirect("login")

    context = {"form": form}
    return render(request, "register.html", context)


def login_view(request):
    """Handle login with email or username support"""
    form = EmailOrUsernameAuthenticationForm(request, data=request.POST or None)
    error_message = None

    if request.method == "POST":
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = None

        # Try to authenticate with username first
        user = authenticate(request, username=username_or_email, password=password)

        # If username doesn't work, try email
        if user is None and '@' in username_or_email:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            login(request, user)
            # Show welcome message
            messages.success(
                request,
                f'Welcome back, {user.first_name or user.username}! 👋',
                extra_tags='welcome'
            )
            return redirect("home")
        else:
            error_message = "Invalid username/email or password."

    context = {
        "form": form,
        "error": error_message,
    }

    return render(request, "login.html", context)


def logout_user(request):
    """Handle user logout"""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect("home")


@login_required(login_url="login")
def profile(request):
    """Display user profile"""
    profile = Profile.objects.get(user=request.user)
    context = {"profile": profile}
    return render(request, "profile.html", context)


@login_required(login_url="login")
def edit_profile(request):
    """Edit user profile"""
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileForm(
            request.POST,
            request.FILES,
            instance=profile
        )

        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect("checkout")

    else:
        form = ProfileForm(instance=profile)

    context = {"form": form}
    return render(request, "edit_profile.html", context)

