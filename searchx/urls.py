from django.urls import path
from . import views

app_name = "searchx"

urlpatterns = [
    # Search & Discovery UI
    path("search/", views.search_page, name="search"),
    # HTML CRUD
    path("concepts/", views.concept_list, name="concept_list"),
    path("concepts/new/", views.concept_create, name="concept_create"),
    path("concepts/<int:pk>/edit/", views.concept_edit, name="concept_edit"),
    path("concepts/<int:pk>/delete/", views.concept_delete, name="concept_delete"),

    path("collections/", views.collection_list, name="collection_list"),
    path("collections/new/", views.collection_create, name="collection_create"),
    path("collections/<int:pk>/edit/", views.collection_edit, name="collection_edit"),
    path("collections/<int:pk>/delete/", views.collection_delete, name="collection_delete"),
    # API endpoints
    path("api/search/", views.api_search, name="api_search"),
    path("api/concepts/", views.api_concepts, name="api_concepts"),
    path("api/collections/<int:pk>", views.api_collection_detail, name="api_collection_detail"),
    path("api/search/semantic", views.api_search_semantic, name="api_search_semantic"),
    path("api/search/semantic-emb", views.api_search_semantic_emb, name="api_search_semantic_emb"),
    path("api/search/similarity", views.api_search_similarity, name="api_search_similarity"),
    path("api/trends/", views.api_trends, name="api_trends"),
    # Convenience UI pages that consume the above APIs
    path("pages/api/search/", views.api_search_page, name="api_search_page"),
    path("pages/api/concepts/", views.api_concepts_page, name="api_concepts_page"),
    path("pages/api/collection/<int:pk>/", views.api_collection_page, name="api_collection_page"),
    path("pages/api/search/semantic/", views.api_search_semantic_page, name="api_search_semantic_page"),
    path("pages/api/search/semantic-emb/", views.api_search_semantic_emb_page, name="api_search_semantic_emb_page"),
    path("pages/api/search/similarity/", views.api_search_similarity_page, name="api_search_similarity_page"),
    path("pages/api/trends/", views.api_trends_page, name="api_trends_page"),
]
