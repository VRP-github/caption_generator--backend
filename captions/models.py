from django.db import models
from django.core.validators import FileExtensionValidator


class CaptionRequest(models.Model):
    STYLE_CHOICES = [
        ('funny', 'Funny'),
        ('poetic', 'Poetic'),
        ('minimal', 'Minimal'),
        ('trendy', 'Trendy'),
    ]

    LENGTH_CHOICES = [
        ('short', 'Short'),
        ('medium', 'Medium'),
        ('long', 'Long'),
    ]

    image = models.ImageField(
        upload_to='uploads/',
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    style = models.CharField(max_length=10, choices=STYLE_CHOICES, default='trendy')
    length = models.CharField(max_length=10, choices=LENGTH_CHOICES, default='medium')
    people = models.CharField(max_length=200, blank=True, help_text="Who's in the photo?")
    location = models.CharField(max_length=200, blank=True, help_text="Where was this taken?")
    moment = models.TextField(blank=True, help_text="Special moment to highlight")
    sample_captions = models.TextField(blank=True, help_text="Your favorite captions for style reference")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Caption Request {self.id} - {self.created_at}"


class GeneratedCaption(models.Model):
    request = models.ForeignKey(CaptionRequest, on_delete=models.CASCADE, related_name='captions')
    caption_text = models.TextField()
    reason = models.TextField()
    order = models.IntegerField()
    has_bias_warning = models.BooleanField(default=False)
    bias_terms = models.JSONField(default=list)


class FilterRecommendation(models.Model):
    request = models.OneToOneField(CaptionRequest, on_delete=models.CASCADE, related_name='filter')
    filter_name = models.CharField(max_length=100)
    explanation = models.TextField()


class SongSuggestion(models.Model):
    request = models.ForeignKey(CaptionRequest, on_delete=models.CASCADE, related_name='songs')
    song_title_artist = models.CharField(max_length=200)
    order = models.IntegerField()
