from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group, User
from django.core.paginator import EmptyPage, InvalidPage, Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import translation

from .forms import SignUpForm
from .middleware import CURRENCIES
from .models import Category, FeaturedSlide, Product, Review
from wishlist.models import WishlistItem

def index(request):
	text_var = 'This is my first django app web page.'
	return HttpResponse(text_var)

#Category view

def allProdCat(request, c_slug=None):
    c_page = None
    if c_slug:
        c_page = get_object_or_404(Category, slug=c_slug)
        products_list = Product.objects.filter(category=c_page, available=True)
    else:
        products_list = Product.objects.filter(available=True)

    # Sidebar filters
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    in_stock  = request.GET.get('in_stock')
    sort      = request.GET.get('sort', 'newest')

    if min_price:
        try:
            products_list = products_list.filter(price__gte=min_price)
        except Exception:
            pass
    if max_price:
        try:
            products_list = products_list.filter(price__lte=max_price)
        except Exception:
            pass
    if in_stock == 'true':
        products_list = products_list.filter(stock__gt=0)

    sort_map = {
        'newest':     '-created',
        'price_asc':  'price',
        'price_desc': '-price',
        'name':       'name',
    }
    products_list = products_list.order_by(sort_map.get(sort, '-created_date'))

    paginator = Paginator(products_list, 6)
    try:
        page = int(request.GET.get('page', '1'))
    except Exception:
        page = 1
    try:
        products = paginator.page(page)
    except (EmptyPage, InvalidPage):
        products = paginator.page(paginator.num_pages)

    slides = []
    featured_products = []
    if c_slug is None:
        slides = list(FeaturedSlide.objects.filter(is_active=True).exclude(image='').order_by('order', 'id'))
        featured_products = list(Product.objects.filter(is_featured=True, available=True)[:12])

    return render(request, 'shop/category.html', {
        'category':          c_page,
        'products':          products,
        'slides':            slides,
        'featured_products': featured_products,
        'sort':              sort,
        'min_price':         min_price or '',
        'max_price':         max_price or '',
        'in_stock':          in_stock or '',
    })


#Product View

def ProdCatDetail(request, c_slug, product_slug):
    product = get_object_or_404(Product, category__slug=c_slug, slug=product_slug)

    # Group variants by name (e.g. {'Size': [...], 'Color': [...]})
    variant_groups = defaultdict(list)
    for v in product.variants.all():
        variant_groups[v.name].append(v)

    # Wishlist status
    is_wishlisted = (
        request.user.is_authenticated and
        WishlistItem.objects.filter(user=request.user, product=product).exists()
    )

    return render(request, 'shop/product.html', {
        'product': product,
        'variant_groups': dict(variant_groups),
        'is_wishlisted': is_wishlisted,
    })


# ---------------------------------------------------------------------------
# Currency / Language switchers
# ---------------------------------------------------------------------------

def set_currency(request):
    code = request.GET.get('code', '').upper()
    if code in CURRENCIES:
        request.session['currency'] = code
    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


def set_language_view(request):
    lang = request.GET.get('lang', 'en')
    request.session['django_language'] = lang
    translation.activate(lang)
    next_url = request.META.get('HTTP_REFERER', '/')
    return redirect(next_url)


#Forms View

def signupView(request):
	if request.method == 'POST':
		form = SignUpForm(request.POST)
		if form.is_valid():
			user = form.save()
			# Optionally add to Customer group if it exists
			customer_group = Group.objects.filter(name='Customer').first()
			if customer_group:
				customer_group.user_set.add(user)
			login(request, user)
			return redirect('shop:allProdCat')
	else:
		form = SignUpForm()
	return render(request, 'accounts/signup.html', {'form': form})			


def signinView(request):
	if request.method == 'POST':
		form = AuthenticationForm(data = request.POST) #putting data = request.POST as the signin form was treating form as a empty form
		if form.is_valid():
			username = request.POST['username']
			password = request.POST['password']
			user = authenticate(username = username, password = password)
			if user is not None: #checking if there is any user of that username and password and taking action accordingly 
				login(request, user)
				return redirect('shop:allProdCat')
			else:
				return redirect('signup')
	else:
		form = AuthenticationForm()
	return render(request, 'accounts/signin.html', {'form':form})


def signoutView(request):
	logout(request)
	return redirect('signin')


@login_required
def submit_review(request, product_id):
	product = get_object_or_404(Product, id=product_id)
	if request.method == 'POST':
		rating = request.POST.get('rating', '').strip()
		title = request.POST.get('title', '').strip()
		body = request.POST.get('body', '').strip()
		if rating and body:
			Review.objects.update_or_create(
				product=product,
				user=request.user,
				defaults={
					'rating': int(rating),
					'title': title,
					'body': body,
				}
			)
			messages.success(request, 'Your review has been submitted.')
	return redirect(product.get_url() + '#reviews')