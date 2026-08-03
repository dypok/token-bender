import pytest
import io
import pandas as pd


@pytest.mark.asyncio
async def test_translate_service_unit():
    from app.services.translator import translate
    translated, engine = await translate("La aplicación se cierra sola")
    assert translated != ""
    assert translated.strip().lower() != "la aplicación se cierra sola"
    assert "close" in translated.lower() or "app" in translated.lower() or "crash" in translated.lower()


@pytest.mark.asyncio
async def test_batch_start_and_progress_flow(client):
    # Crear un DataFrame dummy en memoria
    df = pd.DataFrame({
        "review": [
            "Excelente producto, superó mis expectativas.",
            "Excelente producto, superó mis expectativas.",  # Duplicado
            "La aplicación se cierra al abrir el menú."
        ]
    })
    excel_io = io.BytesIO()
    df.to_excel(excel_io, index=False, engine="openpyxl")
    excel_io.seek(0)

    files = {"file": ("test.xlsx", excel_io.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    data = {"optent_tokens": "true", "engine": "ctranslate2"}

    resp = await client.post("/api/batch/start", files=files, data=data)
    assert resp.status_code == 200
    task_data = resp.json()
    assert "task_id" in task_data
    task_id = task_data["task_id"]

    # Consultar progreso hasta que done=True
    import asyncio
    done = False
    resultData = None
    for _ in range(20):
        await asyncio.sleep(0.5)
        prog_resp = await client.get(f"/api/batch/progress/{task_id}")
        assert prog_resp.status_code == 200
        prog_json = prog_resp.json()
        if prog_json["done"]:
            done = True
            resultData = prog_json["result"]
            break

    assert done is True
    assert resultData is not None
    # Con el agrupamiento semántico, las 3 reseñas de entrada se consolidan en 2 clusters ejecutivos
    assert len(resultData["results"]) == 2
    # El cluster "Excelente producto..." contiene frecuencia=2 por los duplicados
    assert resultData["results"][0]["frequency"] == 2 or resultData["results"][1]["frequency"] == 2
    assert resultData["results"][0]["text_en"] != ""
