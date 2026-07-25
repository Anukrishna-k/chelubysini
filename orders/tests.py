import urllib.parse
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from products.models import Product, Category
from orders.models import Order, OrderItem
from orders.views import generate_whatsapp_message
from cart.cart import Cart

class WhatsAppOrderIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create category & product
        self.category = Category.objects.create(name="Kasavu Sarees")
        self.product = Product.objects.create(
            category=self.category,
            name="Classic Kasavu Saree",
            price=2500.00,
            stock=10,
            image="products/saree.jpg"
        )
        
        # Create user
        self.user = User.objects.create_user(
            username="test_customer",
            email="customer@example.com",
            password="Password123"
        )
        
        # Log in client
        self.client.login(username="test_customer", password="Password123")
        
        # Add product to cart
        session = self.client.session
        session['cart'] = {
            str(self.product.id): {
                'quantity': 2,
                'price': '2500.00'
            }
        }
        session.save()

    def test_checkout_saves_order_with_pending_status_and_note(self):
        """Checkout should save the order with 'Pending' status and custom note."""
        response = self.client.post(reverse('orders:checkout'), {
            'name': 'Test Recipient',
            'email': 'customer@example.com',
            'phone': '9876543210',
            'address': '123 Main Street',
            'city': 'Bangalore',
            'state': 'Karnataka',
            'pincode': '560001',
            'payment_method': 'COD',
            'order_note': 'Deliver after 6 PM, please.'
        })
        
        # Verify redirect to order_confirmation page
        order = Order.objects.latest('id')
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('orders:order_confirmation', kwargs={'pk': order.id}))
        
        # Verify database storage
        self.assertEqual(order.status, 'Pending')
        self.assertEqual(order.note, 'Deliver after 6 PM, please.')
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.items.first().product, self.product)
        self.assertEqual(order.items.first().quantity, 2)

    def test_whatsapp_message_content_and_encoding(self):
        """Helper generate_whatsapp_message should output correctly structured and encoded string."""
        # Create dummy order in DB
        order = Order.objects.create(
            user=self.user,
            name='Test Recipient',
            email='customer@example.com',
            phone_number='9876543210',
            address='123 Main Street',
            city='Bangalore',
            state='Karnataka',
            pincode='560001',
            total_price=5000.00,
            payment_method='COD',
            status='Pending',
            note='Deliver after 6 PM, please.'
        )
        OrderItem.objects.create(
            order=order,
            product=self.product,
            price=2500.00,
            quantity=2
        )
        
        whatsapp_url = generate_whatsapp_message(order)
        parsed_url = urllib.parse.urlparse(whatsapp_url)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        self.assertEqual(parsed_url.netloc, 'wa.me')
        self.assertEqual(parsed_url.path, '/919497360705')
        self.assertIn('text', query_params)
        
        message_text = query_params['text'][0]
        self.assertIn('NEW ORDER RECEIVED', message_text)
        self.assertIn(f'*Order ID:* {order.id}', message_text)
        self.assertIn('Name: Test Recipient', message_text)
        self.assertIn('Classic Kasavu Saree', message_text)
        self.assertIn('Quantity: 2', message_text)
        self.assertIn('Price: ₹2500.00', message_text)
        self.assertIn('Total Amount: ₹5000.00', message_text)
        self.assertIn('Deliver after 6 PM, please.', message_text)

    def test_payment_verify_redirects_to_confirmation(self):
        """Payment verification should redirect the user to the order confirmation screen."""
        order = Order.objects.create(
            user=self.user,
            name='Test Recipient',
            email='customer@example.com',
            phone_number='9876543210',
            address='123 Main Street',
            city='Bangalore',
            state='Karnataka',
            pincode='560001',
            total_price=5000.00,
            payment_method='Razorpay',
            status='Pending'
        )
        
        response = self.client.post(reverse('orders:payment_verify', kwargs={'pk': order.id}), {
            'status': 'success'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('orders:order_confirmation', kwargs={'pk': order.id}))
        
        # Verify payment status is set to True
        order.refresh_from_db()
        self.assertTrue(order.payment_status)

class AdminProductManagementTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(name="Kasavu Sarees")
        self.product = Product.objects.create(
            category=self.category,
            name="Classic Kasavu Saree",
            price=2500.00,
            stock=10,
            image="products/saree.jpg"
        )
        # Create normal user
        self.user = User.objects.create_user(username='customer', password='password123')
        # Create staff user
        self.staff_user = User.objects.create_user(username='admin_staff', password='password123', is_staff=True)

    def test_admin_product_edit_success(self):
        """Staff members should be able to edit product fields and toggle featured/best seller statuses."""
        self.client.login(username='admin_staff', password='password123')
        edit_url = reverse('orders:admin_product_edit', kwargs={'pk': self.product.id})
        
        response = self.client.post(edit_url, {
            'category': self.category.id,
            'name': 'Updated Saree',
            'description': 'Updated description.',
            'price': '3000.00',
            'stock': '15',
            'featured': 'on',
            'best_seller': 'on'
        })
        self.assertEqual(response.status_code, 302)
        
        # Verify product parameters are updated
        self.product.refresh_from_db()
        self.assertEqual(self.product.name, 'Updated Saree')
        self.assertEqual(self.product.price, 3000.00)
        self.assertEqual(self.product.stock, 15)
        self.assertTrue(self.product.featured)
        self.assertTrue(self.product.best_seller)

    def test_admin_product_delete_success(self):
        """Staff members should be able to delete products."""
        self.client.login(username='admin_staff', password='password123')
        delete_url = reverse('orders:admin_product_delete', kwargs={'pk': self.product.id})
        
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        
        # Verify product is deleted
        self.assertFalse(Product.objects.filter(id=self.product.id).exists())

    def test_non_staff_denied_edit_and_delete(self):
        """Regular customers should be blocked from editing or deleting products."""
        self.client.login(username='customer', password='password123')
        
        # Try to edit
        edit_url = reverse('orders:admin_product_edit', kwargs={'pk': self.product.id})
        response = self.client.post(edit_url, {
            'category': self.category.id,
            'name': 'Hacked Saree',
            'description': 'Hacked description',
            'price': '10.00',
            'stock': '999'
        })
        self.assertNotEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertNotEqual(self.product.name, 'Hacked Saree')
        
        # Try to delete
        delete_url = reverse('orders:admin_product_delete', kwargs={'pk': self.product.id})
        response = self.client.post(delete_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(Product.objects.filter(id=self.product.id).exists())

class HomepageContentManagementTests(TestCase):
    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='admin_staff',
            password='password123',
            is_staff=True
        )
        self.regular_user = User.objects.create_user(
            username='customer',
            password='password123',
            is_staff=False
        )
        
        # Create dummy image for testing uploads
        from django.core.files.uploadedfile import SimpleUploadedFile
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x4c\x01\x00\x3b',
            content_type='image/jpeg'
        )
        
        # Setup initial content
        from products.models import HeroSlide, HappyCustomer
        self.slide = HeroSlide.objects.create(
            subtitle="Initial Subtitle",
            title="Initial Title",
            button_text="Click Me",
            button_url="/target/",
            order=1,
            image=self.test_image
        )
        
        self.testimonial = HappyCustomer.objects.create(
            name="Initial Name",
            location="Initial Location",
            quote="Initial Quote",
            image=self.test_image
        )

    def test_staff_can_add_hero_slide(self):
        self.client.login(username='admin_staff', password='password123')
        from products.models import HeroSlide
        add_url = reverse('orders:admin_heroslide_add')
        
        response = self.client.post(add_url, {
            'subtitle': 'New Subtitle',
            'title': 'New Title',
            'button_text': 'Shop Now',
            'button_url': '/shop/',
            'order': '2',
            'image': self.test_image
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(HeroSlide.objects.filter(title='New Title').exists())

    def test_staff_can_edit_hero_slide(self):
        self.client.login(username='admin_staff', password='password123')
        from products.models import HeroSlide
        edit_url = reverse('orders:admin_heroslide_edit', kwargs={'pk': self.slide.id})
        
        response = self.client.post(edit_url, {
            'subtitle': 'Updated Subtitle',
            'title': 'Updated Title',
            'button_text': 'Updated Button',
            'button_url': '/updated-url/',
            'order': '10'
        })
        self.assertEqual(response.status_code, 302)
        self.slide.refresh_from_db()
        self.assertEqual(self.slide.title, 'Updated Title')
        self.assertEqual(self.slide.subtitle, 'Updated Subtitle')
        self.assertEqual(self.slide.button_url, '/updated-url/')
        self.assertEqual(self.slide.order, 10)

    def test_staff_can_delete_hero_slide(self):
        self.client.login(username='admin_staff', password='password123')
        from products.models import HeroSlide
        delete_url = reverse('orders:admin_heroslide_delete', kwargs={'pk': self.slide.id})
        
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(HeroSlide.objects.filter(id=self.slide.id).exists())

    def test_staff_can_edit_customer_testimonial(self):
        self.client.login(username='admin_staff', password='password123')
        from products.models import HappyCustomer
        edit_url = reverse('orders:admin_customer_photo_edit', kwargs={'pk': self.testimonial.id})
        
        response = self.client.post(edit_url, {
            'name': 'Updated Name',
            'location': 'Updated Location',
            'quote': 'Updated Quote'
        })
        self.assertEqual(response.status_code, 302)
        self.testimonial.refresh_from_db()
        self.assertEqual(self.testimonial.name, 'Updated Name')
        self.assertEqual(self.testimonial.location, 'Updated Location')
        self.assertEqual(self.testimonial.quote, 'Updated Quote')

    def test_staff_can_delete_customer_testimonial(self):
        self.client.login(username='admin_staff', password='password123')
        from products.models import HappyCustomer
        delete_url = reverse('orders:admin_customer_photo_delete', kwargs={'pk': self.testimonial.id})
        
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(HappyCustomer.objects.filter(id=self.testimonial.id).exists())

    def test_non_staff_denied_access(self):
        self.client.login(username='customer', password='password123')
        from products.models import HeroSlide, HappyCustomer
        
        # Slide add block
        add_url = reverse('orders:admin_heroslide_add')
        response = self.client.post(add_url, {
            'subtitle': 'Hack Subtitle',
            'title': 'Hack Title',
            'image': self.test_image
        })
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(HeroSlide.objects.filter(title='Hack Title').exists())
        
        # Testimonial delete block
        delete_url = reverse('orders:admin_customer_photo_delete', kwargs={'pk': self.testimonial.id})
        response = self.client.post(delete_url)
        self.assertNotEqual(response.status_code, 200)
        self.assertTrue(HappyCustomer.objects.filter(id=self.testimonial.id).exists())
