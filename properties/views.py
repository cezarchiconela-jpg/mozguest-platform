from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Prefetch
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PropertyForm, RoomForm, PropertyPhotoForm
from .models import Property, Room, PropertyPhoto
from .services import calculate_distance_km
from .image_utils import optimize_image_field


def is_owner_user(user):
    return user.is_authenticated and hasattr(user, 'owner_profile')


def owner_required(request):
    if not is_owner_user(request.user):
        messages.error(request, 'Apenas proprietários podem aceder a esta área.')
        return False
    return True


def get_min_price(property_obj):
    prices = []

    for room in property_obj.rooms.all():
        if not room.is_available:
            continue

        if room.price_hour:
            prices.append(room.price_hour)

        if room.price_day:
            prices.append(room.price_day)

        if room.price_night:
            prices.append(room.price_night)

        if room.price_month:
            prices.append(room.price_month)

    if prices:
        return min(prices)

    return None


def get_main_photo(property_obj):
    main_photo = property_obj.photos.filter(is_main=True).first()

    if main_photo:
        return main_photo

    return property_obj.photos.first()


def property_list(request):
    properties = Property.objects.filter(status='approved').prefetch_related(
        'photos',
        'reviews',
        Prefetch('rooms', queryset=Room.objects.filter(is_available=True))
    )

    query = request.GET.get('q')
    property_type = request.GET.get('type')
    max_price = request.GET.get('max_price')
    min_price = request.GET.get('min_price')
    price_mode = request.GET.get('price_mode')
    verified = request.GET.get('verified')
    has_wifi = request.GET.get('wifi')
    has_ac = request.GET.get('ac')
    has_parking = request.GET.get('parking')
    private_bathroom = request.GET.get('private_bathroom')
    radius = request.GET.get('radius')
    sort = request.GET.get('sort', 'recent')

    user_lat = request.GET.get('lat')
    user_lng = request.GET.get('lng')

    if query:
        properties = properties.filter(
            Q(name__icontains=query) |
            Q(city__icontains=query) |
            Q(neighbourhood__icontains=query) |
            Q(district__icontains=query) |
            Q(province__icontains=query) |
            Q(description__icontains=query)
        )

    if property_type:
        properties = properties.filter(property_type=property_type)

    if verified == '1':
        properties = properties.filter(is_verified=True)

    if has_wifi == '1':
        properties = properties.filter(rooms__has_wifi=True)

    if has_ac == '1':
        properties = properties.filter(rooms__has_ac=True)

    if has_parking == '1':
        properties = properties.filter(rooms__has_parking=True)

    if private_bathroom == '1':
        properties = properties.filter(rooms__has_private_bathroom=True)

    if min_price:
        if price_mode == 'hour':
            properties = properties.filter(rooms__price_hour__gte=min_price)
        elif price_mode == 'day':
            properties = properties.filter(rooms__price_day__gte=min_price)
        elif price_mode == 'night':
            properties = properties.filter(rooms__price_night__gte=min_price)
        elif price_mode == 'month':
            properties = properties.filter(rooms__price_month__gte=min_price)
        else:
            properties = properties.filter(
                Q(rooms__price_hour__gte=min_price) |
                Q(rooms__price_day__gte=min_price) |
                Q(rooms__price_night__gte=min_price) |
                Q(rooms__price_month__gte=min_price)
            )

    if max_price:
        if price_mode == 'hour':
            properties = properties.filter(rooms__price_hour__lte=max_price)
        elif price_mode == 'day':
            properties = properties.filter(rooms__price_day__lte=max_price)
        elif price_mode == 'night':
            properties = properties.filter(rooms__price_night__lte=max_price)
        elif price_mode == 'month':
            properties = properties.filter(rooms__price_month__lte=max_price)
        else:
            properties = properties.filter(
                Q(rooms__price_hour__lte=max_price) |
                Q(rooms__price_day__lte=max_price) |
                Q(rooms__price_night__lte=max_price) |
                Q(rooms__price_month__lte=max_price)
            )

    properties = properties.distinct()

    property_items = []

    for property_obj in properties:
        distance = calculate_distance_km(
            user_lat,
            user_lng,
            property_obj.latitude,
            property_obj.longitude
        )

        property_obj.distance_km = distance

        if radius and user_lat and user_lng:
            try:
                radius_value = float(radius)
                if distance is None or distance > radius_value:
                    continue
            except ValueError:
                pass

        approved_reviews = property_obj.reviews.filter(status='approved')
        property_obj.average_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg']
        property_obj.review_count = approved_reviews.count()
        property_obj.min_price = get_min_price(property_obj)
        property_obj.available_rooms_count = property_obj.rooms.count()
        property_obj.main_photo = get_main_photo(property_obj)

        property_items.append(property_obj)

    if sort == 'distance' and user_lat and user_lng:
        property_items.sort(
            key=lambda item: item.distance_km if item.distance_km is not None else 999999
        )
    elif sort == 'price':
        property_items.sort(
            key=lambda item: item.min_price if item.min_price is not None else 999999
        )
    elif sort == 'rating':
        property_items.sort(
            key=lambda item: item.average_rating if item.average_rating is not None else 0,
            reverse=True
        )
    elif sort == 'featured':
        property_items.sort(
            key=lambda item: (item.is_featured, item.is_verified, item.created_at),
            reverse=True
        )
    else:
        property_items.sort(
            key=lambda item: item.created_at,
            reverse=True
        )

    context = {
        'properties': property_items,
        'query': query,
        'property_type': property_type,
        'min_price': min_price,
        'max_price': max_price,
        'price_mode': price_mode,
        'verified': verified,
        'has_wifi': has_wifi,
        'has_ac': has_ac,
        'has_parking': has_parking,
        'private_bathroom': private_bathroom,
        'radius': radius,
        'sort': sort,
        'user_lat': user_lat,
        'user_lng': user_lng,
    }

    return render(request, 'public/property_list.html', context)


