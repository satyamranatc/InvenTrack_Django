from datetime import date
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from .models import Category, Product, Order, InventoryLog

User = get_user_model()


class InventoryAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='admin',
            email='admin@inventrack.com',
            password='password123',
        )

    def test_login_with_email_and_username(self):
        res_email = self.client.post(
            '/api/auth/login',
            {'email': 'admin@inventrack.com', 'password': 'password123'},
            format='json',
        )
        self.assertEqual(res_email.status_code, status.HTTP_200_OK)
        self.assertIn('token', res_email.data)
        self.assertEqual(res_email.data['data']['user']['email'], 'admin@inventrack.com')

        res_bad = self.client.post(
            '/api/auth/login',
            {'email': 'admin@inventrack.com', 'password': 'wrong'},
            format='json',
        )
        self.assertEqual(res_bad.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_category_product_order_and_audit_flow(self):
        # Create category
        cat_res = self.client.post('/api/categories', {'name': 'Electronics'}, format='json')
        self.assertEqual(cat_res.status_code, status.HTTP_201_CREATED)
        cat_id = cat_res.data['id']

        # Create product -> creates Inbound log
        prod_res = self.client.post(
            '/api/products',
            {
                'name': 'MacBook Pro',
                'price': '1999.00',
                'costPrice': '1500.00',
                'category': cat_id,
                'stock': 10,
                'minStockThreshold': 3,
                'location': 'Warehouse A',
            },
            format='json',
        )
        self.assertEqual(prod_res.status_code, status.HTTP_201_CREATED)
        prod_id = prod_res.data['id']
        self.assertEqual(prod_res.data['category_name'], 'Electronics')
        self.assertEqual(InventoryLog.objects.filter(product_id=prod_id, type='Inbound').count(), 1)

        # Update product stock -> creates Adjustment log
        patch_res = self.client.patch(
            f'/api/products/{prod_id}',
            {'stock': 15, 'reason': 'Manual Adjustment'},
            format='json',
        )
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(InventoryLog.objects.filter(product_id=prod_id, type='Adjustment').count(), 1)

        # Create order -> deducts stock and creates Outbound log
        order_res = self.client.post(
            '/api/orders',
            {
                'customerName': 'Satyam Rana',
                'product': prod_id,
                'quantity': 4,
                'orderDate': str(date.today()),
                'status': 'Pending',
            },
            format='json',
        )
        self.assertEqual(order_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(order_res.data['product_name'], 'MacBook Pro')
        self.assertEqual(Product.objects.get(id=prod_id).stock, 11)
        self.assertEqual(InventoryLog.objects.filter(product_id=prod_id, type='Outbound').count(), 1)

        # Audit logs endpoint
        logs_res = self.client.get('/api/audit-logs')
        self.assertEqual(logs_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(logs_res.data), 3)
