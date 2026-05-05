from django.shortcuts import render


def chat_view(request):
    messages = [
        {"role": "user", "text": "What's the open bug trend for the last 2 weeks?", "tools": False},
        {
            "role": "gj",
            "text": "Over the last 2 weeks: 28 opened, 26 closed…",
            "tools": True,
        },
    ]
    return render(request, "ui/mockups/chat/chat.html", {"active_nav": "gjallarhorn", "thread": messages})
