from django.contrib import admin
from .models import Concept, Collection

@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "level", "created_at")
    search_fields = ("name", "description", "level")


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "filiere", "level", "created_at")
    search_fields = ("name", "description", "filiere", "level")
    filter_horizontal = ("concepts",)