def property_detail(request, pk):
    property_obj = get_object_or_404(
        Property.objects.prefetch_related(
            'photos',
            'reviews',
            Prefetch('rooms', queryset=Room.objects.filter(is_available=True).prefetch_related('photos'))
        ),
        pk=pk,
        status='approved'
    )

    rooms = property_obj.rooms.all()
    reviews = property_obj.reviews.filter(status='approved')[:10]
    average_rating = property_obj.reviews.filter(status='approved').aggregate(avg=Avg('rating'))['avg']
    review_count = property_obj.reviews.filter(status='approved').count()

    is_favorite = False

    if request.user.is_authenticated:
        is_favorite = property_obj.favorited_by.filter(user=request.user).exists()

    context = {
        'property': property_obj,
        'rooms': rooms,
        'reviews': reviews,
        'average_rating': average_rating,
        'review_count': review_count,
        'is_favorite': is_favorite,
    }

    return render(request, 'public/property_detail.html', context)


@login_required
def owner_property_list(request):
    if not owner_required(request):
        return redirect('home')

    properties = Property.objects.filter(owner=request.user).prefetch_related('rooms', 'photos')

    return render(request, 'owner/property_list.html', {
        'properties': properties
    })


@login_required
def owner_property_create(request):
    if not owner_required(request):
        return redirect('home')

    if request.method == 'POST':
        form = PropertyForm(request.POST)

        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.status = 'pending'
            property_obj.save()

            messages.success(request, 'Propriedade cadastrada com sucesso. Aguarda aprovação da administração.')
            return redirect('owner_property_list')
    else:
        form = PropertyForm()

    return render(request, 'owner/property_form.html', {
        'form': form,
        'title': 'Cadastrar nova propriedade'
    })


@login_required
def owner_property_edit(request, pk):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=pk, owner=request.user)

    if request.method == 'POST':
        form = PropertyForm(request.POST, instance=property_obj)

        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.status = 'pending'
            property_obj.save()

            messages.success(request, 'Propriedade actualizada com sucesso. Aguarda nova aprovação.')
            return redirect('owner_property_list')
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'owner/property_form.html', {
        'form': form,
        'title': 'Editar propriedade'
    })


@login_required
def owner_room_list(request, property_id):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)
    rooms = property_obj.rooms.prefetch_related('photos').all()

    return render(request, 'owner/room_list.html', {
        'property': property_obj,
        'rooms': rooms,
    })


