from rest_framework import viewsets
from .models import Resource
from .serializers import ResourceSerializer
from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404, JsonResponse
from .forms import ResourceForm
import os
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework.decorators import api_view
from django.utils.text import slugify
from urllib.parse import quote
from .ai_summary import generate_summary
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

# --------------------------
# Helper MongoEngine
# --------------------------
def get_resource_or_404(pk):
    try:
        return Resource.objects.get(id=pk)
    except Resource.DoesNotExist:
        raise Http404

# --------------------------
# DRF ViewSet
# --------------------------
class ResourceViewSet(viewsets.ModelViewSet):
    serializer_class = ResourceSerializer

    def get_queryset(self):
        return Resource.objects.all()

    def get_object(self):
        pk = self.kwargs.get('pk')
        return get_resource_or_404(pk)
        # Ici plus tard : lancer un traitement IA asynchrone
        # ex: process_resource(resource.id)

# --------------------------
# Views Front-Office / CRUD
# --------------------------
def resource_list(request):
    resources = Resource.objects.all()
    return render(request, 'resources/resource_list.html', {'resources': resources})



def front_office_resource_list(request):
    resources = Resource.objects.all()
    for res in resources:
        res.tags_list = res.tags if res.tags else []
    return render(request, 'resources/front_office_resource_list.html', {
        'resources': resources,
        'MEDIA_URL': settings.MEDIA_URL  # <-- ajouter ceci
    })


def resource_detail(request, pk):
    resource = get_resource_or_404(pk)
    tags = resource.tags if resource.tags else []

    file_url = None
    if resource.file:
        path = resource.file
        # Retirer MEDIA_URL si présent pour éviter double /media/
        if path.startswith(settings.MEDIA_URL):
            path = path[len(settings.MEDIA_URL):]
        # Retirer slash initial si présent
        if path.startswith('/'):
            path = path[1:]
        file_url = settings.MEDIA_URL + path  # ← pas de quote()

    return render(request, 'resources/resource_detail.html', {
        'resource': resource,
        'tags': tags,
        'file_url': file_url
    })


def front_office_resource_add(request):
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            tags = [t.strip() for t in data.get('tags', '').split(',') if t.strip()]

            uploaded_file = request.FILES['file']
            
            filename = slugify(os.path.splitext(uploaded_file.name)[0])
            extension = os.path.splitext(uploaded_file.name)[1].lower()
            file_path = os.path.join('resources', f"{filename}{extension}")
            saved_path = default_storage.save(file_path, uploaded_file)
            full_path = os.path.join(settings.MEDIA_ROOT, saved_path)

            # --- Extraction texte PDF ---
            content_text = ""
            if extension == '.pdf':
                try:
                    import pdfplumber
                    with pdfplumber.open(full_path) as pdf:
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                content_text += text + "\n"
                    print("Texte extrait PDF (pdfplumber) :", content_text[:200])

                    # Fallback OCR si PDF scanné
                    if not content_text.strip():
                        from pdf2image import convert_from_path
                        import pytesseract
                        pages = convert_from_path(full_path)
                        for page_img in pages:
                            content_text += pytesseract.image_to_string(page_img) + "\n"
                        print("Texte extrait PDF (OCR) :", content_text[:200])

                except Exception as e:
                    print(f"Erreur extraction texte PDF : {e}")

            # Créer la ressource
            resource = Resource(
                title=data['title'],
                description=data.get('description', ''),
                file=saved_path,
                resource_type=data['resource_type'],
                tags=tags,
                content_text=content_text
            )
            resource.save()

            return redirect('front_office_resource_list')
    else:
        form = ResourceForm()

    return render(request, 'resources/resource_ajout.html', {'form': form})

def resource_edit(request, pk):
    resource = get_resource_or_404(pk)
    if request.method == "POST":
        resource.title = request.POST.get('title')
        resource.description = request.POST.get('description', '')
        resource.resource_type = request.POST.get('resource_type', '')
        tags = request.POST.get('tags', '')
        resource.tags = [tag.strip() for tag in tags.split(',')] if tags else []
        resource.save()
        return redirect('front_office_resource_list')
    return render(request, 'resources/resource_edit.html', {'resource': resource})


def resource_delete(request, pk):
    resource = get_resource_or_404(pk)
    if request.method == "POST":
        resource.delete()
        return redirect('/api/list')
    return render(request, 'resources/resource_confirm_delete.html', {'resource': resource})


def generate_summary_view(request, resource_id):
    resource = get_resource_or_404(resource_id)

    if not resource.summary and getattr(resource, "content_text", None):
        summary = generate_summary(resource.content_text)
        resource.update(set__summary=summary)
        # Recharger l'objet depuis la DB pour avoir le summary à jour
        resource.reload()
    else:
        summary = resource.summary or "Aucun texte disponible pour générer un résumé."

    # Si c'est une requête AJAX, renvoyer JSON
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'summary': summary})

    return redirect('front_office_resource_detail', resource.id)

def get_resource_or_404(pk):
    try:
        return Resource.objects.get(pk=pk)  # pk fonctionne avec MongoEngine
    except Resource.DoesNotExist:
        raise Http404
