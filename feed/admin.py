from django.contrib import admin
from .models import FeedItem


@admin.register(FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    """
    Configuration admin pour FeedItem
    """
    
    list_display = [
        'title',
        'content_type',
        'author',
        'is_active',
        'created_at',
        'updated_at'
    ]
    
    list_filter = [
        'content_type',
        'is_active',
        'created_at',
        'author'
    ]
    
    search_fields = [
        'title',
        'description',
        'author__username'
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Informations principales', {
            'fields': ('title', 'description', 'content_type', 'author', 'deadline')
        }),
        ('Métadonnées', {
            'fields': ('is_active', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    date_hierarchy = 'created_at'
    
    ordering = ['-created_at']
    
    list_per_page = 25
    
    actions = ['activate_items', 'deactivate_items']
    
    def activate_items(self, request, queryset):
        """Active les éléments sélectionnés"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} élément(s) activé(s).')
    activate_items.short_description = '✅ Activer les éléments sélectionnés'
    
    def deactivate_items(self, request, queryset):
        """Désactive les éléments sélectionnés"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} élément(s) désactivé(s).')
    deactivate_items.short_description = '❌ Désactiver les éléments sélectionnés'