@login_required
def owner_room_create(request, property_id):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES)
        form.fields['property'].queryset = Property.objects.filter(owner=request.user)

        if form.is_valid():
            room = form.save(commit=False)
            room.property = property_obj
            room.save()

            photos = request.FILES.getlist('photos')

            for image in photos:
                photo = PropertyPhoto.objects.create(
                    property=property_obj,
                    room=room,
                    image=image,
                    caption=room.name,
                    is_main=False
                )
                optimize_image_field(photo.image)

            messages.success(request, f'Quarto/unidade cadastrado com sucesso. Foram adicionadas {len(photos)} fotografia(s).')
            return redirect('owner_room_list', property_id=property_obj.id)
    else:
        form = RoomForm(initial={'property': property_obj})
        form.fields['property'].queryset = Property.objects.filter(owner=request.user)

    return render(request, 'owner/room_form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Cadastrar quarto/unidade',
        'room': None,
        'room_photos': [],
    })


@login_required
def owner_room_edit(request, room_id):
    if not owner_required(request):
        return redirect('home')

    room = get_object_or_404(Room, pk=room_id, property__owner=request.user)
    property_obj = room.property

    if request.method == 'POST':
        form = RoomForm(request.POST, request.FILES, instance=room)
        form.fields['property'].queryset = Property.objects.filter(owner=request.user)

        if form.is_valid():
            room = form.save(commit=False)
            room.property = property_obj
            room.save()

            photos = request.FILES.getlist('photos')

            for image in photos:
                photo = PropertyPhoto.objects.create(
                    property=property_obj,
                    room=room,
                    image=image,
                    caption=room.name,
                    is_main=False
                )
                optimize_image_field(photo.image)

            messages.success(request, f'Quarto/unidade actualizado com sucesso. Foram adicionadas {len(photos)} nova(s) fotografia(s).')
            return redirect('owner_room_list', property_id=property_obj.id)
    else:
        form = RoomForm(instance=room)
        form.fields['property'].queryset = Property.objects.filter(owner=request.user)

    room_photos = PropertyPhoto.objects.filter(room=room)

    return render(request, 'owner/room_form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Editar quarto/unidade',
        'room': room,
        'room_photos': room_photos,
    })


@login_required
def owner_room_toggle(request, room_id):
    if not owner_required(request):
        return redirect('home')

    room = get_object_or_404(Room, pk=room_id, property__owner=request.user)
    room.is_available = not room.is_available
    room.save()

    if room.is_available:
        messages.success(request, 'Quarto/unidade activado com sucesso.')
    else:
        messages.success(request, 'Quarto/unidade desactivado com sucesso.')

    return redirect('owner_room_list', property_id=room.property.id)


@login_required
def owner_photo_create(request, property_id):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)

    if request.method == 'POST':
        form = PropertyPhotoForm(request.POST, request.FILES)
        form.fields['property'].queryset = Property.objects.filter(owner=request.user)
        form.fields['room'].queryset = property_obj.rooms.all()

        if form.is_valid():
            photo = form.save(commit=False)
            photo.property = property_obj
            photo.save()

            if photo.is_main:
                PropertyPhoto.objects.filter(property=photo.property).exclude(id=photo.id).update(is_main=False)

            optimize_image_field(photo.image)

            messages.success(request, 'Fotografia adicionada com sucesso.')
            return redirect('owner_photo_gallery', property_id=property_obj.id)
    else:
        form = PropertyPhotoForm(initial={'property': property_obj})
        form.fields['property'].queryset = Property.objects.filter(owner=request.user)
        form.fields['room'].queryset = property_obj.rooms.all()

    return render(request, 'owner/photo_form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Adicionar fotografia'
    })


@login_required
def owner_photo_gallery(request, property_id):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)
    photos = property_obj.photos.select_related('room').all()

    return render(request, 'owner/photo_gallery.html', {
        'property': property_obj,
        'photos': photos,
    })


@login_required
def owner_photo_set_main(request, photo_id):
    if not owner_required(request):
        return redirect('home')

    photo = get_object_or_404(PropertyPhoto, pk=photo_id, property__owner=request.user)

    PropertyPhoto.objects.filter(property=photo.property).update(is_main=False)

    photo.is_main = True
    photo.save()

    messages.success(request, 'Foto principal definida com sucesso.')
    return redirect('owner_photo_gallery', property_id=photo.property.id)


@login_required
def owner_photo_delete(request, photo_id):
    if not owner_required(request):
        return redirect('home')

    photo = get_object_or_404(PropertyPhoto, pk=photo_id, property__owner=request.user)
    property_id = photo.property.id
    photo.delete()

    messages.success(request, 'Fotografia apagada com sucesso.')
    return redirect('owner_photo_gallery', property_id=property_id)
