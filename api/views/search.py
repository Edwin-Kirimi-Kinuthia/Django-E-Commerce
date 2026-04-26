from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Q

from shop.models import Product
from api.serializers.products import ProductListSerializer


class SearchView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        query = request.query_params.get('q', '').strip()
        category = request.query_params.get('category', '')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        min_rating = request.query_params.get('min_rating')
        in_stock = request.query_params.get('in_stock')
        ordering = request.query_params.get('ordering', 'name')

        qs = Product.objects.filter(available=True).select_related('category')

        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(brand__icontains=query)
            )
        if category:
            qs = qs.filter(category__slug=category)
        if min_price:
            qs = qs.filter(price__gte=min_price)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        if in_stock == 'true':
            qs = qs.filter(stock__gt=0)

        allowed_orderings = ['price', '-price', 'name', '-name', 'created', '-created']
        if ordering in allowed_orderings:
            qs = qs.order_by(ordering)

        serializer = ProductListSerializer(qs, many=True, context={'request': request})
        return Response({
            'query': query,
            'count': qs.count(),
            'results': serializer.data,
        })
