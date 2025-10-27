from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import FeedItem
from .forms import FeedItemForm, FeedItemSearchForm

@login_required
def feed_list(request):
    """
    Liste des éléments du feed avec recherche et filtres
    """
    # Récupération des éléments actifs
    feed_items = FeedItem.objects.filter(is_active=True)
    
    # Formulaire de recherche
    search_form = FeedItemSearchForm(request.GET)
    
    if search_form.is_valid():
        # Recherche par texte
        search_query = search_form.cleaned_data.get('search_query')
        if search_query:
            feed_items = feed_items.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Filtre par type de contenu
        content_type = search_form.cleaned_data.get('content_type')
        if content_type:
            feed_items = feed_items.filter(content_type=content_type)
        
        # Tri
        ordering = search_form.cleaned_data.get('ordering')
        if ordering:
            feed_items = feed_items.order_by(ordering)
    
    # Pagination
    paginator = Paginator(feed_items, 10)  # 10 éléments par page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques globales
    stats = {
        'total_items': FeedItem.objects.filter(is_active=True).count(),
        'content_types': FeedItem.objects.filter(is_active=True).values(
            'content_type'
        ).distinct().count()
    }
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'stats': stats,
        'page_title': 'Feed - Fil d\'actualité'
    }
    
    return render(request, 'feed/feed_list.html', context)

@login_required
def feed_detail(request, pk):
    """
    Détail d'un élément du feed
    """
    feed_item = get_object_or_404(FeedItem, pk=pk)
    
    context = {
        'feed_item': feed_item,
        'page_title': feed_item.title
    }
    
    return render(request, 'feed/feed_detail.html', context)


# ============================================
# CREATE - Création
# ============================================

@login_required
def feed_create(request):
    """
    Créer un nouvel élément du feed
    """
    if request.method == 'POST':
        form = FeedItemForm(request.POST)
        if form.is_valid():
            feed_item = form.save(commit=False)
            feed_item.author = request.user
            feed_item.save()
            
            messages.success(
                request,
                f'✅ Élément "{feed_item.title}" créé avec succès !'
            )
            return redirect('feed:detail', pk=feed_item.pk)
        else:
            messages.error(
                request,
                '❌ Erreur dans le formulaire. Veuillez corriger les erreurs.'
            )
    else:
        form = FeedItemForm()
    
    context = {
        'form': form,
        'action': 'Créer',
        'page_title': 'Créer un élément du feed'
    }
    
    return render(request, 'feed/feed_form.html', context)


# ============================================
# UPDATE - Modification
# ============================================

@login_required
def feed_update(request, pk):
    """
    Modifier un élément du feed
    """
    feed_item = get_object_or_404(FeedItem, pk=pk)
    
    # Vérifier que l'utilisateur est l'auteur ou admin
    if feed_item.author != request.user and not request.user.is_staff:
        messages.error(
            request,
            '❌ Vous n\'avez pas la permission de modifier cet élément.'
        )
        return redirect('feed:detail', pk=pk)
    
    if request.method == 'POST':
        form = FeedItemForm(request.POST, instance=feed_item)
        if form.is_valid():
            feed_item = form.save()
            
            messages.success(
                request,
                f'✅ Élément "{feed_item.title}" modifié avec succès !'
            )
            return redirect('feed:detail', pk=feed_item.pk)
        else:
            messages.error(
                request,
                '❌ Erreur dans le formulaire. Veuillez corriger les erreurs.'
            )
    else:
        form = FeedItemForm(instance=feed_item)
    
    context = {
        'form': form,
        'feed_item': feed_item,
        'action': 'Modifier',
        'page_title': f'Modifier: {feed_item.title}'
    }
    
    return render(request, 'feed/feed_form.html', context)


# ============================================
# DELETE - Suppression
# ============================================

@login_required
def feed_delete(request, pk):
    """
    Supprimer un élément du feed
    """
    feed_item = get_object_or_404(FeedItem, pk=pk)
    
    # Vérifier que l'utilisateur est l'auteur ou admin
    if feed_item.author != request.user and not request.user.is_staff:
        messages.error(
            request,
            '❌ Vous n\'avez pas la permission de supprimer cet élément.'
        )
        return redirect('feed:detail', pk=pk)
    
    if request.method == 'POST':
        title = feed_item.title
        feed_item.delete()
        
        messages.success(
            request,
            f'✅ Élément "{title}" supprimé avec succès.'
        )
        return redirect('feed:list')
    
    context = {
        'feed_item': feed_item,
        'page_title': f'Supprimer: {feed_item.title}'
    }
    
    return render(request, 'feed/feed_confirm_delete.html', context)