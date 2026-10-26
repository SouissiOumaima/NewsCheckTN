"""Configuration commune des tests.

NLI_BACKEND=stub : les tests ne téléchargent jamais le modèle NLI du Lot C (environ 1 Go), même
sur une machine où torch / transformers sont installés. Les tests du Lot C injectent un faux
modèle avec `models.nli.stance.set_classifier`.
"""

import os

os.environ.setdefault("NLI_BACKEND", "stub")
