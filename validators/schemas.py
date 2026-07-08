from pydantic import BaseModel, validator
from typing import Optional
from datetime import datetime

class PQRSRecord(BaseModel):
    id: Optional[int]
    fecha_recepcion: datetime
    tipo_pqrs: str  # Petición, Queja, Reclamo, Sugerencia
    canal: str  # Correo, Web, Presencial, etc.
    nombre_solicitante: str
    email_solicitante: str
    telefono_solicitante: Optional[str]
    descripcion: str
    estado: str  # Recibido, En proceso, Resuelto, Cerrado
    fecha_resolucion: Optional[datetime]
    observaciones: Optional[str]

    @validator('tipo_pqrs')
    def validate_tipo(cls, v):
        allowed = ['Petición', 'Queja', 'Reclamo', 'Sugerencia']
        if v not in allowed:
            raise ValueError(f'Tipo debe ser uno de {allowed}')
        return v

    @validator('estado')
    def validate_estado(cls, v):
        allowed = ['Recibido', 'En proceso', 'Resuelto', 'Cerrado']
        if v not in allowed:
            raise ValueError(f'Estado debe ser uno de {allowed}')
        return v