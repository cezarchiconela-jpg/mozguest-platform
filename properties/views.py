from urllib.parse import quote

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Q, Prefetch
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .forms import PropertyForm, RoomForm, PropertyPhotoForm, MultiplePropertyPhotoForm
from .models import Property, Room, PropertyPhoto
from .services import calculate_distance_km
from .image_utils import optimize_image_field
from monetization.services import get_owner_limits


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


def normalize_phone_for_whatsapp(value):
    """Normalize common Mozambique phone formats for wa.me links without changing stored data."""
    if not value:
        return ''

    digits = ''.join(ch for ch in str(value) if ch.isdigit())

    if digits.startswith('00'):
        digits = digits[2:]

    if digits.startswith('0') and len(digits) >= 9:
        digits = digits[1:]

    if len(digits) == 9 and digits.startswith(('8', '2')):
        digits = f'258{digits}'

    return digits


def build_whatsapp_url(property_obj, message):
    phone = normalize_phone_for_whatsapp(property_obj.whatsapp or property_obj.phone)

    if not phone:
        return ''

    return f'https://wa.me/{phone}?text={quote(message)}'


def build_room_price_options(room):
    options = []
    price_fields = [
        ('hour', 'Hora', room.price_hour),
        ('day', 'Dia', room.price_day),
        ('night', 'Noite', room.price_night),
        ('month', 'Mês', room.price_month),
    ]

    for key, label, price in price_fields:
        if price:
            options.append({
                'key': key,
                'label': label,
                'price': price,
            })

    return options


def build_price_summary(rooms):
    summary = []

    for key, label, attr in [
        ('hour', 'hora', 'price_hour'),
        ('day', 'dia', 'price_day'),
        ('night', 'noite', 'price_night'),
        ('month', 'mês', 'price_month'),
    ]:
        values = [getattr(room, attr) for room in rooms if getattr(room, attr)]
        if values:
            summary.append({
                'key': key,
                'label': label,
                'min_price': min(values),
                'count': len(values),
            })

    return summary


def build_trust_badges(property_obj, rooms, reviews_count):
    photo_count = property_obj.photos.count()
    badges = []

    if property_obj.is_verified:
        badges.append({
            'label': 'Verificado pela +258 Guest',
            'description': 'Alojamento validado antes de aparecer publicamente.',
            'tone': 'emerald',
            'icon': '✓',
        })

    if property_obj.latitude and property_obj.longitude:
        badges.append({
            'label': 'Localização no mapa',
            'description': 'Tem coordenadas para facilitar rota e orientação.',
            'tone': 'blue',
            'icon': '⌖',
        })

    if photo_count >= 3:
        badges.append({
            'label': 'Galeria real',
            'description': f'{photo_count} fotografia(s) disponíveis para melhor avaliação.',
            'tone': 'slate',
            'icon': '▣',
        })

    if property_obj.whatsapp or property_obj.phone or property_obj.email:
        badges.append({
            'label': 'Contacto directo',
            'description': 'Cliente pode contactar antes ou depois do pedido.',
            'tone': 'emerald',
            'icon': '☎',
        })

    if rooms:
        badges.append({
            'label': 'Unidades disponíveis',
            'description': f'{len(rooms)} opção(ões) activas para reserva.',
            'tone': 'blue',
            'icon': '⌂',
        })

    if reviews_count:
        badges.append({
            'label': 'Avaliado por clientes',
            'description': f'{reviews_count} avaliação(ões) aprovada(s).',
            'tone': 'amber',
            'icon': '★',
        })

    return badges[:6]


