from django.urls import path
from . import views

urlpatterns = [
    # Read APIs
    path("api/search/", views.api_search, name="api_search"),
    path("api/concepts/", views.api_concepts, name="api_concepts"),
    path("api/collections/", views.api_collections, name="api_collections"),
    path("api/collections/<int:pk>", views.api_collection_detail, name="api_collection_detail"),

    # AI APIs (support POST and GET where implemented)
    path("api/search/semantic", views.api_search_semantic, name="api_search_semantic"),
    path("api/search/semantic/", views.api_search_semantic),
    # Local embeddings-based semantic search
    path("api/search/semantic-emb", views.api_search_semantic_emb, name="api_search_semantic_emb"),
    path("api/search/semantic-emb/", views.api_search_semantic_emb),
    path("api/search/similarity", views.api_search_similarity, name="api_search_similarity"),
    path("api/search/similarity/", views.api_search_similarity),

    # Trends
    path("api/trends/", views.api_trends, name="api_trends"),
    path("api/trends", views.api_trends),

    # JSON CRUD write APIs
    path("api/concepts/write/", views.api_concepts_write, name="api_concepts_write"),
    path("api/concepts/write/<int:pk>", views.api_concepts_write, name="api_concepts_write_detail"),
    path("api/collections/write/", views.api_collections_write, name="api_collections_write"),
    path("api/collections/write/<int:pk>", views.api_collections_write, name="api_collections_write_detail"),

    # AI Resource endpoints
    
    path("api/resources/<int:id>/transcribe", views.api_resource_transcribe, name="api_resource_transcribe"),
    path("api/resources/<int:id>/transcribe/", views.api_resource_transcribe),

    # Advanced AI endpoints
    path("api/ai/generate/", views.api_generate_text, name="api_generate_text"),
    path("api/ai/embedding/", views.api_get_embedding, name="api_get_embedding"),
    path("api/ai/classify/", views.api_classify_text, name="api_classify_text"),
    path("api/ai/extract-concepts/", views.api_extract_concepts, name="api_extract_concepts"),
    path("api/ai/ask/", views.api_ai_ask, name="api_ai_ask"),
    path("api/ai/describe/", views.api_ai_describe, name="api_ai_describe"),
   
    # Lightweight AI test endpoint (developer convenience)
    path("ai/test/", views.ai_test, name="ai_test"),
    path("ai/test", views.ai_test),

    # Recommendations & interactions
    path("api/recommendations", views.api_recommendations, name="api_recommendations"),
    path("api/recommendations/", views.api_recommendations),
    path("api/interactions/log", views.api_log_interaction, name="api_log_interaction"),
    path("api/interactions/log/", views.api_log_interaction),
]
