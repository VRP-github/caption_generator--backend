import google.generativeai as genai
from django.conf import settings
from PIL import Image
import os
import re
from .models import GeneratedCaption, FilterRecommendation, SongSuggestion


class CaptionGeneratorService:
    def __init__(self):
        # Explicitly disable ADC and use only API key
        os.environ.pop('GOOGLE_APPLICATION_CREDENTIALS', None)
        os.environ.pop('GOOGLE_CLOUD_PROJECT', None)

        # Configure with API key only
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        self.banned_terms = ["crazy", "lame", "exotic", "tribal", "gyp"]

    def check_bias(self, text):
        flagged = [term for term in self.banned_terms if term.lower() in text.lower()]
        return flagged

    def parse_gemini_output(self, text):
        res_captions = []
        filter_str = ""
        filter_exp = ""
        songs = []

        # Split text into sections more reliably
        sections = re.split(r'\n(?=\d\.|\*\*\d\.)', text)

        current_caption = None
        current_reason = ""
        caption_count = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            lines = section.split('\n')
            first_line = lines[0].strip()

            # Check if this section starts with a numbered caption
            if re.match(r'^(\*\*)?[123]\.', first_line):
                caption_count += 1

                # Extract caption text
                caption_text = re.sub(r'^(\*\*)?[123]\.\s*(\*\*)?\s*', '', first_line)
                caption_text = caption_text.replace('"', '').replace('"', '').replace('"', '').replace('**', '').strip()

                # Look for reason in subsequent lines
                reason = ""
                for line in lines[1:]:
                    line = line.strip()
                    if line.lower().startswith('reason:'):
                        reason = line.replace('Reason:', '').replace('reason:', '').strip()
                    elif reason and not any(keyword in line.lower() for keyword in ['filter:', 'songs:', 'music:']):
                        reason += " " + line

                if caption_text:
                    res_captions.append({
                        "caption": caption_text,
                        "reason": reason
                    })

        # Parse the entire text for filter and songs using different approach
        text_lower = text.lower()

        # Extract filter information
        filter_patterns = [
            r'filter[:\s]+(.*?)(?=\n\n|\nreason|\nsongs|\nmusic|$)',
            r'recommended filter[:\s]+(.*?)(?=\n\n|\nreason|\nsongs|\nmusic|$)',
            r'instagram filter[:\s]+(.*?)(?=\n\n|\nreason|\nsongs|\nmusic|$)'
        ]

        for pattern in filter_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                filter_text = match.group(1).strip()
                # Split filter name and explanation
                filter_lines = filter_text.split('\n')
                filter_str = filter_lines[0].replace('*', '').replace('"', '').strip()
                if len(filter_lines) > 1:
                    filter_exp = ' '.join(filter_lines[1:]).strip()
                break

        # Extract songs more reliably
        song_patterns = [
            r'songs?[:\s]*\n((?:[-•]\s*.*\n?)*)',
            r'music[:\s]*\n((?:[-•]\s*.*\n?)*)',
            r'tracks?[:\s]*\n((?:[-•]\s*.*\n?)*)'
        ]

        for pattern in song_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                song_block = match.group(1)
                for line in song_block.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•'):
                        song_text = line[1:].strip().replace('"', '').replace('"', '').replace('"', '')
                        if song_text and len(song_text) > 3:
                            songs.append(song_text)
                break

        # Fallback: Look for songs that might be mixed with captions
        if not songs:
            all_lines = text.split('\n')
            for line in all_lines:
                line = line.strip()
                # Look for lines that look like songs (contain " - " and no "Reason:")
                if (' - ' in line and
                        not line.lower().startswith('reason:') and
                        not any(keyword in line.lower() for keyword in ['filter:', 'caption', 'explain'])):
                    song_text = line.replace('"', '').replace('"', '').replace('"', '').strip()
                    if song_text and len(song_text) > 3:
                        songs.append(song_text)

        return res_captions, filter_str, filter_exp, songs

    def generate_captions(self, caption_request):
        try:
            # Build prompt
            extra_details = ""
            if caption_request.people:
                extra_details += f" The following people are in the photo: {caption_request.people}."
            if caption_request.location:
                extra_details += f" The location of the photo is: {caption_request.location}."
            if caption_request.moment:
                extra_details += f" A special moment to highlight: {caption_request.moment}"

            custom_style = ""
            if caption_request.sample_captions:
                custom_style = f"\nBelow are my favorite captions. Try to match their tone and style:\n{caption_request.sample_captions}"

            # **IMPROVED PROMPT with clearer structure**
            gen_prompt = (
                f"Create three {caption_request.length}, {caption_request.style} Instagram captions for this image."
                f"{extra_details}\n\n"
                "Format your response EXACTLY like this:\n\n"
                "1. [First caption with hashtags and emojis]\n"
                "Reason: [Brief explanation]\n\n"
                "2. [Second caption with hashtags and emojis]\n"
                "Reason: [Brief explanation]\n\n"
                "3. [Third caption with hashtags and emojis]\n"
                "Reason: [Brief explanation]\n\n"
                "Filter: [Recommended Instagram filter name]\n"
                "[Filter explanation]\n\n"
                "Songs:\n"
                "- [Song Title - Artist Name]\n"
                "- [Song Title - Artist Name]\n"
                "- [Song Title - Artist Name]"
                f"{custom_style}"
            )

            # Open and process image
            image = Image.open(caption_request.image.path)
            response = self.model.generate_content([gen_prompt, image])
            output_text = response.text

            # **DEBUG: Show raw output**
            print("=== RAW GEMINI OUTPUT ===")
            print(output_text)
            print("=== END OUTPUT ===")

            # Parse response
            captions, filter_str, filter_exp, songs = self.parse_gemini_output(output_text)

            # **DEBUG: Show parsing results**
            print(f"Parsed captions: {len(captions)} items")
            for i, cap in enumerate(captions):
                print(f"Caption {i + 1}: {cap['caption'][:50]}...")
                print(f"  Reason: {cap['reason'][:50]}...")

            print(f"Parsed songs: {len(songs)} items")
            for i, song in enumerate(songs):
                print(f"Song {i + 1}: {song}")

            print(f"Filter: {filter_str}")

            # **FALLBACK: If no captions found, create basic ones**
            if not captions:
                print("No captions found in parsing, creating fallback captions...")
                # Try to extract any text that might be captions
                lines = output_text.split('\n')
                potential_captions = []

                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10 and not line.lower().startswith(
                            ('reason:', 'filter:', 'songs:', 'music:')):
                        # Remove quotes and clean up
                        clean_line = line.replace('"', '').replace('"', '').replace('"', '').strip()
                        if clean_line and '#' in clean_line:  # Likely a caption if it has hashtags
                            potential_captions.append({
                                "caption": clean_line,
                                "reason": "Caption extracted from AI response"
                            })

                # Use up to 3 potential captions
                captions = potential_captions[:3]
                print(f"Created {len(captions)} fallback captions")

            # Save captions
            for idx, cap_dict in enumerate(captions):
                bias_terms = self.check_bias(cap_dict["caption"])
                GeneratedCaption.objects.create(
                    request=caption_request,
                    caption_text=cap_dict["caption"],
                    reason=cap_dict["reason"],
                    order=idx + 1,
                    has_bias_warning=bool(bias_terms),
                    bias_terms=bias_terms
                )

            # Save filter recommendation
            if filter_str:
                FilterRecommendation.objects.create(
                    request=caption_request,
                    filter_name=filter_str,
                    explanation=filter_exp if filter_exp else ""
                )

            # Save song suggestions
            for idx, song in enumerate(songs):
                SongSuggestion.objects.create(
                    request=caption_request,
                    song_title_artist=song,
                    order=idx + 1
                )

            return True, "Captions generated successfully!"

        except Exception as e:
            print(f"Error in generate_captions: {str(e)}")
            import traceback
            traceback.print_exc()
            return False, str(e)
