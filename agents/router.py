def route_request(text: str) -> str:
    text = text.lower()

    coding = [
        "code", "bug", "error", "django", "react", "next.js", "nextjs",
        "python", "docker", "github", "api", "database", "sql",
        "كود", "برمجة", "خطأ", "مشروع", "سيرفر", "دجانجو"
    ]

    research = [
        "research", "thesis", "paper", "methodology", "results",
        "hypothesis", "apa", "statistics", "spss",
        "بحث", "رسالة", "منهجية", "نتائج", "فرضية", "إحصاء"
    ]

    creative = [
        "prompt", "image", "video", "design", "visual", "storyboard",
        "برومبت", "صورة", "فيديو", "تصميم", "مشهد", "سيناريو"
    ]

    if any(word in text for word in coding):
        return "coding"

    if any(word in text for word in research):
        return "research"

    if any(word in text for word in creative):
        return "creative"

    return "general"
