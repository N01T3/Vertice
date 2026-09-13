"""O vocabulário mínimo compartilhado: tipo de item e regime de encargos.

Porquê arquivo próprio, nem em `types.py` nem em `query_results.py`:
ingestão e consulta precisam dos dois igualmente. Morar do lado
errado obrigaria o outro lado a importar por ele — exatamente o
acoplamento que a separação entre os dois arquivos existe para evitar.
"""

from __future__ import annotations

from typing import Literal

TipoItem = Literal["INSUMO", "COMPOSICAO"]
Regime = Literal["ONERADO", "DESONERADO", "SEM_ENCARGOS"]
