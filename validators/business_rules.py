import pandas as pd
from typing import Dict, Any
from datetime import datetime


def validate_exportacion_flores(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida registros de exportación de flores mapeando campos reales del CSV.
    """
    errors = {}

    # Función auxiliar para quitar acentos de manera simple
    def limpiar_texto(texto: str) -> str:
        replacements = (("Á", "A"), ("É", "E"), ("Í", "I"), ("Ó", "O"), ("Ú", "U"))
        res = str(texto).upper().strip()
        for a, b in replacements:
            res = res.replace(a, b)
        return res

    # 1. Validar fecha (mapea fecha_pedido o fecha)
    fecha_col = next((c for c in ['fecha_pedido', 'fecha', 'fecha_exportacion'] if c in record), None)
    if fecha_col:
        try:
            fecha = pd.to_datetime(record[fecha_col])
            if fecha > datetime.now():
                errors[fecha_col] = "Fecha no puede ser futura"
        except:
            errors[fecha_col] = "Formato de fecha inválido"

    # 2. Validar cantidad (mapea cantidad_tallos o cantidad)
    cant_col = next((c for c in ['cantidad_tallos', 'cantidad'] if c in record), None)
    if cant_col:
        try:
            cantidad = float(record[cant_col])
            if cantidad <= 0:
                errors[cant_col] = "Cantidad debe ser mayor a 0"
        except:
            errors[cant_col] = "Cantidad debe ser un número"

    # 3. Validar valor (mapea total_venta_usd, precio_unitario_usd o valor)
    valor_col = next((c for c in ['total_venta_usd', 'precio_unitario_usd', 'valor', 'valor_usd'] if c in record), None)
    if valor_col:
        try:
            valor = float(record[valor_col])
            if valor <= 0:
                errors[valor_col] = "Valor debe ser mayor a 0"
        except:
            errors[valor_col] = "Valor debe ser un número"

    # 4. Validar destino (mapea ciudad_destino o pais)
    destino_col = next((c for c in ['ciudad_destino', 'pais', 'pais_destino'] if c in record), None)
    if destino_col:
        # Se asume válido por ahora al ser ciudades, o puedes agregar una lista de tus ciudades válidas
        pass

    # 5. Validar tipo de flor (Normaliza tildes y mayúsculas)
    # 5. Validar tipo de flor (Soporta singulares, plurales y nuevas especies)
    if 'tipo_flor' in record:
        # Catálogo maestro ampliado con variantes en singular, plural y nuevas flores detectadas
        flores_validas = {
            'ROSAS', 'ROSA',
            'CLAVELES', 'CLAVEL',
            'GIRASOLES', 'GIRASOL',
            'ORQUIDEAS', 'ORQUIDEA',
            'LIRIOS', 'LIRIO',
            'TULIPANES', 'TULIPAN',
            'ASTROMELIAS', 'ASTROMELIA',
            'CRISANTEMOS', 'CRISANTEMO'
        }

        # Limpieza profunda de espacios y tildes
        flor_limpia = limpiar_texto(record['tipo_flor'])

        if flor_limpia not in flores_validas:
            errors[
                'tipo_flor'] = f"Tipo de flor no válido ('{record['tipo_flor']}'). Válidos: {sorted(list(flores_validas))}"

    if errors:
        raise ValueError(f"Errores de validación: {errors}")

    return record
