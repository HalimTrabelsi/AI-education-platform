from rest_framework import serializers
from django.conf import settings
from .models import Resource
import os
from urllib.parse import urljoin

class ResourceSerializer(serializers.Serializer):
    id = serializers.CharField(source='pk', read_only=True)
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True, required=False)
    file = serializers.SerializerMethodField()        # <-- génère URL complète
    resource_type = serializers.ChoiceField(choices=['PDF', 'VIDEO', 'IMAGE'])
    tags = serializers.ListField(child=serializers.CharField(), required=False)
    uploaded_at = serializers.DateTimeField(read_only=True)
    content_text = serializers.CharField(allow_blank=True, required=False)
    summary = serializers.CharField(read_only=True, allow_blank=True)
    formulas = serializers.CharField(read_only=True, allow_blank=True)
    images_extracted = serializers.DictField(read_only=True)
    processed = serializers.BooleanField(read_only=True)
    thumbnail = serializers.SerializerMethodField()  # <-- génère URL complète


    def get_file(self, obj):
        if obj.file:
            return urljoin(settings.MEDIA_URL, obj.file)
        return ''

    def get_thumbnail(self, obj):
        if obj.thumbnail:
            return urljoin(settings.MEDIA_URL, f"resources/{obj.thumbnail}")
        return ''

    def create(self, validated_data):
        tags = validated_data.get('tags', [])
        if isinstance(tags, str):
            validated_data['tags'] = [t.strip() for t in tags.split(',')]
        resource = Resource(**validated_data)
        resource.save()
        return resource

    def update(self, instance, validated_data):
        tags = validated_data.get('tags', [])
        if isinstance(tags, str):
            validated_data['tags'] = [t.strip() for t in tags.split(',')]
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
