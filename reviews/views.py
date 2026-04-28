from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from properties.models import Property
from .forms import ReviewForm
from .models import Review


@login_required
def create_review(request, property_id):
    property_obj = get_object_or_404(Property, pk=property_id, status='approved')

    existing_review = Review.objects.filter(
        property=property_obj,
        user=request.user
    ).first()

    if existing_review:
        messages.error(request, 'Já submeteu uma avaliação para este alojamento.')
        return redirect('property_detail', pk=property_obj.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)

        if form.is_valid():
            review = form.save(commit=False)
            review.property = property_obj
            review.user = request.user
            review.status = 'pending'
            review.save()

            messages.success(request, 'Avaliação submetida com sucesso. Aguarda aprovação da MozGuest.')
            return redirect('property_detail', pk=property_obj.id)
    else:
        initial_name = request.user.get_full_name() or request.user.username
        form = ReviewForm(initial={'customer_name': initial_name})

    return render(request, 'reviews/review_form.html', {
        'form': form,
        'property': property_obj,
    })


@login_required
def favorite_toggle(request, property_id):
    from .models import Favorite

    property_obj = get_object_or_404(Property, pk=property_id, status='approved')

    favorite = Favorite.objects.filter(
        user=request.user,
        property=property_obj
    ).first()

    if favorite:
        favorite.delete()
        messages.success(request, 'Alojamento removido dos favoritos.')
    else:
        Favorite.objects.create(
            user=request.user,
            property=property_obj
        )
        messages.success(request, 'Alojamento adicionado aos favoritos.')

    return redirect('property_detail', pk=property_obj.id)


@login_required
def favorite_list(request):
    from .models import Favorite

    favorites = Favorite.objects.filter(user=request.user).select_related('property')

    return render(request, 'reviews/favorite_list.html', {
        'favorites': favorites
    })
