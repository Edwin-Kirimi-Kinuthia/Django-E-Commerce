from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.shortcuts import get_object_or_404, redirect, render

from .models import Address, UserProfile


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.email = request.POST.get('email', user.email)
        user.save()
        profile.phone = request.POST.get('phone', '')
        dob = request.POST.get('date_of_birth', '')
        profile.date_of_birth = dob or None
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'profile': profile})


@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, 'Password changed successfully.')
            return redirect('accounts:profile')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def address_add(request):
    if request.method == 'POST':
        Address.objects.create(
            user=request.user,
            address_type=request.POST.get('address_type', 'shipping'),
            full_name=request.POST.get('full_name', ''),
            address_line1=request.POST.get('address_line1', ''),
            address_line2=request.POST.get('address_line2', ''),
            city=request.POST.get('city', ''),
            state=request.POST.get('state', ''),
            postcode=request.POST.get('postcode', ''),
            country=request.POST.get('country', ''),
            is_default=bool(request.POST.get('is_default')),
        )
        messages.success(request, 'Address added.')
        return redirect('accounts:addresses')
    return render(request, 'accounts/address_form.html', {'action': 'Add'})


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.address_type = request.POST.get('address_type', address.address_type)
        address.full_name = request.POST.get('full_name', address.full_name)
        address.address_line1 = request.POST.get('address_line1', address.address_line1)
        address.address_line2 = request.POST.get('address_line2', address.address_line2)
        address.city = request.POST.get('city', address.city)
        address.state = request.POST.get('state', address.state)
        address.postcode = request.POST.get('postcode', address.postcode)
        address.country = request.POST.get('country', address.country)
        address.is_default = bool(request.POST.get('is_default'))
        address.save()
        messages.success(request, 'Address updated.')
        return redirect('accounts:addresses')
    return render(request, 'accounts/address_form.html', {'action': 'Edit', 'address': address})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address removed.')
    return redirect('accounts:addresses')
