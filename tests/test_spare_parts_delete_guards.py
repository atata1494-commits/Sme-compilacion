"""Regression checks for linked spare-parts orders blocking record deletion."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "index.html").read_text(encoding="utf-8")

class SparePartsDeleteGuardTests(unittest.TestCase):
    def linked_guard(self):
        start = SOURCE.index("const linked=(key==='clientes'")
        return SOURCE[start:SOURCE.index("if(linked){", start)]

    def test_client_delete_guard_checks_orders(self):
        guard = self.linked_guard()
        self.assertIn("(db.pedidosRepuestos||[]).some", guard)
        self.assertIn("x.tipo!=='taller'", guard)
        self.assertIn("String(x.clienteId||'')===id", guard)

    def test_vehicle_delete_guard_checks_orders(self):
        guard = self.linked_guard()
        self.assertIn("key==='vehiculos'", guard)
        self.assertIn("String(x.vehiculoId||'')===id", guard)

    def test_work_order_delete_guard_checks_orders(self):
        guard = self.linked_guard()
        self.assertIn("key==='trabajos'", guard)
        self.assertIn("String(x.trabajoId||'')===id", guard)
