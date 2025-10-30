from django.shortcuts import render
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.db.models import Q
from django.utils import timezone
from collections import Counter
import json
import numpy as np
from django.conf import settings
from web_project import TemplateLayout

from .models import Concept, Collection, UserInteraction
from .forms import ConceptForm, CollectionForm

def search_page(request):
    q = request.GET.get("q", "").strip()
    return render(request, "searchx/search.html", {"q": q})


def api_search_page(request):
    """UI page that consumes `/api/search/` and renders results."""
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_search.html", context)


def api_concepts_page(request):
    """UI page that consumes `/api/concepts/` and renders the list + create form."""
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_concepts.html", context)


def api_collection_page(request, pk: int):
    """UI page that fetches `/api/collections/<pk>` and shows details."""
    context = {"pk": pk}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_collection.html", context)


def api_search_semantic_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_search_semantic.html", context)


def api_search_similarity_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_search_similarity.html", context)


def api_search_semantic_emb_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_search_semantic_emb.html", context)


def api_trends_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_trends.html", context)

def concept_list(request):
    items = Concept.objects.all().order_by("name")
    return render(request, "searchx/manage/concept_list.html", {"items": items})


def concept_create(request):
    if request.method == "POST":
        form = ConceptForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("searchx:concept_list"))
    else:
        form = ConceptForm()
    return render(request, "searchx/manage/concept_form.html", {"form": form})


def concept_edit(request, pk: int):
    try:
        obj = Concept.objects.get(pk=pk)
    except Concept.DoesNotExist:
        raise Http404
    if request.method == "POST":
        form = ConceptForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("searchx:concept_list"))
    else:
        form = ConceptForm(instance=obj)
    return render(request, "searchx/manage/concept_form.html", {"form": form})


def concept_delete(request, pk: int):
    try:
        obj = Concept.objects.get(pk=pk)
    except Concept.DoesNotExist:
        raise Http404
    if request.method == "POST":
        obj.delete()
        return HttpResponseRedirect(reverse("searchx:concept_list"))
    return render(request, "searchx/manage/confirm_delete.html", {"object": obj, "type": "Concept"})


def collection_list(request):
    items = Collection.objects.all().order_by("name")
    return render(request, "searchx/manage/collection_list.html", {"items": items})


def collection_create(request):
    if request.method == "POST":
        form = CollectionForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("searchx:collection_list"))
    else:
        form = CollectionForm()
    return render(request, "searchx/manage/collection_form.html", {"form": form})


def collection_edit(request, pk: int):
    try:
        obj = Collection.objects.get(pk=pk)
    except Collection.DoesNotExist:
        raise Http404
    if request.method == "POST":
        form = CollectionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("searchx:collection_list"))
    else:
        form = CollectionForm(instance=obj)
    return render(request, "searchx/manage/collection_form.html", {"form": form})


def collection_delete(request, pk: int):
    try:
        obj = Collection.objects.get(pk=pk)
    except Collection.DoesNotExist:
        raise Http404
    if request.method == "POST":
        obj.delete()
        return HttpResponseRedirect(reverse("searchx:collection_list"))
    return render(request, "searchx/manage/confirm_delete.html", {"object": obj, "type": "Collection"})


def api_concepts(request):
    if request.method == "POST":
        # Accept FR aliases: nom->name, niveau->level
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        name = (payload.get("name") or payload.get("nom") or "").strip()
        description = payload.get("description", "")
        level = (payload.get("level") or payload.get("niveau") or "").strip()
        c = Concept(name=name, description=description, level=level)
        c.save()
        return JsonResponse({"id": c.id}, status=201)
    data = [
        {"id": c.id, "name": c.name, "description": c.description, "level": c.level}
        for c in Concept.objects.all().order_by("name")
    ]
    return JsonResponse({"results": data})


def api_collections(request):
    if request.method == "POST":
        # Accept FR aliases: nom->name, niveau->level, concepts->concept_ids
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        def parse_resources(val):
            if val in (None, ""):
                return []
            if isinstance(val, (list, dict)):
                return val
            try:
                return json.loads(val)
            except Exception:
                return []
        name = (payload.get("name") or payload.get("nom") or "").strip()
        description = payload.get("description", "")
        filiere = payload.get("filiere", "")
        level = (payload.get("level") or payload.get("niveau") or "").strip()
        resources = parse_resources(payload.get("resources"))
        col = Collection(name=name, description=description, filiere=filiere, level=level, resources=resources)
        col.save()
        concept_ids = payload.get("concept_ids") or payload.get("concepts") or []
        if concept_ids:
            col.concepts.set(Concept.objects.filter(id__in=concept_ids))
        return JsonResponse({"id": col.id}, status=201)
    cols = []
    for col in Collection.objects.all().order_by("name"):
        cols.append({
            "id": col.id,
            "name": col.name,
            "description": col.description,
            "filiere": col.filiere,
            "level": col.level,
            "concepts": [
                {"id": c.id, "name": c.name, "level": c.level} for c in col.concepts.all()
            ],
            "resources": col.resources,
        })
    return JsonResponse({"results": cols})


