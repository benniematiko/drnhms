from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout  # ✅ Add logout here

from .forms import CustomUserCreationForm
from django.contrib.auth.views import LoginView


# Registration
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # auto-login after registration
            return redirect('patients')  # redirect to patients page
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})


# Login using built-in view
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'





# logoout
def logout_view(request):

    logout(request)
    return redirect('login')

