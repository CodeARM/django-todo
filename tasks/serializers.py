from rest_framework import serializers
from django.core.validators import FileExtensionValidator
from django.conf import settings

class TodoSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    task = serializers.CharField(max_length=500, required=True)
    context = serializers.CharField(max_length=200, required=False, allow_blank=True)
    aof = serializers.CharField(max_length=200, required=False, allow_blank=True)
    date = serializers.CharField(required=False, allow_blank=True)
    done = serializers.BooleanField(default=False)
    file_url = serializers.URLField(read_only=True)
    created_at = serializers.CharField(read_only=True)
    file = serializers.FileField(required=False, write_only=True, validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'])
    ])
    
    def validate_file(self, value):
        if value and value.size > settings.MAX_UPLOAD_SIZE:
            raise serializers.ValidationError(f'File size exceeds {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB limit')
        return value