def api_collection_detail(request, pk: int):
    try:
        col = Collection.objects.get(pk=pk)
    except Collection.DoesNotExist:
        raise Http404
    data = {
        "id": col.id,
        "name": col.name,
        "description": col.description,
        "filiere": col.filiere,
        "level": col.level,
        "concepts": [
            {"id": c.id, "name": c.name, "level": c.level} for c in col.concepts.all()
        ],
        "resources": col.resources,
    }
    return JsonResponse(data)


def api_search(request):
    q = request.GET.get("q", "").strip()
    concepts = []
    collections = []
    resources = []
    if q:
        concepts_qs = Concept.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q)
        ).order_by("name")[:20]
        collections_qs = Collection.objects.filter(
            Q(name__icontains=q) | Q(description__icontains=q) | Q(filiere__icontains=q)
        ).order_by("name")[:20]
        concepts = [
            {"id": c.id, "name": c.name, "description": c.description, "level": c.level}
            for c in concepts_qs
        ]
        collections = [
            {"id": c.id, "name": c.name, "description": c.description}
            for c in collections_qs
        ]
        for col in collections_qs:
            for r in col.resources:
                resources.append(r)
    return JsonResponse({
        "query": q,
        "concepts": concepts,
        "collections": collections,
        "resources": resources,
    })


@csrf_exempt
def api_search_semantic(request):
    # Support POST (JSON {text} or {query, filiere}) and GET (?q=)
    try:
        if request.method == "POST":
            try:
                payload = json.loads(request.body.decode("utf-8"))
            except Exception:
                payload = {}
            text = (payload.get("text") or payload.get("query") or "").strip()
            filiere = (payload.get("filiere") or "").strip()
        elif request.method == "GET":
            text = (request.GET.get("q") or "").strip()
            filiere = (request.GET.get("filiere") or "").strip()
        else:
            return JsonResponse({"error": "Method not allowed"}, status=405)

        if not text:
            return JsonResponse({"query": text, "filiere": filiere, "concepts": [], "collections": [], "resources": []})

        tokens = set(text.lower().split())
        scored = []
        for c in Concept.objects.all():
            corpus = f"{c.name} {c.description} {c.level}".lower().split()
            score = len(tokens.intersection(corpus))
            if score:
                scored.append((score, c))
        scored.sort(key=lambda x: -x[0])
        top = scored[:20]
        # Concepts payload
        concepts_payload = [
            {"id": c.id, "name": c.name, "description": c.description, "level": c.level, "score": s}
            for s, c in top
        ]
        # Collections related to matched concepts (optionally filter by filiere)
        concept_ids = [c.id for _, c in top]
        col_qs = Collection.objects.filter(concepts__id__in=concept_ids).distinct()
        if filiere:
            col_qs = col_qs.filter(filiere__iexact=filiere)
        collections_payload = []
        resources_payload = []
        # Simple scoring: number of matched concepts per collection
        matched_set = set(concept_ids)
        for col in col_qs:
            col_concept_ids = set(col.concepts.values_list("id", flat=True))
            overlap = len(matched_set.intersection(col_concept_ids))
            collections_payload.append({
                "id": col.id,
                "name": col.name,
                "description": col.description,
                "filiere": col.filiere,
                "level": col.level,
                "score": overlap,
            })
            # Aggregate resources
            for r in (col.resources or []):
                resources_payload.append(r)
        collections_payload.sort(key=lambda x: -x["score"])
        return JsonResponse({
            "query": text,
            "filiere": filiere,
            "concepts": concepts_payload,
            "collections": collections_payload,
            "resources": resources_payload,
        })
    except Exception as exc:
        # Print traceback to server logs and return JSON with trace when DEBUG=True
        import traceback
        tb = traceback.format_exc()
        print("[api_search_semantic] Exception:\n", tb)
        resp = {"error": "internal server error"}
        if getattr(settings, "DEBUG", False):
            resp["trace"] = tb
            resp["exception"] = str(exc)
        return JsonResponse(resp, status=500)


