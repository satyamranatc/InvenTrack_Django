from django.contrib.auth import authenticate, get_user_model
from rest_framework import viewsets, status, response
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Category, Product, Order, InventoryLog
from .serializers import CategorySerializer, ProductSerializer, OrderSerializer, InventoryLogSerializer

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    identifier = (request.data.get('email') or request.data.get('username') or '').strip()
    password = request.data.get('password') or ''

    if not identifier or not password:
        return response.Response(
            {'message': 'Email/username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    username = identifier
    if '@' in identifier:
        matched_user = User.objects.filter(email__iexact=identifier).first()
        if matched_user:
            username = matched_user.username

    user = authenticate(request, username=username, password=password)
    if user is None:
        return response.Response(
            {'message': 'Invalid email or password.'},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    return response.Response({
        'token': access_token,
        'access': access_token,
        'refresh': str(refresh),
        'data': {
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'name': user.get_full_name() or user.username,
            }
        },
    })

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    # permission_classes = [IsAuthenticated]

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        product = serializer.save()
        InventoryLog.objects.create(
            product=product,
            productName=product.name,
            type='Inbound',
            quantityChange=product.stock,
            newStock=product.stock,
            reason='Initial Stock Entry'
        )

    def perform_update(self, serializer):
        old_stock = self.get_object().stock
        product = serializer.save()
        new_stock = product.stock
        
        if old_stock != new_stock:
            quantity_change = new_stock - old_stock
            log_type = 'Inbound' if quantity_change > 0 else 'Outbound'
            if 'adjustment' in self.request.data.get('reason', '').lower():
                log_type = 'Adjustment'
            
            InventoryLog.objects.create(
                product=product,
                productName=product.name,
                type=log_type,
                quantityChange=quantity_change,
                newStock=new_stock,
                reason=self.request.data.get('reason', 'Manual Update')
            )

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    # permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        order = serializer.save()
        product = order.product
        
        # Deduct stock
        product.stock -= order.quantity
        product.save()
        
        # Log movement
        InventoryLog.objects.create(
            product=product,
            productName=product.name,
            type='Outbound',
            quantityChange=-order.quantity,
            newStock=product.stock,
            reason=f'Order #{order.id} for {order.customerName}'
        )

class InventoryLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryLog.objects.all().order_by('-timestamp')
    serializer_class = InventoryLogSerializer
    # permission_classes = [IsAuthenticated]
