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
from .signals import extract_text
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.styles import ParagraphStyle





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

            # Création de la ressource (content_text vide, le signal post_save s'en occupe)
            resource = Resource(
                title=data['title'],
                description=data.get('description', ''),
                file=saved_path,
                resource_type=data['resource_type'],
                tags=tags,
                content_text=""
            )
            resource.save()

            # 🔹 Appel manuel du signal pour générer texte et résumé
            extract_text(sender=Resource, instance=resource, created=True)

            print(f"💾 Ressource '{resource.title}' enregistrée et résumé généré.")
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


def download_summary_pdf(request, resource_id):
    resource = get_resource_or_404(resource_id)

    if not resource.summary:
        return HttpResponse("Aucun résumé disponible.", status=404)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=40, leftMargin=40,
                            topMargin=60, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    story = []

    # Personnalisation du titre
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.red,
        alignment=1,  # centré
        spaceAfter=20
    )
    story.append(Paragraph(resource.title, title_style))

    # Type de ressource
    type_style = ParagraphStyle(
        'TypeStyle',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.darkred,
        spaceAfter=15
    )
    story.append(Paragraph(f"Type de ressource : {resource.resource_type}", type_style))

    # Ajouter un encadré pour le résumé
    box_data = [[Paragraph(resource.summary.replace("\n", "<br/>"), styles['Normal'])]]
    box_table = Table(box_data, colWidths=[doc.width])
    box_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 1, colors.grey),
        ('BACKGROUND', (0,0), (-1,-1), colors.whitesmoke),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 10),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(box_table)
    story.append(Spacer(1, 12))

    # Générer le PDF
    doc.build(story)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{slugify(resource.title)}_résumé.pdf"'
    return response





    resource = get_resource_or_404(resource_id)

    if not resource.summary:
        return HttpResponse("Aucun résumé disponible.", status=404)

    # Créer un buffer en mémoire
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    textobject = pdf.beginText(40, height - 50)
    textobject.setFont("Helvetica", 12)

    # Ajouter le résumé ligne par ligne
    for line in resource.summary.split('\n'):
        textobject.textLine(line)
    
    pdf.drawText(textobject)
    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{resource.title}_résumé.pdf"'
    return response