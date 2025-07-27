from rest_framework import serializers
from .models import CaptionRequest, GeneratedCaption, FilterRecommendation, SongSuggestion


class GeneratedCaptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedCaption
        fields = ['id', 'caption_text', 'reason', 'order', 'has_bias_warning', 'bias_terms']


class FilterRecommendationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FilterRecommendation
        fields = ['filter_name', 'explanation']


class SongSuggestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SongSuggestion
        fields = ['song_title_artist', 'order']


class CaptionRequestSerializer(serializers.ModelSerializer):
    captions = GeneratedCaptionSerializer(many=True, read_only=True)
    filter = FilterRecommendationSerializer(read_only=True)
    songs = SongSuggestionSerializer(many=True, read_only=True)

    class Meta:
        model = CaptionRequest
        fields = [
            'id', 'image', 'style', 'length', 'people', 'location',
            'moment', 'sample_captions', 'created_at', 'captions', 'filter', 'songs'
        ]


class CaptionRequestCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaptionRequest
        fields = ['image', 'style', 'length', 'people', 'location', 'moment', 'sample_captions']

    def validate_image(self, value):
        if value.size > 10 * 1024 * 1024:  # 10MB limit
            raise serializers.ValidationError("Image file too large. Must be under 10MB.")
        return value
