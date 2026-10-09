from src.main import app

print("Проверка через OpenAPI-схему:")
schema = app.openapi()
for path, methods in schema["paths"].items():
    print(f"  {sorted(methods.keys())} {path}")