def build_review_breakdown(approved_reviews, average_rating):
    reviews = list(approved_reviews)
    total = len(reviews)

    star_counts = []
    for stars in [5, 4, 3, 2, 1]:
        count = sum(1 for review in reviews if review.rating == stars)
        percentage = int((count / total) * 100) if total else 0
        star_counts.append({
            'stars': stars,
            'count': count,
            'percentage': percentage,
        })

    categories = [
        ('Limpeza', 'cleanliness_rating'),
        ('Segurança', 'security_rating'),
        ('Localização', 'location_rating'),
        ('Conforto', 'comfort_rating'),
        ('Atendimento', 'service_rating'),
        ('Preço/qualidade', 'value_rating'),
    ]

    category_ratings = []
    for label, attr in categories:
        values = [getattr(review, attr) for review in reviews if getattr(review, attr)]
        avg = round(sum(values) / len(values), 1) if values else None
        category_ratings.append({
            'label': label,
            'average': avg,
            'percentage': int((avg / 5) * 100) if avg else 0,
        })

    if not average_rating:
        score_label = 'Novo na +258 Guest'
    elif average_rating >= 4.7:
        score_label = 'Excelente'
    elif average_rating >= 4.2:
        score_label = 'Muito bom'
    elif average_rating >= 3.5:
        score_label = 'Bom'
    else:
        score_label = 'Em melhoria'

    return {
        'total': total,
        'star_counts': star_counts,
        'category_ratings': category_ratings,
        'score_label': score_label,
    }


