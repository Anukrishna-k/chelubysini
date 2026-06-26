import os
import io
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.contrib.auth.models import User
from products.models import Category, Product, Review, Coupon
from PIL import Image, ImageDraw, ImageFont
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Populates the database with initial categories, products, coupons, and mock reviews, generating elegant placeholder images.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing data...')
        Product.objects.all().delete()
        Category.objects.all().delete()
        Coupon.objects.all().delete()
        
        self.stdout.write('Populating categories and products...')
        
        # Color palettes for placeholders
        colors = {
            'Kasavu Sarees': (245, 242, 233),     # Off-white Cream
            'Settumundu': (238, 233, 218),        # Rich Cream
            'Designer Sarees': (27, 58, 36),       # Deep Forest Green
            'Silk Sarees': (106, 27, 41),         # Rich Maroon/Burgundy
            'Ready-made Blouses': (197, 160, 89),  # Gold Zari
            'Traditional Jewellery': (212, 175, 55) # Antique Gold
        }
        
        categories_data = [
            'Kasavu Sarees', 'Settumundu', 'Designer Sarees', 'Silk Sarees', 'Ready-made Blouses', 'Traditional Jewellery'
        ]
        
        created_categories = {}
        for cat_name in categories_data:
            color = colors.get(cat_name, (200, 200, 200))
            
            # Generate category bubble image (square placeholder)
            img = Image.new('RGB', (150, 150), color=color)
            draw = ImageDraw.Draw(img)
            # Add simple drawing for off-white text contrast
            text_color = (27, 58, 36) if cat_name in ['Kasavu Sarees', 'Settumundu'] else (255, 255, 255)
            draw.text((75, 75), cat_name[0], fill=text_color, anchor="mm")
            
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG')
            image_file = ContentFile(img_io.getvalue(), name=f"{cat_name.lower().replace(' ', '_').replace('-', '_')}_cat.jpg")
            
            category = Category.objects.create(name=cat_name)
            category.image.save(f"{cat_name.lower().replace(' ', '_').replace('-', '_')}_cat.jpg", image_file, save=True)
            created_categories[cat_name] = category
            
            self.stdout.write(f"Created category: {cat_name}")

        # Products Data
        products_data = [
            # Kasavu Sarees
            {
                'category': 'Kasavu Sarees',
                'name': 'Balaramapuram Premium Kasavu Saree',
                'description': 'A masterwork from Balaramapuram handloom weavers. Pure 100s count combed cotton fabric adorned with a rich 3-inch pure gold zari border. Exudes traditional grace.',
                'price': 3200.00,
                'stock': 12,
                'featured': True,
                'best_seller': False,
            },
            {
                'category': 'Kasavu Sarees',
                'name': 'Silver Kasavu Kerala Saree',
                'description': 'A chic modern alternative to gold zari, featuring a fine silver Kasavu border on cream handloom cotton. Soft texture, ideal for temple visits and festive occasions.',
                'price': 2800.00,
                'stock': 8,
                'featured': False,
                'best_seller': True,
            },
            # Settumundu
            {
                'category': 'Settumundu',
                'name': 'Kuthampully Double Zari Settumundu',
                'description': 'Traditional double-zari Mundum Neriathum from Kuthampully weavers. Soft hand-woven cotton stripes with classic gold borders that drape perfectly and feel comfortable all day.',
                'price': 1999.00,
                'stock': 15,
                'featured': True,
                'best_seller': True,
            },
            {
                'category': 'Settumundu',
                'name': 'Mural Painted Peacock Settumundu',
                'description': 'Fine cream handloom Settumundu adorned with exquisite hand-painted mural art depicting vibrant peacock and floral motifs on the neriathu (pallu).',
                'price': 2999.00,
                'stock': 6,
                'featured': False,
                'best_seller': False,
            },
            # Designer Sarees
            {
                'category': 'Designer Sarees',
                'name': 'Emerald Floral Georgette Saree',
                'description': 'Flowing designer georgette saree in a rich deep emerald green color, detailed with delicate floral thread embroidery and tiny sequins along the scalloped borders.',
                'price': 2499.00,
                'stock': 10,
                'featured': False,
                'best_seller': True,
            },
            {
                'category': 'Designer Sarees',
                'name': 'Ajrakh Print Handloom Saree',
                'description': 'Organic handloom cotton saree printed with natural dyes using traditional Ajrakh block printing. Highly breathable and perfect for daily wear.',
                'price': 1850.00,
                'stock': 10,
                'featured': True,
                'best_seller': False,
            },
            # Silk Sarees
            {
                'category': 'Silk Sarees',
                'name': 'Kanchipuram Crimson Silk Saree',
                'description': 'A royal crimson-red pure silk saree handwoven in Kanchipuram, featuring rich gold zari brocade work and traditional temple patterns along the border.',
                'price': 7500.00,
                'stock': 5,
                'featured': True,
                'best_seller': False,
            },
            {
                'category': 'Silk Sarees',
                'name': 'Soft Indigo Tussar Silk Saree',
                'description': 'Elegant deep indigo Tussar silk saree featuring a contrasting copper-zari border and delicate hand-block printed motifs. Lightweight and soft drape.',
                'price': 4500.00,
                'stock': 7,
                'featured': False,
                'best_seller': True,
            },
            # Ready-made Blouses
            {
                'category': 'Ready-made Blouses',
                'name': 'Peacock Motif Aari Blouse',
                'description': 'Ready-made green silk blouse intricately embroidered with peacock designs using fine hand Aari needlework. Padded with a secure back tie.',
                'price': 1499.00,
                'stock': 20,
                'featured': False,
                'best_seller': True,
            },
            {
                'category': 'Ready-made Blouses',
                'name': 'Golden Brocade Padded Blouse',
                'description': 'Classic elbow-sleeve blouse made from premium golden Banarasi brocade fabric. Fully lined with soft cotton, pairs elegantly with any Kasavu saree.',
                'price': 1199.00,
                'stock': 18,
                'featured': True,
                'best_seller': False,
            },
            # Traditional Jewellery
            {
                'category': 'Traditional Jewellery',
                'name': 'Kemp Stone Temple Jhumkas',
                'description': 'Traditional antique-finish gold-plated temple earrings studded with red kemp stones, green crystals, and hanging seed pearls.',
                'price': 799.00,
                'stock': 25,
                'featured': False,
                'best_seller': False,
            }
        ]

        for p_data in products_data:
            cat_obj = created_categories[p_data['category']]
            color = colors.get(p_data['category'], (150, 150, 150))
            
            # Generate product card image (vertical poster format)
            img = Image.new('RGB', (400, 500), color=color)
            draw = ImageDraw.Draw(img)
            
            # Draw chic minimal borders
            draw.rectangle([(20, 20), (380, 480)], outline=(255, 255, 255), width=2)
            
            # Draw label
            draw.text((200, 230), p_data['name'].split()[0], fill=(255, 255, 255), anchor="mm")
            draw.text((200, 270), "CHELU", fill=(255, 255, 255), anchor="mm")
            
            img_io = io.BytesIO()
            img.save(img_io, format='JPEG')
            image_file = ContentFile(img_io.getvalue(), name=f"{p_data['name'].lower().replace(' ', '_')}.jpg")
            
            product = Product.objects.create(
                category=cat_obj,
                name=p_data['name'],
                description=p_data['description'],
                price=p_data['price'],
                stock=p_data['stock'],
                featured=p_data['featured'],
                best_seller=p_data['best_seller']
            )
            product.image.save(f"{p_data['name'].lower().replace(' ', '_')}.jpg", image_file, save=True)
            self.stdout.write(f"Created product: {product.name}")
            
        # Create standard coupon codes
        Coupon.objects.create(
            code="CHELU10",
            discount_percent=10,
            active=True,
            valid_until=timezone.now() + timedelta(days=30)
        )
        Coupon.objects.create(
            code="SINI20",
            discount_percent=20,
            active=True,
            valid_until=timezone.now() + timedelta(days=30)
        )
        self.stdout.write("Created standard coupons (CHELU10 and SINI20)")
        
        # Create some reviews if admin user is already created
        admin_user = User.objects.filter(is_superuser=True).first()
        if admin_user:
            first_product = Product.objects.all().first()
            if first_product:
                Review.objects.create(
                    product=first_product,
                    user=admin_user,
                    rating=5,
                    comment="Absolutely gorgeous piece! The fabric is high quality and breathes well. Got multiple compliments at an event."
                )
                self.stdout.write(f"Added mock review to {first_product.name}")
                
        self.stdout.write(self.style.SUCCESS('Successfully populated database!'))