@csrf_exempt
def api_search_semantic_emb(request):
    """Semantic search using local sentence-transformers embeddings (if available).
    Accepts POST JSON {query, top_k, model} or GET ?q=&top_k=&model=
    Returns top concepts by cosine similarity on embeddings.
    """
    # Read inputs
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            payload = {}
        text = (payload.get('query') or payload.get('text') or '').strip()
        top_k = int(payload.get('top_k', 10) or 10)
        model = (payload.get('model') or 'sentence-transformers/all-MiniLM-L6-v2').strip()
    else:
        # For GET requests, redirect to the HTML tester page instead of returning raw JSON
        q = (request.GET.get('q') or '').strip()
        params = f"?q={q}" if q else ""
        return HttpResponseRedirect(f"/searchx/pages/api/search/semantic-emb/{params}")

    if not text:
        return JsonResponse({"query": text, "results": []})

    # Try embeddings first; otherwise fall back to token overlap similarity
    results = []
    q_vec = ai_utils.hf_get_embedding(text, model_name=model)
    if not isinstance(q_vec, str):
        for c in Concept.objects.all():
            c_text = f"{c.name}. {c.description}".strip()
            if not c_text:
                continue
            c_vec = ai_utils.hf_get_embedding(c_text, model_name=model)
            if isinstance(c_vec, str):
                # If a concept embedding fails, skip it (continue with others)
                continue
            denom = (np.linalg.norm(q_vec) * np.linalg.norm(c_vec)) or 1.0
            sim = float(np.dot(q_vec, c_vec) / denom)
            results.append({
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "similarity": round(sim, 4)
            })
    else:
        # Fallback: token-based similarity (no embeddings available)
        tokens = set(text.lower().split())
        for c in Concept.objects.all():
            corpus_tokens = set(f"{c.name} {c.description} {c.level}".lower().split())
            if not corpus_tokens:
                continue
            inter = len(tokens.intersection(corpus_tokens))
            if inter == 0:
                continue
            union = len(tokens.union(corpus_tokens)) or 1
            sim = inter / union
            results.append({
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "similarity": round(sim, 4)
            })

    # Sort local results by similarity
    results.sort(key=lambda r: -r['similarity'])

    # AI enrichment: get external or generated suggestions
    try:
        ai_suggestions = ai_utils.semantic_expand(text) or []
    except Exception:
        ai_suggestions = []

    # Map local results to unified format and apply weighting
    local_weight = 0.7
    ai_weight = 0.3

    local_items = []
    for r in results:
        base_rel = max(0.0, float(r.get('similarity') or 0.0))
        local_items.append({
            "id": r["id"],
            "title": f"Concept : {r['name']}",
            "description": r.get("description", ""),
            "source": "local_concept",
            "relevance": round(local_weight * base_rel, 4),
        })

    ai_items = []
    for it in ai_suggestions:
        title = str(it.get("title") or "").strip()
        if not title:
            continue
        desc = str(it.get("description") or "").strip()
        src = str(it.get("source") or it.get("source_type") or "external_ai").strip() or "external_ai"
        rel = it.get("relevance")
        try:
            rel = float(rel)
        except Exception:
            rel = 0.6
        rel = max(0.0, min(1.0, rel))
        ai_items.append({
            "title": title,
            "description": desc,
            "source": src,
            "relevance": round(ai_weight * rel, 4),
        })

    combined = local_items + ai_items
    combined.sort(key=lambda x: -x.get("relevance", 0.0))

    return JsonResponse({
        "query": text,
        "model": model,
        "results": combined[:top_k]
    })


@csrf_exempt
def api_search_similarity(request):
    # Support POST JSON or GET params
    payload = {}
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            payload = {}
        concept_id = payload.get("concept_id")
        resource_text = (payload.get("resource_text") or "").strip()
    elif request.method == "GET":
        concept_id = request.GET.get("concept_id")
        resource_text = (request.GET.get("resource_text") or "").strip()
    else:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    base_tokens = set()
    if concept_id:
        try:
            c = Concept.objects.get(pk=concept_id)
            base_tokens = set(f"{c.name} {c.description}".lower().split())
        except Concept.DoesNotExist:
            base_tokens = set()
    elif resource_text:
        base_tokens = set(resource_text.lower().split())
    else:
        return JsonResponse({"results": []})
    results = []
    for other in Concept.objects.all():
        tokens = set(f"{other.name} {other.description}".lower().split())
        inter = len(base_tokens.intersection(tokens))
        union = len(base_tokens.union(tokens)) or 1
        sim = inter / union
        if sim > 0:
            results.append({
                "id": other.id,
                "name": other.name,
                "description": other.description,
                "similarity": round(sim, 4),
            })
    results.sort(key=lambda r: -r["similarity"])
    return JsonResponse({"results": results[:20]})