def build_property_setup(property_obj):
    """Return a non-persistent operational checklist for the owner's property setup."""
    rooms = list(property_obj.rooms.all())
    photos = list(property_obj.photos.all())

    has_rooms = len(rooms) > 0
    has_active_room = any(room.is_available for room in rooms)
    has_price = any(
        (room.price_hour and room.price_hour > 0) or
        (room.price_day and room.price_day > 0) or
        (room.price_night and room.price_night > 0) or
        (room.price_month and room.price_month > 0)
        for room in rooms
    )
    has_photos = len(photos) >= 3
    has_main_photo = any(photo.is_main for photo in photos)
    has_location = bool(property_obj.city and (property_obj.neighbourhood or property_obj.address_reference or (property_obj.latitude and property_obj.longitude)))
    has_contact = bool(property_obj.phone or property_obj.whatsapp or property_obj.email)
    has_description = bool(property_obj.description and len(property_obj.description.strip()) >= 60)
    is_approved = property_obj.status == 'approved'

    items = [
        {
            'label': 'Dados básicos completos',
            'description': 'Nome, tipo e descrição comercial clara.',
            'done': has_description,
            'href': f'/proprietario/propriedades/{property_obj.id}/editar/',
            'action': 'Melhorar dados',
        },
        {
            'label': 'Localização preenchida',
            'description': 'Cidade, bairro/referência e, idealmente, coordenadas para o mapa.',
            'done': has_location,
            'href': f'/proprietario/propriedades/{property_obj.id}/editar/',
            'action': 'Completar localização',
        },
        {
            'label': 'Contactos de reserva',
            'description': 'Telefone, WhatsApp ou e-mail disponível para suporte ao cliente.',
            'done': has_contact,
            'href': f'/proprietario/propriedades/{property_obj.id}/editar/',
            'action': 'Completar contactos',
        },
        {
            'label': 'Quartos/unidades criados',
            'description': 'Pelo menos uma unidade disponível para reserva.',
            'done': has_rooms and has_active_room,
            'href': f'/proprietario/propriedades/{property_obj.id}/quartos/',
            'action': 'Gerir quartos',
        },
        {
            'label': 'Preços definidos',
            'description': 'Preço por hora, dia, noite ou mês para permitir reserva transparente.',
            'done': has_price,
            'href': f'/proprietario/propriedades/{property_obj.id}/quartos/',
            'action': 'Definir preços',
        },
        {
            'label': 'Galeria convincente',
            'description': 'Pelo menos 3 fotografias reais, nítidas e actualizadas.',
            'done': has_photos,
            'href': f'/proprietario/propriedades/{property_obj.id}/fotos/',
            'action': 'Adicionar fotos',
        },
        {
            'label': 'Foto principal escolhida',
            'description': 'A imagem principal é o primeiro impacto na pesquisa.',
            'done': has_main_photo,
            'href': f'/proprietario/propriedades/{property_obj.id}/fotos/',
            'action': 'Escolher principal',
        },
        {
            'label': 'Aprovação +258 Guest',
            'description': 'Validação administrativa para aparecer publicamente.',
            'done': is_approved,
            'href': '/suporte/novo/',
            'action': 'Contactar suporte',
        },
    ]

    done_count = sum(1 for item in items if item['done'])
    score = int((done_count / len(items)) * 100) if items else 0
    next_item = next((item for item in items if not item['done']), None)

    if score >= 85 and is_approved:
        readiness_label = 'Pronto para receber clientes'
        readiness_tone = 'emerald'
    elif score >= 65:
        readiness_label = 'Quase pronto'
        readiness_tone = 'blue'
    elif score >= 40:
        readiness_label = 'Precisa completar dados importantes'
        readiness_tone = 'amber'
    else:
        readiness_label = 'Configuração inicial'
        readiness_tone = 'red'

    return {
        'items': items,
        'done_count': done_count,
        'total_count': len(items),
        'score': score,
        'next_item': next_item,
        'readiness_label': readiness_label,
        'readiness_tone': readiness_tone,
        'rooms_count': len(rooms),
        'photos_count': len(photos),
        'has_price': has_price,
        'has_photos': has_photos,
        'has_location': has_location,
    }


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
        property_obj.whatsapp_url = build_whatsapp_url(
            property_obj,
            f'Olá, vi o alojamento {property_obj.name} na +258 Guest e gostaria de mais informações.'
        )
        property_obj.price_summary = build_price_summary(list(property_obj.rooms.all()))
        property_obj.trust_badges = build_trust_badges(property_obj, list(property_obj.rooms.all()), property_obj.review_count)[:3]

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

    rooms = list(property_obj.rooms.all())
    approved_reviews = property_obj.reviews.filter(status='approved')
    reviews = approved_reviews[:10]
    average_rating = approved_reviews.aggregate(avg=Avg('rating'))['avg']
    review_count = approved_reviews.count()

    for room in rooms:
        room.price_options = build_room_price_options(room)
        room.lowest_price = min([option['price'] for option in room.price_options], default=None)

    is_favorite = False
    can_review = request.user.is_authenticated
    already_reviewed = False

    if request.user.is_authenticated:
        is_favorite = property_obj.favorited_by.filter(user=request.user).exists()
        already_reviewed = property_obj.reviews.filter(user=request.user).exists()
        can_review = not already_reviewed

    whatsapp_url = build_whatsapp_url(
        property_obj,
        f'Olá, vi o alojamento {property_obj.name} na +258 Guest e gostaria de saber disponibilidade, preços e condições.'
    )

    price_summary = build_price_summary(rooms)
    trust_badges = build_trust_badges(property_obj, rooms, review_count)
    review_breakdown = build_review_breakdown(approved_reviews, average_rating)
    main_photo = get_main_photo(property_obj)
    gallery_photos = property_obj.photos.all()[:12]
    first_room = rooms[0] if rooms else None

    context = {
        'property': property_obj,
        'rooms': rooms,
        'reviews': reviews,
        'average_rating': average_rating,
        'review_count': review_count,
        'review_breakdown': review_breakdown,
        'is_favorite': is_favorite,
        'can_review': can_review,
        'already_reviewed': already_reviewed,
        'whatsapp_url': whatsapp_url,
        'price_summary': price_summary,
        'trust_badges': trust_badges,
        'main_photo': main_photo,
        'gallery_photos': gallery_photos,
        'first_room': first_room,
    }

    return render(request, 'public/property_detail.html', context)


@login_required
def owner_property_list(request):
    if not owner_required(request):
        return redirect('home')

    properties = list(Property.objects.filter(owner=request.user).prefetch_related('rooms', 'photos'))
    for property_obj in properties:
        property_obj.setup = build_property_setup(property_obj)
        property_obj.main_photo = get_main_photo(property_obj)

    total_properties = len(properties)
    ready_properties = sum(1 for property_obj in properties if property_obj.setup['score'] >= 85 and property_obj.status == 'approved')
    needs_attention = sum(1 for property_obj in properties if property_obj.setup['score'] < 65 or property_obj.status != 'approved')

    return render(request, 'owner/property_list.html', {
        'properties': properties,
        'total_properties': total_properties,
        'ready_properties': ready_properties,
        'needs_attention': needs_attention,
    })


