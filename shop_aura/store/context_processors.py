from .models import CartItem

def cart_count(request):
    """Context processor to add cart count to all templates."""
    if request.user.is_authenticated:
        count = CartItem.objects.filter(user=request.user).count()
        return {'cart_count': count}
    return {'cart_count': 0}