# --------------------- Recommendations & Interactions ---------------------
 


@csrf_exempt
def api_log_interaction(request):
    """POST JSON {event_type, query, content_type, content_id, metadata}
    Saves a lightweight user interaction for behavior-based recommendations.
    """
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
    evt = (payload.get("event_type") or "").strip() or "click"
    ui = UserInteraction.objects.create(
        user=request.user if getattr(request, 'user', None) and request.user.is_authenticated else None,
        event_type=evt if evt in dict(UserInteraction.EVENT_CHOICES) else "click",
        query=payload.get("query", ""),
        content_type=payload.get("content_type", ""),
        content_id=str(payload.get("content_id", "")),
        metadata=payload.get("metadata") or {},
    )
    return JsonResponse({"ok": True, "id": ui.id})


@csrf_exempt
def api_recommendations(request):
    """GET/POST -> hybrid recommendations for collections/resources.
    Inputs (either GET params or POST JSON):
      - q: optional current query text
      - filiere: optional filter
      - top_k: default 10
      - alpha: weight for content similarity vs behavior (0..1, default 0.7)
    Output: {query, candidates: [...]} with per-item scores and components.
    """
    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            payload = {}
        q = (payload.get("q") or payload.get("query") or "").strip()
        filiere = (payload.get("filiere") or "").strip()
        top_k = int(payload.get("top_k", 10) or 10)
        alpha = float(payload.get("alpha", 0.7) or 0.7)
    else:
        q = (request.GET.get("q") or "").strip()
        filiere = (request.GET.get("filiere") or "").strip()
        top_k = int(request.GET.get("top_k") or 10)
        alpha = float(request.GET.get("alpha") or 0.7)

    # Candidate collections
    qs = Collection.objects.all()
    if filiere:
        qs = qs.filter(filiere__iexact=filiere)
    candidates = list(qs)

    # Build user behavior profile from recent interactions
    user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None
    recent = UserInteraction.objects.all()
    if user:
        recent = recent.filter(user=user)
    recent = recent.order_by('-created_at')[:200]

    # Behavior signals
    filiere_counts = Counter()
    concept_counts = Counter()
    queries = []
    for it in recent:
        if it.query:
            queries.append(it.query)
        # Extract any filiere or concept IDs from metadata if present
        meta = it.metadata or {}
        if meta.get('filiere'):
            filiere_counts[meta['filiere']] += 1
        if meta.get('concept_ids'):
            try:
                for cid in meta['concept_ids']:
                    concept_counts[str(cid)] += 1
            except Exception:
                pass

    # Content query: prefer current q; otherwise aggregate recent queries
    if not q and queries:
        q = ' \n '.join(queries[-10:])[:2000]

    # Precompute content vectors via pairwise similarity using existing util
    def to_text(col: Collection) -> str:
        concept_names = ', '.join(col.concepts.values_list('name', flat=True))
        resources_text = '\n'.join([str(r) for r in (col.resources or [])])
        return f"{col.name}. {col.description}. {col.filiere}. {col.level}. {concept_names}. {resources_text}"

    content_scores = {}
    if q:
        for col in candidates:
            content_scores[col.id] = float(ai_utils.compute_similarity(q, to_text(col)) or 0.0)
    else:
        for col in candidates:
            content_scores[col.id] = 0.0

    # Behavior scoring: boost by user's preferred filiere and concepts
    max_fil = max(filiere_counts.values()) if filiere_counts else 0
    max_con = max(concept_counts.values()) if concept_counts else 0

    def behavior_score(col: Collection) -> float:
        bf = 0.0
        if filiere_counts and col.filiere:
            bf += (filiere_counts.get(col.filiere, 0) / (max_fil or 1)) * 0.6
        # overlap concepts
        if concept_counts:
            col_cids = [str(cid) for cid in col.concepts.values_list('id', flat=True)]
            overlap = sum(concept_counts.get(cid, 0) for cid in col_cids)
            bf += (overlap / (max_con or 1)) * 0.4
        return bf

    # Final hybrid score
    results = []
    for col in candidates:
        cs = content_scores.get(col.id, 0.0)
        bs = behavior_score(col)
        score = alpha * cs + (1 - alpha) * bs
        results.append({
            "id": col.id,
            "name": col.name,
            "description": col.description,
            "filiere": col.filiere,
            "level": col.level,
            "content_score": round(cs, 4),
            "behavior_score": round(bs, 4),
            "score": round(score, 4),
            "resources": col.resources,
            "concepts": [
                {"id": c.id, "name": c.name, "level": c.level} for c in col.concepts.all()
            ],
        })

    results.sort(key=lambda r: -r["score"])
    return JsonResponse({
        "query": q,
        "filiere": filiere,
        "alpha": alpha,
        "results": results[:top_k]
    })


