from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from .models import Report
from .forms import ReportForm
from .ai_tools import ai_analyze_report

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# ------------------------------
# EXPORT PDF
# ------------------------------
def export_reports_pdf(request):
    reports = Report.objects.all()

    # Create HttpResponse
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reports_dashboard.pdf"'

    # Create document
    doc = SimpleDocTemplate(response, pagesize=landscape(A4),
                            rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    styles = getSampleStyleSheet()

    # Title
    title = Paragraph("Tableau de bord des signalements", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    subtitle = Paragraph("Suivi des signalements avec détection AI, plagiat et contenu NSFW", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 24))

    # Table headers
    data = [["Titre", "Signalé par", "Plagiat", "NSFW", "Score IA", "Tags AI", "Risque"]]

    for r in reports:
        data.append([
            r.title,
            r.flagged_by,
            "Oui" if r.is_plagiarism else "Non",
            "Oui" if r.is_nsfw else "Non",
            f"{r.ai_confidence:.2f}",
            r.ai_flags or "Aucun",
            r.risk_label
        ])

    table = Table(data, repeatRows=1, colWidths=[120, 100, 50, 50, 60, 120, 60])
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4e73df")),  # header blue
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.whitesmoke, colors.lightgrey])
    ])
    table.setStyle(table_style)

    elements.append(table)

    # Footer with page numbers
    def add_page_number(canvas, doc):
        page_num = canvas.getPageNumber()
        canvas.setFont('Helvetica', 9)
        canvas.drawRightString(landscape(A4)[0] - 30, 15, f"Page {page_num}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
    return response

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
        data.append({
            'id': str(r.id),
            'title': r.title,
            'flagged_by': r.flagged_by,
            'is_plagiarism': r.is_plagiarism,
            'is_nsfw': r.is_nsfw,
            'ai_confidence': float(r.ai_confidence or 0.0),
            'ai_flags': r.ai_flags or "",
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

    # Unique AI tags
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
            ai_result = ai_analyze_report(
                title=data.get('title'),
                description=data.get('description'),
                resource_url=data.get('resource_url')
            )
            report = Report(
                title=data['title'],
                description=data['description'],
                resource_url=data['resource_url'],
                flagged_by=data['flagged_by'],
                is_plagiarism=data.get('is_plagiarism', ai_result.get('is_plagiarism', False)),
                is_nsfw=data.get('is_nsfw', ai_result.get('is_nsfw', False)),
                ai_confidence=data.get('ai_confidence', ai_result.get('ai_confidence', 0.0)),
                ai_flags=ai_result.get('ai_flags', ""),
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
            report.title = data['title']
            report.description = data.get('description', '')
            report.resource_url = data.get('resource_url', '')
            report.flagged_by = data['flagged_by']

            ai_result = ai_analyze_report(
                title=data.get('title'),
                description=data.get('description'),
                resource_url=data.get('resource_url')
            )

            report.is_plagiarism = data.get('is_plagiarism', ai_result.get('is_plagiarism', False))
            report.is_nsfw = data.get('is_nsfw', ai_result.get('is_nsfw', False))
            report.ai_confidence = data.get('ai_confidence', ai_result.get('ai_confidence', report.ai_confidence))
            report.ai_flags = ai_result.get('ai_flags', report.ai_flags)
            report.risk_label = ai_result.get('risk_label', report.risk_label)
            report.save()
            return redirect('moderation:report_list')
    else:
        initial_data = {
            'title': report.title,
            'description': report.description,
            'resource_url': report.resource_url,
            'flagged_by': report.flagged_by,
            'is_plagiarism': report.is_plagiarism,
            'is_nsfw': report.is_nsfw,
            'ai_confidence': report.ai_confidence
        }
        form = ReportForm(initial=initial_data)

    return render(request, 'moderation/report_form.html', {'form': form, 'report': report})

def report_delete(request, report_id):
    Report.objects.get(id=report_id).delete()
    return redirect('moderation:report_list')
