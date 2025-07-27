from django.urls import path
from . import views

urlpatterns = [
    # Main endpoints
    path('api/captions/generate/', views.CaptionRequestCreateView.as_view(), name='generate-captions'),
    path('api/captions/<int:id>/', views.CaptionRequestDetailView.as_view(), name='caption-detail'),
    path('api/captions/', views.CaptionRequestListView.as_view(), name='caption-list'),

    # Utility endpoints
    path('api/choices/', views.get_choices, name='get-choices'),
    path('api/captions/<int:caption_request_id>/regenerate/', views.regenerate_captions, name='regenerate-captions'),
    path('api/captions/<int:caption_request_id>/delete/', views.delete_caption_request, name='delete-caption-request'),
]
