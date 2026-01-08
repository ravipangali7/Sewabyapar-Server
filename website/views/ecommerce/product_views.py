from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from ecommerce.models import Product, Category, Review
from website.models import MySetting, CMSPages


def products_view(request):
    """Product listing page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    products = Product.objects.filter(is_active=True, is_approved=True, store__is_opened=True)
    
    # Filter by category
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = Category.objects.get(id=category_id)
            # Get all subcategory IDs
            subcategory_ids = category.subcategories.values_list('id', flat=True)
            products = products.filter(
                Q(category__id=category_id) | Q(category__id__in=subcategory_ids)
            )
        except Category.DoesNotExist:
            pass
    
    # Filter by store
    store_id = request.GET.get('store')
    if store_id:
        products = products.filter(store__id=store_id)
    
    # Search
    search = request.GET.get('search')
    if search:
        products = products.filter(
            Q(name__icontains=search) | Q(description__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.filter(is_active=True, parent=None)
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'products': page_obj,
        'categories': categories,
        'selected_category': category_id,
        'search_query': search,
    }
    
    return render(request, 'website/ecommerce/products.html', context)


def product_detail_view(request, product_id):
    """Product detail page"""
    try:
        settings = MySetting.objects.first()
    except MySetting.DoesNotExist:
        settings = None
    
    menu_pages = CMSPages.objects.filter(on_menu=True)
    footer_pages = CMSPages.objects.filter(on_footer=True)
    
    product = get_object_or_404(Product, id=product_id, is_active=True, is_approved=True, store__is_opened=True)
    reviews = Review.objects.filter(product=product).order_by('-created_at')[:10]
    
    # Get related products (same category)
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True,
        is_approved=True,
        store__is_opened=True
    ).exclude(id=product_id)[:4]
    
    # Check if user has this in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = product.wishlist_set.filter(user=request.user).exists()
    
    # Check if user has this in cart
    in_cart = False
    cart_quantity = 0
    if request.user.is_authenticated:
        cart_item = product.cart_set.filter(user=request.user).first()
        if cart_item:
            in_cart = True
            cart_quantity = cart_item.quantity
    
    context = {
        'settings': settings,
        'menu_pages': menu_pages,
        'footer_pages': footer_pages,
        'product': product,
        'reviews': reviews,
        'related_products': related_products,
        'in_wishlist': in_wishlist,
        'in_cart': in_cart,
        'cart_quantity': cart_quantity,
    }
    
    return render(request, 'website/ecommerce/product_detail.html', context)

