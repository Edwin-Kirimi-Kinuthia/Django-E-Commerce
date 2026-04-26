from decimal import Decimal, InvalidOperation

from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.db.models import Avg, Count, Q
from django.shortcuts import render

from shop.models import Category, Product


def searchResult(request):
    query = request.GET.get('q', '').strip()
    sort = request.GET.get('sort', 'relevance')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    category_slug = request.GET.get('category', '')
    in_stock = request.GET.get('in_stock', '')
    min_rating = request.GET.get('min_rating', '')
    brand = request.GET.get('brand', '')

    products = Product.objects.filter(available=True).select_related('category')

    # Keyword search
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query) |
            Q(category__name__icontains=query)
        )

    # Category filter
    if category_slug:
        products = products.filter(category__slug=category_slug)

    # Price filters
    try:
        if min_price:
            products = products.filter(price__gte=Decimal(min_price))
        if max_price:
            products = products.filter(price__lte=Decimal(max_price))
    except InvalidOperation:
        pass

    # In stock filter
    if in_stock:
        products = products.filter(stock__gt=0)

    # Brand filter
    if brand:
        products = products.filter(brand__iexact=brand)

    # Annotate with avg rating and review count for sorting/filtering
    products = products.annotate(
        avg_rating=Avg('reviews__rating'),
        num_reviews=Count('reviews', distinct=True),
    )

    # Minimum rating filter
    if min_rating:
        try:
            products = products.filter(avg_rating__gte=float(min_rating))
        except ValueError:
            pass

    # Sorting
    sort_map = {
        'price_asc': 'price',
        'price_desc': '-price',
        'newest': '-created',
        'name': 'name',
        'rating': '-avg_rating',
        'popularity': '-num_reviews',
    }
    if sort in sort_map:
        products = products.order_by(sort_map[sort])

    # Available brands for sidebar (from matching products before brand filter)
    all_brands = (
        Product.objects.filter(available=True, brand__gt='')
        .values_list('brand', flat=True)
        .distinct()
        .order_by('brand')
    )

    # Categories for sidebar
    links = Category.objects.all()

    result_count = products.count()

    # Pagination (12 per page)
    paginator = Paginator(products, 12)
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    try:
        page_obj = paginator.page(page_num)
    except (EmptyPage, InvalidPage):
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'query': query,
        'products': page_obj,
        'result_count': result_count,
        'page_obj': page_obj,
        'paginator': paginator,
        'links': links,
        'all_brands': all_brands,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'category_slug': category_slug,
        'in_stock': in_stock,
        'min_rating': min_rating,
        'brand': brand,
    }
    return render(request, 'search.html', context)
