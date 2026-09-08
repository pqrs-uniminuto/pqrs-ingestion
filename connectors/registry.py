from typing import Dict, Type
from connectors.strategies import (
    BaseIngestionStrategy,
    CsvIngestionStrategy,
    ExcelIngestionStrategy,
    JsonApiIngestionStrategy
)


class StrategyRegistry:
    """Registro desacoplado que asocia extensiones y tipos a su estrategia correspondiente."""

    _STRATEGIES: Dict[str, Type[BaseIngestionStrategy]] = {
        "CSV": CsvIngestionStrategy,
        "EXCEL": ExcelIngestionStrategy,
        "XLSX": ExcelIngestionStrategy,
        "XLS": ExcelIngestionStrategy,
        "JSON": JsonApiIngestionStrategy,
        "API": JsonApiIngestionStrategy,
        "SOCRATA": JsonApiIngestionStrategy,
    }

    @classmethod
    def get_strategy(cls, source_type: str) -> BaseIngestionStrategy:
        key = source_type.upper().strip()
        strategy_class = cls._STRATEGIES.get(key)

        if not strategy_class:
            raise KeyError(
                f"Tipo de fuente '{source_type}' no soportado. Opciones válidas: {list(cls._STRATEGIES.keys())}")

        return strategy_class()