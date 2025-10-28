from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from bson import ObjectId
from bson.errors import InvalidId
from .models import FeedItem
from .forms import FeedItemForm, FeedItemSearchForm


def feed_list(request):
    """
    Liste des éléments du feed avec recherche et filtres
    """
    # Récupérer tous les items actifs
    feed_items = FeedItem.objects(is_active=True)
    
    search_form = FeedItemSearchForm(request.GET)
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query')
        if search_query:
            # Recherche dans le titre et la description
            feed_items = feed_items.filter(
                title__icontains=search_query
            ) | feed_items.filter(
                description__icontains=search_query
            )
        
        content_type = search_form.cleaned_data.get('content_type')
        if content_type:
            feed_items = feed_items.filter(content_type=content_type)
        
        ordering = search_form.cleaned_data.get('ordering')
        if ordering:
            feed_items = feed_items.order_by(ordering)
    
    # Pagination
    feed_items_list = list(feed_items)
    paginator = Paginator(feed_items_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistiques
    stats = {
        'total_items': FeedItem.objects(is_active=True).count(),
        'content_types': len(FeedItem.objects(is_active=True).distinct('content_type'))
    }
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'stats': stats,
        'page_title': 'Feed - Fil d\'actualité'
    }
    
    return render(request, 'feed/feed_list.html', context)


def feed_detail(request, pk):
    """
    Détail d'un élément du feed
    """
    try:
        feed_item = FeedItem.objects.get(id=pk)
    except (FeedItem.DoesNotExist, InvalidId):
        messages.error(request, '❌ Élément introuvable.')
        return redirect('feed:list')
    
    context = {
        'feed_item': feed_item,
        'page_title': feed_item.title
    }
    
    return render(request, 'feed/feed_detail.html', context)


def feed_create(request):
    """
    Créer un nouvel élément du feed
    """
    if request.method == 'POST':
        form = FeedItemForm(request.POST)
        if form.is_valid():
            # Récupérer l'ID utilisateur MongoDB depuis la session
            user_id = request.session.get('_auth_user_id')
            
            if not user_id:
                messages.error(
                    request,
                    '❌ Vous devez être connecté pour créer un élément.'
                )
                return redirect('accounts:login')
            
            try:
                # Créer le FeedItem MongoDB
                feed_item = FeedItem(
                    title=form.cleaned_data['title'],
                    description=form.cleaned_data['description'],
                    content_type=form.cleaned_data['content_type'],
                    deadline=form.cleaned_data.get('deadline'),
                    is_active=form.cleaned_data.get('is_active', True),
                    author_id=str(user_id)
                )
                feed_item.save()
                
                messages.success(
                    request,
                    f'✅ Élément "{feed_item.title}" créé avec succès !'
                )
                return redirect('feed:detail', pk=str(feed_item.id))
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Erreur lors de la sauvegarde : {str(e)}'
                )
                print(f"ERROR: {e}")
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


def feed_update(request, pk):
    """
    Modifier un élément du feed
    """
    try:
        feed_item = FeedItem.objects.get(id=pk)
    except (FeedItem.DoesNotExist, InvalidId):
        messages.error(request, '❌ Élément introuvable.')
        return redirect('feed:list')
    
    # Vérifier que l'utilisateur est l'auteur
    user_id = request.session.get('_auth_user_id')
    if str(feed_item.author_id) != str(user_id):
        messages.error(
            request,
            '❌ Vous n\'avez pas la permission de modifier cet élément.'
        )
        return redirect('feed:detail', pk=pk)
    
    if request.method == 'POST':
        form = FeedItemForm(request.POST)
        if form.is_valid():
            try:
                # Mettre à jour les champs
                feed_item.title = form.cleaned_data['title']
                feed_item.description = form.cleaned_data['description']
                feed_item.content_type = form.cleaned_data['content_type']
                feed_item.deadline = form.cleaned_data.get('deadline')
                feed_item.is_active = form.cleaned_data.get('is_active', True)
                feed_item.save()
                
                messages.success(
                    request,
                    f'✅ Élément "{feed_item.title}" modifié avec succès !'
                )
                return redirect('feed:detail', pk=str(feed_item.id))
            except Exception as e:
                messages.error(
                    request,
                    f'❌ Erreur lors de la modification : {str(e)}'
                )
        else:
            messages.error(
                request,
                '❌ Erreur dans le formulaire. Veuillez corriger les erreurs.'
            )
    else:
        # Pré-remplir le formulaire avec les données existantes
        form = FeedItemForm(initial={
            'title': feed_item.title,
            'description': feed_item.description,
            'content_type': feed_item.content_type,
            'deadline': feed_item.deadline,
            'is_active': feed_item.is_active,
        })
    
    context = {
        'form': form,
        'feed_item': feed_item,
        'action': 'Modifier',
        'page_title': f'Modifier: {feed_item.title}'
    }
    
    return render(request, 'feed/feed_form.html', context)


def feed_delete(request, pk):
    """
    Supprimer un élément du feed
    """
    try:
        feed_item = FeedItem.objects.get(id=pk)
    except (FeedItem.DoesNotExist, InvalidId):
        messages.error(request, '❌ Élément introuvable.')
        return redirect('feed:list')
    
    # Vérifier que l'utilisateur est l'auteur
    user_id = request.session.get('_auth_user_id')
    if str(feed_item.author_id) != str(user_id):
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