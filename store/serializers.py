from rest_framework import serializers
from django.db.models import Avg
from .models import (
    Brand, Category, UsageTag, Product,
    ProductVariant, ProductImage, Review, SiteConfig, Coupon
)


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ['id', 'name', 'slug']


class CategorySerializer(serializers.ModelSerializer):
    # Add this field to return the full absolute URL
    image = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'image', 'is_featured']

    def get_image(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url # Fallback
        return None

class UsageTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageTag
        fields = ['id', 'name', 'slug', 'icon']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'order']

    


class ProductVariantSerializer(serializers.ModelSerializer):
    final_price = serializers.SerializerMethodField()
    final_original_price = serializers.SerializerMethodField()

    class Meta:
        model = ProductVariant
        fields = [
            'id', 'ram', 'storage', 'stock',
            'price_override', 'final_price', 'final_original_price'
        ]

    def get_final_price(self, obj):
        return float(obj.product.price + obj.price_override)

    def get_final_original_price(self, obj):
        if obj.product.original_price:
            return float(obj.product.original_price + obj.price_override)
        return None


class ReviewSerializer(serializers.ModelSerializer):
    date = serializers.SerializerMethodField()
    user_name = serializers.CharField(read_only=True) 

    class Meta:
        model = Review
        fields = ['id', 'user_name', 'rating', 'comment', 'date']

    def get_date(self, obj):
        from django.utils.timesince import timesince
        return f"{timesince(obj.created_at).split(',')[0]} ago"


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing pages"""
    images = ProductImageSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    usage_tags = UsageTagSerializer(many=True, read_only=True)
    condition_display = serializers.CharField(
        source='get_condition_display', read_only=True
    )
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    discount_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'sku',
            'category_name', 'brand_name', 'condition', 'condition_display',
            'price', 'original_price', 'discount_percentage',
            'processor', 'ram', 'storage', 'display',
            'usage_tags', 'images',
            'is_new_arrival', 'is_best_seller', 'is_trending', 'is_best_deal',
            'review_count', 'average_rating',
        ]

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else 0

    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            disc = ((obj.original_price - obj.price) / obj.original_price) * 100
            return round(disc)
        return 0


class ProductDetailSerializer(ProductListSerializer):
    """Full serializer for product detail page"""
    variants = ProductVariantSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    highlights_list = serializers.SerializerMethodField()
    refurbishment_points_list = serializers.SerializerMethodField()
    warranty_details_list = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + [
            'description', 'highlights_list',
            'refurbishment_summary', 'refurbishment_points_list',
            'warranty_summary', 'warranty_details_list',
            'processor', 'ram', 'storage', 'display',
            'graphics', 'operating_system', 'battery',
            'weight', 'ports', 'wifi', 'bluetooth',
            'variants', 'reviews','service_centers', 'warranty_period', 'return_policy'
        ]

    def get_highlights_list(self, obj):
        if not obj.highlights:
            return []
        return [h.strip() for h in obj.highlights.split('\n') if h.strip()]

    def get_refurbishment_points_list(self, obj):
        if not obj.refurbishment_points:
            return []
        return [p.strip() for p in obj.refurbishment_points.split('\n') if p.strip()]

    def get_warranty_details_list(self, obj):
        if not obj.warranty_details:
            return []
        return [d.strip() for d in obj.warranty_details.split('\n') if d.strip()]


class SiteConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteConfig
        fields = '__all__' # Ensure new fields are included

# Add this new serializer at the bottom
class ProductSearchSerializer(serializers.ModelSerializer):
    """Optimized for search dropdown - lightweight + image"""
    image = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    discount_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'title', 'slug', 'sku', 'price', 'original_price', 
            'image', 'category_name', 'brand_name', 'discount_percentage'
        ]
    
    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        return primary_image.image.url if primary_image else None
    
    def get_discount_percentage(self, obj):
        if obj.original_price and obj.original_price > obj.price:
            disc = ((obj.original_price - obj.price) / obj.original_price) * 100
            return round(disc)
        return 0