def api_trends(request):
    filiere = request.GET.get("filiere", "")
    qs = Collection.objects.all()
    if filiere:
        qs = qs.filter(filiere__iexact=filiere)
    data = []
    for col in qs:
        data.append({
            "collection_id": col.id,
            "collection": col.name,
            "filiere": col.filiere,
            "level": col.level,
            "concept_count": col.concepts.count(),
            "resource_count": len(col.resources),
        })
    data.sort(key=lambda x: (-(x["resource_count"]), -(x["concept_count"]), x["collection"]))
    return JsonResponse({"filiere": filiere, "trends": data[:20]})


# --------------------- AI Resource Endpoints ---------------------
from . import ai_utils



@csrf_exempt
def api_resource_transcribe(request, id: int):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
        
    if not request.FILES.get('audio'):
        return JsonResponse({"error": "No audio file provided"}, status=400)
    
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
        
    lang = (payload.get("lang") or "fr").strip()
    
    try:
        # Save uploaded file temporarily
        audio = request.FILES['audio']
        audio_path = f"/tmp/audio_{id}_{audio.name}"
        with open(audio_path, 'wb+') as destination:
            for chunk in audio.chunks():
                destination.write(chunk)
                
        # Process transcription
        transcript = ai_utils.transcribe_audio(audio_path, lang)
        
        # Clean up
        import os
        os.remove(audio_path)
        
        return JsonResponse({
            "id": id,
            "language": lang,
            "transcript": transcript
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_generate_text(request):
    """Génère du texte à partir d'un prompt (POST JSON {prompt, model, max_length})."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
    prompt = (payload.get("prompt") or payload.get("text") or "").strip()
    if not prompt:
        return JsonResponse({"error": "No prompt provided"}, status=400)
    model = payload.get("model") or "gpt2"
    try:
        out = ai_utils.hf_generate_text(prompt, model_name=model, max_length=int(payload.get("max_length", 100)))
        return JsonResponse({"prompt": prompt, "model": model, "generated": out})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def api_get_embedding(request):
    """Retourne un embedding (POST JSON {text, model})."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
    text = (payload.get("text") or payload.get("query") or "").strip()
    if not text:
        return JsonResponse({"error": "No text provided"}, status=400)
    model = payload.get("model") or "sentence-transformers/all-MiniLM-L6-v2"
    emb = ai_utils.hf_get_embedding(text, model_name=model)
    # Ensure JSON serializable
    if isinstance(emb, (list, tuple)):
        emb_list = list(emb)
    elif hasattr(emb, "tolist"):
        emb_list = emb.tolist()
    else:
        return JsonResponse({"error": str(emb)}, status=500)
    return JsonResponse({"model": model, "embedding": emb_list})


@csrf_exempt
def api_classify_text(request):
    """Classifie un texte (POST JSON {text, model})."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=400)
    try:
        payload = json.loads(request.body.decode("utf-8")) if request.body else {}
    except Exception:
        payload = {}
    text = (payload.get("text") or payload.get("query") or "").strip()
    if not text:
        return JsonResponse({"error": "No text provided"}, status=400)
    model = payload.get("model") or "distilbert-base-uncased-finetuned-sst-2-english"
    result = ai_utils.hf_classify_text(text, model_name=model)
    return JsonResponse({"model": model, "result": result})


@csrf_exempt
def api_extract_concepts(request):
    """POST JSON {texte: '...'} -> {concepts: [...]}
    Accepts 'text' or 'texte' keys.
    """
    # Support both POST (JSON body) and GET (?texte= or ?text=) for quick tests
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            payload = {}
        text = (payload.get('texte') or payload.get('text') or '').strip()
    elif request.method == 'GET':
        text = (request.GET.get('texte') or request.GET.get('text') or '').strip()
    else:
        return JsonResponse({'error': 'Method not allowed (use POST or GET)'}, status=405)
    if not text:
        return JsonResponse({'concepts': []})
    concepts = ai_utils.extract_concepts_from_text(text)
    return JsonResponse({'concepts': concepts})


@csrf_exempt
def api_ai_describe(request):
    """POST JSON {name, type?} -> {description}
    Generates a short French description (2-3 sentences) for a concept or collection name.
    Uses OpenAI via ai_utils.ai_answer_question when available; otherwise uses a simple fallback.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else {}
    except Exception:
        payload = {}
    name = (payload.get('name') or payload.get('title') or '').strip()
    obj_type = (payload.get('type') or 'concept').strip().lower()
    if not name:
        return JsonResponse({'description': ''})
    # Try AI answer first
    prompt = f"Rédige une courte description (2-3 phrases) en français pour le {obj_type}: '{name}'. Sois clair et pédagogique."
    desc = ai_utils.ai_answer_question(prompt)

    def synthesize_local_description() -> str:
        # Local, no-key synthesis from existing data
        # 1) collect top similar concepts
        sims = []
        try:
            for c in Concept.objects.all():
                base = f"{c.name} {c.description}".strip()
                s = float(ai_utils.compute_similarity(name, base) or 0.0)
                if s > 0:
                    sims.append((s, c))
        except Exception:
            sims = []
        sims.sort(key=lambda x: -x[0])
        top = [c for _, c in sims[:3]]
        # 2) build 2-3 sentences using available fields
        parts = []
        if obj_type == 'collection':
            # Try infer filiere/level from closest collection names
            try:
                col_sims = []
                for col in Collection.objects.all():
                    base = f"{col.name} {col.description} {col.filiere} {col.level}".strip()
                    s = float(ai_utils.compute_similarity(name, base) or 0.0)
                    if s > 0:
                        col_sims.append((s, col))
                col_sims.sort(key=lambda x: -x[0])
                if col_sims:
                    best_col = col_sims[0][1]
                    if best_col.filiere:
                        parts.append(f"Cette collection s'inscrit dans la filière {best_col.filiere} et vise le niveau {best_col.level or 'débutant'}.")
            except Exception:
                pass
        # Describe the concept/collection itself
        parts.append(f"{name} couvre les notions essentielles avec des explications progressives et des exemples concrets.")
        if top:
            # Add related notions synthesized from similar concepts
            related = ", ".join([t.name for t in top if t and t.name][:3])
            parts.append(f"Sujets liés: {related}.")
        # Include a distilled snippet from the closest description if any
        snippet = None
        for c in top:
            if c and c.description:
                snippet = c.description.strip().replace('\n', ' ')
                if len(snippet) > 180:
                    snippet = snippet[:177].rsplit(' ', 1)[0] + '...'
                break
        if snippet:
            parts.append(f"Résumé: {snippet}")
        return " ".join(parts[:3]) if parts else f"{name}: description synthétique indisponible."

    # If AI is unavailable or generic, use local synthesis
    if not desc or desc.lower().startswith('désolé'):
        desc = synthesize_local_description()

    return JsonResponse({'description': desc})


@csrf_exempt
def api_ai_ask(request):
    """POST JSON {question: '...'} -> {answer: '...'}
    Also supports GET ?q=... for quick browser testing.
    """
    if request.method == 'POST':
        try:
            payload = json.loads(request.body.decode('utf-8')) if request.body else {}
        except Exception:
            payload = {}
        question = (payload.get('question') or payload.get('q') or payload.get('ask') or '').strip()
        context = payload.get('context') or None
    elif request.method == 'GET':
        question = (request.GET.get('q') or request.GET.get('question') or '').strip()
        context = None
    else:
        return JsonResponse({'error': 'Method not allowed (use POST or GET)'}, status=405)

    if not question:
        return JsonResponse({'answer': ''})

    answer = ai_utils.ai_answer_question(question, context=context)

    # OpenAI-only mode: do not synthesize locally
    openai_only = getattr(settings, 'AI_OPENAI_ONLY', True)
    openai_key_set = bool(getattr(settings, 'OPENAI_API_KEY', None))
    openrouter_key_set = bool(getattr(settings, 'OPENROUTER_API_KEY', None))
    external_llm_available = openai_key_set or openrouter_key_set
    if openai_only:
        if not external_llm_available:
            guidance = (
               ""
            )
            return JsonResponse({'answer': guidance})
        if not answer or answer.lower().startswith('erreur ai') or answer.lower().startswith('erreur openrouter'):
            guidance = (
                "Erreur lors de l'appel du fournisseur IA (OpenAI/OpenRouter). Vérifiez:\n"
                "- La clé (OPENAI_API_KEY ou OPENROUTER_API_KEY) est valide et active\n"
                "- Le modèle (OPENAI_MODEL ou OPENROUTER_MODEL) est correct\n"
                "- La connexion réseau sortante est autorisée\n"
                "Puis réessayez."
            )
            return JsonResponse({'answer': guidance})

    def synthesize_local_answer(q: str) -> str:
        q_clean = (q or '').strip()
        # Try TF-IDF similarity for better ranking
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity
            # Build small corpus from Concepts and Collections
            concept_items = list(Concept.objects.all().only('name', 'description', 'level'))
            collection_items = list(Collection.objects.all().only('name', 'description', 'filiere', 'level'))
            docs = []
            meta = []
            for c in concept_items:
                docs.append(f"{c.name or ''}. {c.description or ''}. Niveau: {c.level or ''}")
                meta.append(('concept', c))
            for col in collection_items:
                docs.append(f"{col.name or ''}. {col.description or ''}. Filiere: {col.filiere or ''}. Niveau: {col.level or ''}")
                meta.append(('collection', col))
            if not docs:
                raise RuntimeError('empty-corpus')
            vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
            X = vectorizer.fit_transform(docs + [q_clean])
            q_vec = X[-1]
            sims = cosine_similarity(X[:-1], q_vec)
            ranked = sorted([(float(sims[i][0]), meta[i]) for i in range(len(meta))], key=lambda x: -x[0])
            topk = ranked[:5]
            # Compose concise answer
            lines = [f"Réponse synthétique sur \"{q_clean}\" (mode local):"]
            # Top concept hint
            top_concepts = [m[1] for score, m in topk if m[0] == 'concept'][:3]
            if top_concepts:
                names = ', '.join([c.name for c in top_concepts if getattr(c, 'name', None)])
                if names:
                    lines.append(f"Notions proches: {names}.")
            # Collections bullets
            top_cols = [m[1] for score, m in topk if m[0] == 'collection'][:3]
            if top_cols:
                lines.append("Collections pertinentes:")
                for col in top_cols:
                    frag = (col.description or '').strip()
                    if len(frag) > 140:
                        frag = frag[:137].rsplit(' ', 1)[0] + '...'
                    lines.append(f"- {col.name} ({col.filiere or 'général'}): {frag}")
            if len(lines) == 1:
                lines.append("Je n'ai pas trouvé de correspondance directe. Essaie de préciser le sujet.")
            return "\n".join(lines)
        except Exception:
            # Fallback to simple token overlap if sklearn not available
            ql = (q or '').lower()
            tokens = set(ql.split())
            scored = []
            for c in Concept.objects.all():
                corpus = f"{c.name} {c.description} {c.level}".lower().split()
                score = len(tokens.intersection(corpus))
                if score:
                    scored.append((score, c))
            scored.sort(key=lambda x: -x[0])
            top = [c for _, c in scored[:5]]
            col_qs = Collection.objects.filter(concepts__in=top).distinct()[:5]
            related = ', '.join([c.name for c in top]) if top else ''
            lines = [f"Réponse synthétique sur \"{q_clean}\" (mode local):"]
            if related:
                lines.append(f"Notions proches: {related}.")
            if col_qs:
                lines.append("Collections pertinentes:")
                for col in col_qs:
                    frag = (col.description or '').strip()
                    if len(frag) > 140:
                        frag = frag[:137].rsplit(' ', 1)[0] + '...'
                    lines.append(f"- {col.name} ({col.filiere or 'général'}): {frag}")
            if not top and not col_qs:
                lines.append("Je n'ai pas trouvé de correspondance directe. Essaie de préciser le sujet.")
            return "\n".join(lines)

    # If AI is unavailable or generic, produce a local synthesis
    if not answer or answer.lower().startswith('désolé') or answer.lower().startswith('erreur ai'):
        answer = synthesize_local_answer(question)

    return JsonResponse({'answer': answer})


def ai_test(request):
    """Lightweight health/test endpoint for AI subsystem.
    GET /ai/test/ -> {status: 'ok'} (adds debug info when DEBUG=True)
    """
    info = {"status": "ok"}
    if getattr(settings, "DEBUG", False):
        info["debug"] = True
        # Help developers quickly discover available AI API paths
        info["endpoints"] = [
            "/api/ai/generate/",
            "/api/ai/embedding/",
            "/api/ai/classify/",
            "/api/ai/extract-concepts/",
            "/api/ai/ask/",
        ]
        # Add runtime AI diagnostic (keys, dependencies)
        try:
            status = ai_utils.get_ai_status()
            info["ai_status"] = status
        except Exception as e:
            info["ai_status_error"] = str(e)
    return JsonResponse(info)


# --------------------- JSON CRUD APIs ---------------------
@csrf_exempt
def api_concepts_write(request, pk: int = None):
    if request.method == "POST" and pk is None:
        # Create
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        c = Concept(
            name=payload.get("name", "").strip(),
            description=payload.get("description", ""),
            level=payload.get("level", "") or "",
        )
        c.save()
        return JsonResponse({"id": c.id}, status=201)
    if pk is None:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    # With PK: GET is already handled by api_search/api_concepts list; here support PUT/DELETE and GET one if needed
    if request.method == "GET":
        try:
            c = Concept.objects.get(pk=pk)
        except Concept.DoesNotExist:
            raise Http404
        return JsonResponse({"id": c.id, "name": c.name, "description": c.description, "level": c.level})
    if request.method == "PUT":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        try:
            c = Concept.objects.get(pk=pk)
        except Concept.DoesNotExist:
            raise Http404
        c.name = payload.get("name", c.name)
        c.description = payload.get("description", c.description)
        c.level = payload.get("level", c.level)
        c.save()
        return JsonResponse({"ok": True})
    if request.method == "DELETE":
        try:
            c = Concept.objects.get(pk=pk)
        except Concept.DoesNotExist:
            raise Http404
        c.delete()
        return JsonResponse({"ok": True})
    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def api_collections_write(request, pk: int = None):
    # Helpers to parse resources and concepts
    def parse_resources(val):
        if val in (None, ""):
            return []
        if isinstance(val, (list, dict)):
            return val
        try:
            return json.loads(val)
        except Exception:
            return []

    if request.method == "POST" and pk is None:
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        col = Collection(
            name=payload.get("name", "").strip(),
            description=payload.get("description", ""),
            filiere=payload.get("filiere", ""),
            level=payload.get("level", ""),
            resources=parse_resources(payload.get("resources")),
        )
        col.save()
        concept_ids = payload.get("concept_ids") or []
        if concept_ids:
            col.concepts.set(Concept.objects.filter(id__in=concept_ids))
        return JsonResponse({"id": col.id}, status=201)
    if pk is None:
        return JsonResponse({"error": "Method not allowed"}, status=405)
    if request.method == "GET":
        try:
            col = Collection.objects.get(pk=pk)
        except Collection.DoesNotExist:
            raise Http404
        data = {
            "id": col.id,
            "name": col.name,
            "description": col.description,
            "filiere": col.filiere,
            "level": col.level,
            "concept_ids": list(col.concepts.values_list("id", flat=True)),
            "resources": col.resources,
        }
        return JsonResponse(data)
    if request.method == "PUT":
        try:
            payload = json.loads(request.body.decode("utf-8"))
        except Exception:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
        try:
            col = Collection.objects.get(pk=pk)
        except Collection.DoesNotExist:
            raise Http404
        col.name = payload.get("name", col.name)
        col.description = payload.get("description", col.description)
        col.filiere = payload.get("filiere", col.filiere)
        col.level = payload.get("level", col.level)
        if "resources" in payload:
            col.resources = parse_resources(payload.get("resources"))
        col.save()
        if "concept_ids" in payload:
            col.concepts.set(Concept.objects.filter(id__in=(payload.get("concept_ids") or [])))
        return JsonResponse({"ok": True})
    if request.method == "DELETE":
        try:
            col = Collection.objects.get(pk=pk)
        except Collection.DoesNotExist:
            raise Http404
        col.delete()
        return JsonResponse({"ok": True})
    return JsonResponse({"error": "Method not allowed"}, status=405)


# --------------------- New AI Utility Endpoints ---------------------



def api_demos_index(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_index.html", context)


def api_recommendations_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_recommendations.html", context)


def api_collections_write_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/api_collections_write.html", context)


def ui_navbar_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/ui_navbar.html", context)


def ui_footer_page(request):
    context = {}
    context = TemplateLayout().init(context)
    return render(request, "searchx/ui_footer.html", context)