@login_required
def owner_property_create(request):
    if not owner_required(request):
        return redirect('home')

    limits = get_owner_limits(request.user)
    current_properties = Property.objects.filter(owner=request.user).count()
    if current_properties >= limits['max_properties']:
        plan_name = limits['plan'].name if limits['plan'] else 'Gratuito'
        messages.error(
            request,
            f'O seu plano actual ({plan_name}) permite no máximo {limits["max_properties"]} propriedade(s). Solicite um plano superior para cadastrar mais alojamentos.'
        )
        return redirect('owner_property_list')

    if request.method == 'POST':
        form = PropertyForm(request.POST)

        if form.is_valid():
            property_obj = form.save(commit=False)
            property_obj.owner = request.user
            property_obj.status = 'pending'
            property_obj.save()

            messages.success(request, 'Propriedade cadastrada com sucesso. Agora complete quartos, preços e fotografias para acelerar a aprovação.')
            return redirect('owner_property_setup', property_id=property_obj.id)
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

            messages.success(request, 'Propriedade actualizada com sucesso. Revise o checklist antes da aprovação.')
            return redirect('owner_property_setup', property_id=property_obj.id)
    else:
        form = PropertyForm(instance=property_obj)

    return render(request, 'owner/property_form.html', {
        'form': form,
        'title': 'Editar propriedade'
    })


