from pydantic import BaseModel


class ConfigStatusResponse(BaseModel):
    engine: str = "ctranslate2"
    model_ready: bool = True
