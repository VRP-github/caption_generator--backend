from rest_framework import status, generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from .models import CaptionRequest
from .serializers import CaptionRequestSerializer, CaptionRequestCreateSerializer
from .services import CaptionGeneratorService


class CaptionRequestCreateView(generics.CreateAPIView):
    """
    Create a new caption request and generate captions
    """
    queryset = CaptionRequest.objects.all()
    serializer_class = CaptionRequestCreateSerializer
    parser_classes = (MultiPartParser, FormParser)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            # Save the caption request
            caption_request = serializer.save()

            # Generate captions using the service
            service = CaptionGeneratorService()
            success, message = service.generate_captions(caption_request)

            if success:
                # Return the full caption request with generated data
                response_serializer = CaptionRequestSerializer(caption_request)
                return Response({
                    'success': True,
                    'message': message,
                    'data': response_serializer.data
                }, status=status.HTTP_201_CREATED)
            else:
                # Delete the request if generation failed
                caption_request.delete()
                return Response({
                    'success': False,
                    'message': message,
                    'errors': []
                }, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({
                'success': False,
                'message': 'Validation errors occurred',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


class CaptionRequestDetailView(generics.RetrieveAPIView):
    """
    Retrieve a specific caption request with all generated data
    """
    queryset = CaptionRequest.objects.all()
    serializer_class = CaptionRequestSerializer
    lookup_field = 'id'

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })


class CaptionRequestListView(generics.ListAPIView):
    """
    List all caption requests (for history/admin purposes)
    """
    queryset = CaptionRequest.objects.all()
    serializer_class = CaptionRequestSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'count': queryset.count(),
            'data': serializer.data
        })


@api_view(['GET'])
def get_choices(request):
    """
    Get available choices for style and length
    """
    return Response({
        'success': True,
        'data': {
            'styles': [
                {'value': 'funny', 'label': 'Funny'},
                {'value': 'poetic', 'label': 'Poetic'},
                {'value': 'minimal', 'label': 'Minimal'},
                {'value': 'trendy', 'label': 'Trendy'},
            ],
            'lengths': [
                {'value': 'short', 'label': 'Short'},
                {'value': 'medium', 'label': 'Medium'},
                {'value': 'long', 'label': 'Long'},
            ]
        }
    })


@api_view(['POST'])
def regenerate_captions(request, caption_request_id):
    """
    Regenerate captions for an existing request
    """
    caption_request = get_object_or_404(CaptionRequest, id=caption_request_id)

    # Clear existing generated content
    caption_request.captions.all().delete()
    if hasattr(caption_request, 'filter'):
        caption_request.filter.delete()
    caption_request.songs.all().delete()

    # Generate new captions
    service = CaptionGeneratorService()
    success, message = service.generate_captions(caption_request)

    if success:
        serializer = CaptionRequestSerializer(caption_request)
        return Response({
            'success': True,
            'message': message,
            'data': serializer.data
        })
    else:
        return Response({
            'success': False,
            'message': message
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
def delete_caption_request(request, caption_request_id):
    """
    Delete a caption request and all associated data
    """
    caption_request = get_object_or_404(CaptionRequest, id=caption_request_id)
    caption_request.delete()

    return Response({
        'success': True,
        'message': 'Caption request deleted successfully'
    }, status=status.HTTP_204_NO_CONTENT)
