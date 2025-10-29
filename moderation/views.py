from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from .models import Report
from .forms import ReportForm
from .ai_tools import ai_analyze_report
from django.views.decorators.csrf import csrf_exempt

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Report
from .forms import ReportForm
from .ai_tools import ai_analyze_report
import json
# ------------------------------
# EXPORT PDF WITHOUT AI TAGS
# ------------------------------
def export_reports_pdf(request):
    reports = Report.objects.all()

    # Create HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reports_dashboard.pdf"'

    # Create document
    doc = SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=20, leftMargin=20, topMargin=30, bottomMargin=30
    )

    elements = []
    styles = getSampleStyleSheet()

    # Title and subtitle
    elements.append(Paragraph("Tableau de bord des signalements", styles['Title']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(
        "Suivi des signalements avec détection AI, plagiat et contenu NSFW",
        styles['Normal']
    ))
    elements.append(Spacer(1, 16))

    # Table headers (Risque column removed)
    data = [["Titre", "Signalé par", "Plagiat", "NSFW", "Score IA"]]

    for r in reports:
        data.append([
            r.title,
            r.flagged_by,
            "Oui" if r.is_plagiarism else "Non",
            "Oui" if r.is_nsfw else "Non",
            f"{r.ai_confidence:.2f}"
        ])

    # Adjust column widths proportionally
    col_widths = [300, 150, 60, 60, 80]

    table = Table(data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4e73df")),  # header background
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # header text
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # center all except first column
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # left-align "Titre"
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
    ]))

    elements.append(table)



    # Footer with page numbers
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(landscape(A4)[0] - 20, 15, f"Page {page_num}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return response
# views.py (excerpt)
@csrf_exempt
def verify_ai(request):
    if request.method != "POST":
        return JsonResponse({"error": "Méthode non autorisée"}, status=405)
    try:
        data = json.loads(request.body)
        title = data.get("title", "")
        description = data.get("description", "")
        result = ai_analyze_report(title, description)
        return JsonResponse({
            "ai_confidence": result["ai_confidence"],
            "ai_flags": result["ai_flags"],
            "is_nsfw": result["is_nsfw"],
            "is_plagiarism": result["is_plagiarism"],
            "risk_label": result["risk_label"]
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# ------------------------------
# DASHBOARD
# ------------------------------
def report_list(request):
    return render(request, 'moderation/report_list.html')

# ------------------------------
# DATA ENDPOINT
# ------------------------------
def report_data(request):
    query = request.GET.get('q', '').strip()
    sort_order = request.GET.get('sort', 'asc')
    page_number = int(request.GET.get('page', 1))

    reports_qs = Report.objects(title__icontains=query) if query else Report.objects.all()
    reports_qs = reports_qs.order_by('title' if sort_order == 'asc' else '-title')

    paginator = Paginator(list(reports_qs), 5)
    page_obj = paginator.get_page(page_number)

    data = []
    for r in page_obj:
        ai_tags = []
        if r.ai_confidence and r.ai_confidence > 0.4:
            ai_tags.append("Signalements")
        if r.is_plagiarism:
            ai_tags.append("anti-plagiat")
        if r.is_nsfw or (r.ai_confidence and r.ai_confidence > 0.55):
            ai_tags.append("détection IA de triche / NSFW")

        data.append({
            'id': str(r.id),
            'title': r.title,
            'flagged_by': r.flagged_by,
            'is_plagiarism': r.is_plagiarism,
            'is_nsfw': r.is_nsfw,
            'ai_confidence': float(r.ai_confidence or 0.0),
            'ai_flags': ", ".join(ai_tags) if ai_tags else "Aucun",
            'risk_label': r.risk_label,
            'created_at': r.created_at.strftime('%Y-%m-%d %H:%M:%S')
        })

    return JsonResponse({
        'reports': data,
        'page_number': page_obj.number,
        'num_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })

# ------------------------------
# STATS ENDPOINT
# ------------------------------
def report_stats(request):
    reports = Report.objects.all()
    total = reports.count()
    plagiarism_count = reports.filter(is_plagiarism=True).count()
    nsfw_count = reports.filter(is_nsfw=True).count()
    risky_count = reports.filter(risk_label="Risky").count()
    safe_count = reports.filter(risk_label="Safe").count()

    all_tags = []
    for r in reports:
        if r.ai_flags:
            all_tags += [t.strip() for t in r.ai_flags.split(',')]
    unique_tags = len(set(all_tags))

    return JsonResponse({
        "total": total,
        "plagiarism_count": plagiarism_count,
        "nsfw_count": nsfw_count,
        "risky_count": risky_count,
        "safe_count": safe_count,
        "unique_tags": unique_tags
    })

# ------------------------------
# CRUD
# ------------------------------
def report_create(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            # Analyze AI
            ai_result = ai_analyze_report(
                title=data.get('title'),
                description=data.get('description'),
                resource_url=data.get('resource_url')
            )

            ai_conf = ai_result.get('ai_confidence', 0.0) or 0.0
            is_nsfw = ai_result.get('is_nsfw', False)
            is_plagiarism = ai_result.get('is_plagiarism', False)

            tags = []
            if ai_conf > 0.4:
                tags.append("Signalements")
            if ai_conf > 0.55 or is_nsfw:
                tags.append("détection IA de triche / NSFW")
                is_nsfw = True
            if ai_conf > 0.7:
                tags.append("Risque élevé")
            # Check for duplicates using MongoEngine
            if Report.objects(title=data.get('title')).first() or Report.objects(resource_url=data.get('resource_url')).first():
                tags.append("anti-plagiat")
                is_plagiarism = True

            report = Report(
                title=data['title'],
                description=data['description'],
                resource_url=data['resource_url'],
                flagged_by=data['flagged_by'],
                ai_confidence=ai_conf,
                is_plagiarism=is_plagiarism,
                is_nsfw=is_nsfw,
                ai_flags=", ".join(tags) if tags else "",
                risk_label=ai_result.get('risk_label', "Safe")
            )
            report.save()
            return redirect('moderation:report_list')
    else:
        form = ReportForm()

    return render(request, 'moderation/report_form.html', {'form': form})


def report_update(request, report_id):
    report = Report.objects.get(id=report_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            ai_result = ai_analyze_report(
                title=data.get('title'),
                description=data.get('description'),
                resource_url=data.get('resource_url')
            )

            tags = []
            ai_conf = data.get('ai_confidence', ai_result.get('ai_confidence', report.ai_confidence)) or 0.0
            is_plagiarism = data.get('is_plagiarism', report.is_plagiarism)
            is_nsfw = data.get('is_nsfw', report.is_nsfw)

            if ai_conf > 0.4:
                tags.append("Signalements")
            if ai_conf > 0.55 or is_nsfw:
                tags.append("détection IA de triche / NSFW")
                is_nsfw = True
            if ai_conf > 0.7:
                tags.append("Risque élevé")
            if await_check_duplicate(data.get('title'), data.get('resource_url')):
                tags.append("anti-plagiat")
                is_plagiarism = True

            report.title = data['title']
            report.description = data['description']
            report.resource_url = data['resource_url']
            report.flagged_by = data['flagged_by']
            report.ai_confidence = ai_conf
            report.is_plagiarism = is_plagiarism
            report.is_nsfw = is_nsfw
            report.ai_flags = ", ".join(tags) if tags else ""
            report.risk_label = ai_result.get('risk_label', report.risk_label)
            report.save()
            return redirect('moderation:report_list')
    else:
        form = ReportForm(initial={
            'title': report.title,
            'description': report.description,
            'resource_url': report.resource_url,
            'flagged_by': report.flagged_by,
            'is_plagiarism': report.is_plagiarism,
            'is_nsfw': report.is_nsfw,
            'ai_confidence': report.ai_confidence,
            'ai_flags': report.ai_flags
        })

    return render(request, 'moderation/report_form.html', {'form': form, 'report': report})


def await_check_duplicate(title, url):
    """Return True if a report exists with same title or url"""
    if not title and not url:
        return False
    return Report.objects(title=title) or Report.objects(resource_url=url)


def report_delete(request, report_id):
    Report.objects.get(id=report_id).delete()
    return redirect('moderation:report_list')