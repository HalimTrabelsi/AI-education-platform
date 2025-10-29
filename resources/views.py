from rest_framework import viewsets
from .models import Resource
from .serializers import ResourceSerializer
from django.shortcuts import render, get_object_or_404
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from .forms import ResourceForm



class ResourceViewSet(viewsets.ModelViewSet):
    queryset = Resource.objects.all()
    serializer_class = ResourceSerializer

    def perform_create(self, serializer):
        """
        Hook pour traitement futur IA ou stockage cloud.
        """
        resource = serializer.save()
        # Ici plus tard : lancer un traitement IA asynchrone
        # ex: process_resource(resource.id)


def resource_list(request):
    resources = Resource.objects.all()
    return render(request, 'resources/resource_list.html', {'resources': resources})



class ResourceUpdateView(UpdateView):
    model = Resource
    fields = ['title', 'description', 'resource_type', 'tags', 'file']
    template_name = 'resources/resource_form.html'
    success_url = reverse_lazy('resource-list')  # redirection après update

class ResourceDeleteView(DeleteView):
    model = Resource
    template_name = 'resources/resource_confirm_delete.html'
    success_url = reverse_lazy('resource-list')  # redirection après delete


def front_office_resource_list(request):
    """
    Affiche toutes les ressources dans le front-office (côté public).
    """
    resources = Resource.objects.all()
    for res in resources:
        res.tags_list = res.tags.split(',') if res.tags else []
    return render(request, 'resources/front_office_resource_list.html', {'resources': resources})
    
def resource_detail(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    # Sépare les tags avant d’envoyer au template
    tags = resource.tags.split(',') if resource.tags else []

    return render(request, 'resources/resource_detail.html', {
        'resource': resource,
        'tags': tags
    })
    

def front_office_resource_add(request):
    """
    Affiche le formulaire pour ajouter une ressource et gère la soumission.
    """
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('resource-list')  # redirige vers la liste front-office
    else:
        form = ResourceForm()

    return render(request, 'resources/resource_ajout.html', {'form': form})    

def resource_edit(request, pk):
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == "POST":
        resource.title = request.POST.get('title')
        resource.resource_type = request.POST.get('resource_type')
        tags = request.POST.get('tags', '').split(',')
        resource.tags = [tag.strip() for tag in tags]
        resource.save()
        return redirect('front_office_resource_list')

    return render(request, 'resources/resource_edit.html', {'resource': resource})
