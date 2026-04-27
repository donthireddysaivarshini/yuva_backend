from rest_framework import serializers
import re


def validate_indian_phone(value):
    """Strip +91 prefix and validate exactly 10 digits."""
    cleaned = re.sub(r"^\+?91", "", value.strip())
    cleaned = re.sub(r"\s+", "", cleaned)
    if not re.fullmatch(r"\d{10}", cleaned):
        raise serializers.ValidationError("Enter a valid 10-digit Indian mobile number.")
    return cleaned  # store just the 10-digit number


class BulkOrderFormSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    company = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    phone = serializers.CharField()
    device_type = serializers.CharField(max_length=100)
    quantity = serializers.IntegerField(min_value=1)
    requirements = serializers.CharField(required=False, allow_blank=True, default="")

    def validate_phone(self, value):
        return validate_indian_phone(value)

    def validate_quantity(self, value):
        if value < 5:
            raise serializers.ValidationError("Minimum order quantity is 5 units.")
        return value


class ContactFormSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField()
    order_id = serializers.CharField(required=False, allow_blank=True, default="")
    issue_type = serializers.CharField(max_length=100)
    message = serializers.CharField()

    def validate_phone(self, value):
        return validate_indian_phone(value)


class ComplaintFormSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    order_id = serializers.CharField(max_length=50)
    issue_type = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    phone = serializers.CharField()
    description = serializers.CharField()

    def validate_phone(self, value):
        return validate_indian_phone(value)