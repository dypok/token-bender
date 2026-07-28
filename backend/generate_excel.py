import pandas as pd
from faker import Faker
import random
import argparse
import os

fake = Faker('es_ES')

ERROR_TYPES = ["crash", "bug", "performance", "ui", "network", "feature_request"]
COMPONENTS = [
    "login", "signup", "profile_picture_upload", "search", "checkout",
    "payment", "notifications", "settings", "chat", "camera",
    "gallery", "map", "video_player", "audio_player", "file_download",
]

TEMPLATES = [
    "La aplicación se cierra cuando intento {action}. Es muy frustrante.",
    "Cada vez que {action} la app se congela y tengo que reiniciar.",
    "No puedo {action} porque la app explota. Por favor arreglen esto.",
    "Desde la última actualización, cuando {action} la pantalla se pone negra.",
    "Error grave: al {action} la aplicación crashea inmediatamente.",
    "Llevo días sin poder {action} por un bug que no se soluciona.",
    "La app va lenta y cuando {action} se tilda por completo.",
    "Pésimo rendimiento. Intenté {action} y la app se cerró sola.",
    "No funciona correctamente. Quiero {action} pero la app falla siempre.",
    "Horrible experiencia. Al {action} aparece un error y se cierra.",
    "La cámara no abre cuando intento {action} desde el perfil.",
    "Se queda cargando infinitamente cuando trato de {action}.",
    "Desde que actualicé, no puedo {action} sin que la app se buguee.",
    "Increíble que todavía no arreglen el error de {action}.",
    "Cansado de que la app se caiga cada vez que {action}.",
    "Nunca pude {action} porque la app crashea en el intento 5.",
    "Funcionaba bien antes. Ahora al {action} la app muere.",
    "Por favor solucionen el bug que impide {action}.",
]

ACTIONS = [
    "subir una foto de perfil", "abrir la galería", "iniciar sesión",
    "registrarme", "pagar con tarjeta", "ver notificaciones",
    "reproducir un video", "descargar un archivo", "enviar un mensaje",
    "abrir el chat", "buscar un producto", "actualizar mis datos",
    "cambiar la contraseña", "compartir contenido", "ver el mapa",
    "subir un documento", "adjuntar una imagen", "hacer una captura",
    "grabar un video", "editar mi perfil",
]


def generate_review() -> dict:
    template = random.choice(TEMPLATES)
    action = random.choice(ACTIONS)
    text = template.format(action=action)

    return {
        "review": text,
        "error_type": random.choice(ERROR_TYPES),
        "component": random.choice(COMPONENTS),
        "rating": random.choices([1, 2, 3, 4, 5], weights=[30, 25, 20, 15, 10])[0],
        "date": fake.date_between(start_date="-6M", end_date="today"),
        "app_version": f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
        "platform": random.choice(["Android", "iOS"]),
    }


def main():
    parser = argparse.ArgumentParser(description="Generate sample Excel with app store reviews")
    parser.add_argument("-n", "--num", type=int, default=50, help="Number of reviews (default: 50)")
    parser.add_argument("-o", "--output", type=str, default="sample_reviews.xlsx", help="Output file name")
    args = parser.parse_args()

    rows = [generate_review() for _ in range(args.num)]
    df = pd.DataFrame(rows)
    df = df[["review", "error_type", "component", "rating", "date", "app_version", "platform"]]

    output_path = os.path.join(os.path.dirname(__file__), args.output)
    df.to_excel(output_path, index=False)
    print(f"✓ Generado: {output_path}  ({args.num} reseñas)")


if __name__ == "__main__":
    main()
