import os

from django.conf import settings
from django.contrib import messages
from django.core.files.storage import default_storage
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.text import slugify

try:
    from rest_framework import viewsets
except ImportError:  # pragma: no cover - optional dependency
    viewsets = None

from accounts.decorators import role_required
from web_project import TemplateLayout

from .ai_summary import generate_summary
from .forms import ResourceForm
from .models import Resource, RESOURCE_TYPES

if viewsets:
    from .serializers import ResourceSerializer


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _layout_context(data=None):
    return TemplateLayout().init(data or {})


def get_resource_or_404(pk):
    try:
        return Resource.objects.get(id=pk)
    except Resource.DoesNotExist:
        raise Http404


def _process_uploaded_file(uploaded_file):
    filename = slugify(os.path.splitext(uploaded_file.name)[0])
    extension = os.path.splitext(uploaded_file.name)[1].lower()
    file_path = os.path.join("resources", f"{filename}{extension}")
    saved_path = default_storage.save(file_path, uploaded_file)
    full_path = os.path.join(settings.MEDIA_ROOT, saved_path)
    return saved_path, full_path, extension


def _extract_pdf_text(full_path):
    content_text = ""
    try:
        import pdfplumber

        with pdfplumber.open(full_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    content_text += text + "\n"

        if not content_text.strip():
            from pdf2image import convert_from_path
            import pytesseract

            pages = convert_from_path(full_path)
            for page_img in pages:
                content_text += pytesseract.image_to_string(page_img) + "\n"
    except Exception:
        pass
    return content_text


def _create_resource_from_form(form):
    data = form.cleaned_data
    tags = [t.strip() for t in data.get("tags", "").split(",") if t.strip()]
    uploaded_file = form.files["file"]

    saved_path, full_path, extension = _process_uploaded_file(uploaded_file)
    content_text = _extract_pdf_text(full_path) if extension == ".pdf" else ""

    resource = Resource(
        title=data["title"],
        description=data.get("description", ""),
        file=saved_path,
        resource_type=data["resource_type"],
        tags=tags,
        content_text=content_text,
    )
    resource.save()
    return resource


# ---------------------------------------------------------------------------
# DRF viewset (optional)
# ---------------------------------------------------------------------------
if viewsets:

    class ResourceViewSet(viewsets.ModelViewSet):
        serializer_class = ResourceSerializer

        def get_queryset(self):
            return Resource.objects.all()

        def get_object(self):
            pk = self.kwargs.get("pk")
            return get_resource_or_404(pk)


# ---------------------------------------------------------------------------
# Back-office views (teachers / admins)
# ---------------------------------------------------------------------------
@role_required("teacher", "admin")
def resource_list(request):
    resources = list(Resource.objects.order_by("-uploaded_at"))
    resource_types = {
        getattr(res, "resource_type", "") or "Autre" for res in resources
    }
    context = _layout_context(
        {
            "resources": resources,
            "total_resources": len(resources),
            "resource_types_count": len(resource_types),
            "media_url": settings.MEDIA_URL,
        }
    )
    context["page_title"] = "Gestion des ressources"
    return render(request, "resources/resource_list.html", context)


@role_required("teacher", "admin")
def resource_add(request):
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            _create_resource_from_form(form)
            messages.success(request, "Resource created successfully.")
            return redirect("resources:list")
        messages.error(request, "Please correct the form errors.")
    else:
        form = ResourceForm()

    context = _layout_context({"form": form})
    context["page_title"] = "Ajouter une ressource"
    return render(request, "resources/resource_ajout.html", context)


@role_required("teacher", "admin")
def resource_edit(request, pk):
    resource = get_resource_or_404(pk)

    if request.method == "POST":
        resource.title = request.POST.get("title")
        resource.description = request.POST.get("description", "")
        resource.resource_type = request.POST.get("resource_type", "")
        tags = request.POST.get("tags", "")
        resource.tags = [tag.strip() for tag in tags.split(",")] if tags else []
        resource.save()
        messages.success(request, "Resource updated.")
        return redirect("resources:list")

    context = _layout_context({"resource": resource, "resource_types": RESOURCE_TYPES})
    context["page_title"] = "Modifier la ressource"
    return render(request, "resources/resource_edit.html", context)


@role_required("teacher", "admin")
def resource_delete(request, pk):
    resource = get_resource_or_404(pk)
    if request.method == "POST":
        resource.delete()
        messages.success(request, "Resource deleted.")
        return redirect("resources:list")

    context = _layout_context({"resource": resource})
    context["page_title"] = "Supprimer la ressource"
    return render(request, "resources/resource_confirm_delete.html", context)


# ---------------------------------------------------------------------------
# Front-office views (students / teachers / admins)
# ---------------------------------------------------------------------------
@role_required("student", "teacher", "admin")
def front_office_resource_list(request):
    resources = Resource.objects.order_by("-uploaded_at")
    for res in resources:
        res.tags_list = res.tags if res.tags else []

    context = _layout_context(
        {
            "resources": resources,
            "media_url": settings.MEDIA_URL,
        }
    )
    context["page_title"] = "Cours disponibles"
    return render(request, "resources/front_office_resource_list.html", context)


@role_required("student", "teacher", "admin")
def resource_detail(request, pk):
    resource = get_resource_or_404(pk)
    tags = resource.tags if resource.tags else []

    file_url = None
    if resource.file:
        path = resource.file
        if path.startswith(settings.MEDIA_URL):
            path = path[len(settings.MEDIA_URL) :]
        if path.startswith("/"):
            path = path[1:]
        file_url = settings.MEDIA_URL + path

    context = _layout_context(
        {
            "resource": resource,
            "tags": tags,
            "file_url": file_url,
            "quiz_url": reverse("quiz:take", args=[resource.id]) if resource else None,
        }
    )
    context["page_title"] = resource.title
    return render(request, "resources/resource_detail.html", context)


# ---------------------------------------------------------------------------
# AI Summary API
# ---------------------------------------------------------------------------
@role_required("student", "teacher", "admin")
def generate_summary_view(request, resource_id):
    resource = get_resource_or_404(resource_id)

    if request.method != "POST":
        return redirect("resources:detail", resource_id)

    if not resource.summary and getattr(resource, "content_text", None):
        summary = generate_summary(resource.content_text)
        resource.update(set__summary=summary)
        resource.reload()
    else:
        summary = resource.summary or "No text available to generate a summary."

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"summary": summary})

    return redirect("resources:detail", resource.id)
