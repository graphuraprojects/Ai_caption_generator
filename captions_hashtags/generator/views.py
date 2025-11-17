from django.shortcuts import render
from django.conf import settings
from django.http import JsonResponse, HttpResponse
import json
from google import genai
import csv
from io import StringIO, BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

# Initialize Gemini client
client = genai.Client(api_key=getattr(settings, "GEMINI_API_KEY", None))

def input(request):
    return render(request, 'generator/input.html')

def home(request):
    return render(request, 'generator/home.html')

def about(request):
    return render(request, 'generator/about.html')


def generate_gemini_suggestions(product_name, brand_name, description,
                                target_audience, tone, length_preference, platform):
    # Normalize platform name
    platform_lower = platform.lower()

    # Platform style and hashtags count
    if platform_lower in ['instagram']:
        style = "Use emojis, storytelling, and include hashtags."
        hashtags_count = 5
    elif platform_lower in ['x', 'twitter', 'x (twitter)']:
        style = "Short, punchy, include 1–3 hashtags."
        hashtags_count = 3
    elif platform_lower == 'linkedin':
        style = "Professional tone, short paragraphs, no hashtags."
        hashtags_count = 0
    elif platform_lower == 'facebook':
        style = "Casual tone, include CTA, no hashtags."
        hashtags_count = 0
    else:
        style = ""
        hashtags_count = 0

    # Caption length instruction
    if length_preference.lower() == "short":
        length_instruction = "Keep the caption under 15 words."
    elif length_preference.lower() == "medium":
        length_instruction = "Keep the caption between 15–30 words."
    elif length_preference.lower() == "long":
        length_instruction = "Write a detailed caption around 50–80 words."
    else:
        length_instruction = "Use a natural length for the caption."

    # Final prompt
    prompt = (
        f"Generate 1 creative caption for {platform}.\n"
        f"Product: {product_name}\n"
        f"Brand: {brand_name}\n"
        f"Description: {description}\n"
        f"Target Audience: {target_audience}\n"
        f"Tone: {tone}\n"
        f"Style/Instructions: {style}\n"
        f"{length_instruction}\n"
        f"Include up to {hashtags_count} hashtags if applicable.\n\n"
        "Return ONLY a JSON object with keys 'caption' and 'hashtags' (as a list)."
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text or ""
        text = text.strip()

        # Clean code blocks if Gemini returns them
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = "\n".join(text.split("\n")[:-1])

        try:
            suggestion = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            suggestion = {}

        if "caption" not in suggestion:
            suggestion["caption"] = "AI-generated caption"
        if "hashtags" not in suggestion or not isinstance(suggestion["hashtags"], list):
            suggestion["hashtags"] = []

        return suggestion

    except Exception:
        return {"caption": "Sample Caption", "hashtags": []}


def generate_captions(request):
    results = request.session.get('results', {})

    if request.method == 'POST':
        form_data = request.session.get('form_data', {})

        # AJAX regenerate
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            platform = request.POST.get('regenerate_platform')
            index = int(request.POST.get('suggestion_index', 0))

            new_suggestion = generate_gemini_suggestions(
                form_data.get('product_name', ''),
                form_data.get('brand_name', ''),
                form_data.get('description', ''),
                form_data.get('target_audience', ''),
                form_data.get('tone', ''),
                form_data.get('length_preference', ''),
                platform
            )

            if platform in results and 0 <= index < len(results[platform]):
                results[platform][index] = new_suggestion
                request.session['results'] = results

            return JsonResponse({
                'success': True,
                'suggestion': {
                    'caption': new_suggestion['caption'],
                    'hashtags_list': new_suggestion['hashtags']
                }
            })

        # First-time generation
        product_name = request.POST.get('product_name')
        brand_name = request.POST.get('brand_name')
        description = request.POST.get('description')
        target_audience = request.POST.get('target_audience')
        tone = request.POST.get('tone')
        length_preference = request.POST.get('length_preference')
        platforms = request.POST.getlist('platforms')

        request.session['form_data'] = {
            'product_name': product_name,
            'brand_name': brand_name,
            'description': description,
            'target_audience': target_audience,
            'tone': tone,
            'length_preference': length_preference,
            'platforms': platforms
        }

        results = {}
        for platform in platforms:
            results[platform] = [
                generate_gemini_suggestions(
                    product_name, brand_name, description,
                    target_audience, tone, length_preference, platform
                )
                for _ in range(3)
            ]

        request.session['results'] = results

    return render(request, 'generator/generate.html', {'results': results})


# -------- DOWNLOAD / EXPORT FUNCTIONALITY --------
def download_export(request, filetype):
    results = request.session.get('results', {})

    if not results:
        return HttpResponse("No captions to download", status=400)

    if filetype == 'txt':
        content = ""
        for platform, suggestions in results.items():
            content += f"--- {platform} ---\n\n"
            for idx, s in enumerate(suggestions, start=1):
                content += f"Suggestion {idx}:\n{s['caption']}\n{' '.join(s['hashtags'])}\n\n"
        response = HttpResponse(content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="captions.txt"'
        return response

    elif filetype == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Platform', 'Suggestion', 'Caption', 'Hashtags'])
        for platform, suggestions in results.items():
            for idx, s in enumerate(suggestions, start=1):
                writer.writerow([platform, f"Suggestion {idx}", s['caption'], ' '.join(s['hashtags'])])
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="captions.csv"'
        return response

    elif filetype == 'pdf':
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                leftMargin=2*cm, rightMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        elements = []
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontSize = 12
        normal_style.leading = 16

        for platform, suggestions in results.items():
            elements.append(Paragraph(f"<b>--- {platform} ---</b>", styles['Heading2']))
            elements.append(Spacer(1, 0.3*cm))
            for idx, s in enumerate(suggestions, start=1):
                elements.append(Paragraph(f"<b>Suggestion {idx}:</b>", normal_style))
                elements.append(Paragraph(s['caption'], normal_style))
                if s['hashtags']:
                    elements.append(Paragraph(' '.join([f"#{tag}" for tag in s['hashtags']]), normal_style))
                elements.append(Spacer(1, 0.4*cm))
            elements.append(Spacer(1, 0.6*cm))

        doc.build(elements)
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="captions.pdf"'
        return response

    else:
        return HttpResponse("Invalid file type", status=400)
