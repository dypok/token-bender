import random
import pandas as pd
from faker import Faker


def generar_resenas_excel(
    nombre_archivo="resenas_productos_50k.xlsx", num_filas=50000
):
    print(f"Generando {num_filas} registros fake en español...")

    # Inicializar Faker en español
    fake = Faker("es_ES")

    # Lista de productos de ejemplo para hacer los datos más consistentes
    productos_cat = [
        "Audífonos Bluetooth Wireless",
        "Smartphone Pro Max 256GB",
        "Laptop Gamer 15.6''",
        "Reloj Inteligente Sport",
        "Cámara Digital 4K",
        "Teclado Mecánico RGB",
        "Monitor LED 27'' Curved",
        "Silla Ergonómica Oficina",
        "Cafetera Automática Express",
        "Aspiradora Robot Robotik",
        "Mochila Antirrobo Impermeable",
        "Parlante Portátil Waterproof",
    ]

    # Lista de plantillas de reseñas
    plantillas_resenas = [
        "Excelente producto, superó mis expectativas.",
        "Llegó a tiempo y en perfecto estado. Muy recomendado.",
        "La calidad del material es aceptable por el precio.",
        "No me gustó la calidad del producto, esperaba más.",
        "Pésimo servicio de entrega, llegó dañado.",
        "Funciona muy bien, lo uso todos los días.",
        "Buen diseño y materiales, aunque podría ser un poco más barato.",
        "Cumple con lo prometido en la descripción.",
    ]

    data = []

    # Generación eficiente de datos
    for _ in range(num_filas):
        id_cliente = fake.uuid4()[:8].upper()
        cliente = fake.name()
        ciudad = fake.city()
        producto = random.choice(productos_cat)

        # Probabilidad del 25% de que la reseña esté vacía ( None / np.nan )
        # y 75% de que contenga un texto generado o predefinido
        if random.random() < 0.25:
            resena = ""
        else:
            # Combina una plantilla aleatoria con texto simulado de Faker
            resena = (
                f"{random.choice(plantillas_resenas)} {fake.sentence(nb_words=6)}"
            )

        data.append(
            {
                "id_cliente": id_cliente,
                "cliente": cliente,
                "ciudad": ciudad,
                "producto": producto,
                "reseña": resena,
            }
        )

    print("Creando DataFrame de Pandas...")
    df = pd.DataFrame(data)

    print(f"Guardando archivo Excel: {nombre_archivo}...")
    # Exportar a Excel (requiere openpyxl)
    df.to_excel(nombre_archivo, index=False, engine="openpyxl")

    print(f"¡Proceso completado con éxito! Archivo creado: {nombre_archivo}")


if __name__ == "__main__":
    generar_resenas_excel()