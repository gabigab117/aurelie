from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.mixins import UserPassesTestMixin, PermissionRequiredMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView, DeleteView

from apps.account.models import UserRole

User = get_user_model()


class UserListView(PermissionRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    paginate_by = 10
    ordering = ['-date_joined']
    queryset = User.objects.prefetch_related("companies").all()
    permission_required = "account.view_user"

    def test_func(self):
        return self.request.user.is_staff


class UserCreateView(PermissionRequiredMixin, UserPassesTestMixin, CreateView):
    model = User
    fields = ("username", "email", "is_staff", "companies",)
    success_url = reverse_lazy("management:user:list")
    permission_required = "account.add_user"

    def test_func(self):
        return self.request.user.is_staff

    def form_valid(self, form):
        self.object = form.save()

        # Send password reset email to new user so they can set their password
        password_reset = PasswordResetForm(data={"email": self.object.email})
        if password_reset.is_valid():
            password_reset.save(request=self.request)

        # Add default permission group to the user
        self.object.groups.add(Group.objects.get(name=UserRole.EMPLOYEE))

        if self.object.is_staff:
            # If user is manager, add specific permission group
            self.object.groups.add(Group.objects.get(name=UserRole.MANAGER))

        return redirect(self.get_success_url())


class UserUpdateView(PermissionRequiredMixin, UserPassesTestMixin, UpdateView):
    model = User
    fields = ("username", "email", "is_staff", "is_active", "companies",)
    success_url = reverse_lazy("management:user:list")
    permission_required = "account.change_user"

    def test_func(self):
        return self.request.user.is_staff


class UserDeleteView(PermissionRequiredMixin, UserPassesTestMixin, DeleteView):
    model = User
    success_url = reverse_lazy("management:user:list")
    permission_required = "account.delete_user"

    def test_func(self):
        return self.request.user.is_staff