@login_required
def owner_property_setup(request, property_id):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(
        Property.objects.prefetch_related('rooms', 'photos'),
        pk=property_id,
        owner=request.user
    )
    setup = build_property_setup(property_obj)
    limits = get_owner_limits(request.user)
    main_photo = get_main_photo(property_obj)

    return render(request, 'owner/property_setup.html', {
        'property': property_obj,
        'setup': setup,
        'limits': limits,
        'main_photo': main_photo,
        'rooms': property_obj.rooms.all(),
        'photos': property_obj.photos.all()[:6],
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
            photos = request.FILES.getlist('photos')
            limits = get_owner_limits(request.user)
            existing_photos = property_obj.photos.count()

            if existing_photos + len(photos) > limits['max_photos_per_property']:
                form.add_error(
                    'photos',
                    f'O seu plano permite no máximo {limits["max_photos_per_property"]} fotografia(s) por propriedade. Remova fotos antigas ou solicite um plano superior.'
                )
            else:
                room = form.save(commit=False)
                room.property = property_obj
                room.save()

                created_photos = 0
                for image in photos:
                    photo = PropertyPhoto.objects.create(
                        property=property_obj,
                        room=room,
                        image=image,
                        caption=room.name,
                        is_main=False
                    )
                    optimize_image_field(photo.image)
                    created_photos += 1

                if created_photos and not property_obj.photos.filter(is_main=True).exists():
                    first_photo = property_obj.photos.order_by('created_at').last()
                    if first_photo:
                        first_photo.is_main = True
                        first_photo.save()

                messages.success(request, f'Quarto/unidade cadastrado com sucesso. Foram adicionadas {created_photos} fotografia(s).')
                return redirect('owner_property_setup', property_id=property_obj.id)
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
            photos = request.FILES.getlist('photos')
            limits = get_owner_limits(request.user)
            existing_photos = property_obj.photos.count()

            if existing_photos + len(photos) > limits['max_photos_per_property']:
                form.add_error(
                    'photos',
                    f'O seu plano permite no máximo {limits["max_photos_per_property"]} fotografia(s) por propriedade. Remova fotos antigas ou solicite um plano superior.'
                )
            else:
                room = form.save(commit=False)
                room.property = property_obj
                room.save()

                created_photos = 0
                for image in photos:
                    photo = PropertyPhoto.objects.create(
                        property=property_obj,
                        room=room,
                        image=image,
                        caption=room.name,
                        is_main=False
                    )
                    optimize_image_field(photo.image)
                    created_photos += 1

                if created_photos and not property_obj.photos.filter(is_main=True).exists():
                    first_photo = property_obj.photos.order_by('created_at').last()
                    if first_photo:
                        first_photo.is_main = True
                        first_photo.save()

                messages.success(request, f'Quarto/unidade actualizado com sucesso. Foram adicionadas {created_photos} nova(s) fotografia(s).')
                return redirect('owner_property_setup', property_id=property_obj.id)
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
@require_POST
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
@require_POST
def owner_room_duplicate(request, room_id):
    if not owner_required(request):
        return redirect('home')

    source_room = get_object_or_404(Room, pk=room_id, property__owner=request.user)
    duplicated_room = Room.objects.create(
        property=source_room.property,
        name=f'{source_room.name} - cópia',
        room_type=source_room.room_type,
        description=source_room.description,
        capacity=source_room.capacity,
        price_hour=source_room.price_hour,
        price_day=source_room.price_day,
        price_night=source_room.price_night,
        price_month=source_room.price_month,
        minimum_hours=source_room.minimum_hours,
        has_private_bathroom=source_room.has_private_bathroom,
        has_ac=source_room.has_ac,
        has_wifi=source_room.has_wifi,
        has_parking=source_room.has_parking,
        is_available=source_room.is_available,
        status=source_room.status,
    )

    messages.success(request, f'Unidade duplicada com sucesso. Revise o nome e os dados de "{duplicated_room.name}".')
    return redirect('owner_room_edit', room_id=duplicated_room.id)


@login_required
def owner_photo_create(request, property_id):
    if not owner_required(request):
        return redirect('home')

    property_obj = get_object_or_404(Property, pk=property_id, owner=request.user)

    if request.method == 'POST':
        form = MultiplePropertyPhotoForm(request.POST, request.FILES, property_obj=property_obj)

        if form.is_valid():
            images = form.cleaned_data['images']
            room = form.cleaned_data.get('room')
            caption = form.cleaned_data.get('caption') or property_obj.name
            set_first_as_main = form.cleaned_data.get('set_first_as_main')

            limits = get_owner_limits(request.user)
            existing_count = property_obj.photos.count()
            available_slots = limits['max_photos_per_property'] - existing_count

            if len(images) > available_slots:
                form.add_error(
                    'images',
                    f'O seu plano permite mais {available_slots} fotografia(s) nesta propriedade. Seleccione menos imagens ou solicite um plano superior.'
                )
            else:
                created_photos = []
                for index, image in enumerate(images):
                    photo = PropertyPhoto.objects.create(
                        property=property_obj,
                        room=room,
                        image=image,
                        caption=caption,
                        is_main=False,
                    )
                    optimize_image_field(photo.image)
                    created_photos.append(photo)

                if created_photos and (set_first_as_main or not property_obj.photos.filter(is_main=True).exists()):
                    PropertyPhoto.objects.filter(property=property_obj).update(is_main=False)
                    created_photos[0].is_main = True
                    created_photos[0].save()

                messages.success(request, f'{len(created_photos)} fotografia(s) adicionada(s) com sucesso.')
                return redirect('owner_property_setup', property_id=property_obj.id)
    else:
        form = MultiplePropertyPhotoForm(property_obj=property_obj)

    return render(request, 'owner/photo_form.html', {
        'form': form,
        'property': property_obj,
        'title': 'Adicionar fotografias',
        'limits': get_owner_limits(request.user),
        'current_photo_count': property_obj.photos.count(),
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
@require_POST
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
@require_POST
def owner_photo_delete(request, photo_id):
    if not owner_required(request):
        return redirect('home')

    photo = get_object_or_404(PropertyPhoto, pk=photo_id, property__owner=request.user)
    property_id = photo.property.id
    photo.delete()

    messages.success(request, 'Fotografia apagada com sucesso.')
    return redirect('owner_photo_gallery', property_id=property_id)
