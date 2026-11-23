"""Regression checks for linked spare-parts orders blocking record deletion."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")

class SparePartsDeleteGuardTests(unittest.TestCase):
    def test_client_deletion_guard_checks_linked_spare_parts_orders(self):
        guard = SOURCE[ SOURCE.index("const linked="):SOURCE.index("if(linked){", SOURCE.index("const linked=")) ]
        self.assertIn("key==='clientes'", guard)
        self.assertIn("(db.pedidosRepuestos||[]).some", guard)
        self.assertIn("x.tipo!=='taller'", guard)
        self.assertIn("String(x.clienteId||'')===id", guard)

    def test_vehicle_deletion_guard_checks_linked_spare_parts_orders(self):
        guard = SOURCE[ SOURCE.index("const linked="):SOURCE.index("if(linked){", SOURCE.index("const linked=")) ]
        self.assertIn("key==='vehiculos'", guard)
        self.assertIn("String(x.vehiculoId||'')===id", guard)
