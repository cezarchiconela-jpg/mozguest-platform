from django.urls import get_resolver

resolver = get_resolver()

print("ROTAS PRINCIPAIS DO MOZGUEST")
print("=" * 60)

for pattern in resolver.url_patterns:
    print(pattern)
