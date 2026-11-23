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

    def test_delete_guards_cover_all_direct_link_collections(self):
        guard = self.linked_guard()
        client_block = guard[guard.index("key==='clientes'"):guard.index("key==='vehiculos'")]
        vehicle_block = guard[guard.index("key==='vehiculos'"):guard.index("key==='trabajos'")]
        work_block = guard[guard.index("key==='trabajos'"):]
        for collection in ("vehiculos", "trabajos", "presupuestos", "eventos", "recepciones", "diagnosticos", "cuentas", "pedidosRepuestos"):
            self.assertIn((f"(db.{collection}||[]).some" if collection == "pedidosRepuestos" else f"db.{collection}.some"), client_block, f"client guard missing {collection}")
        for collection in ("trabajos", "presupuestos", "eventos", "recepciones", "diagnosticos", "pedidosRepuestos"):
            self.assertIn((f"(db.{collection}||[]).some" if collection == "pedidosRepuestos" else f"db.{collection}.some"), vehicle_block, f"vehicle guard missing {collection}")
        for collection in ("movimientos", "recepciones", "diagnosticos", "presupuestos", "cuentas", "pedidosRepuestos"):
            self.assertIn((f"(db.{collection}||[]).some" if collection == "pedidosRepuestos" else f"db.{collection}.some"), work_block, f"work-order guard missing {collection}")


class ActivityLocalDateTests(unittest.TestCase):
    def test_activity_uses_local_date_helper(self):
        self.assertIn("function smeActivityLocalDate(value)", SOURCE)
        self.assertIn("smeActivityLocalDate(x.time)===today", SOURCE)
        self.assertIn("smeActivityLocalDate(x.time)===d", SOURCE)

    def test_local_date_helper_uses_local_calendar_fields(self):
        start = SOURCE.index("function smeActivityLocalDate(value)")
        helper = SOURCE[start:SOURCE.index("function smeActivityRead()", start)]
        self.assertIn("d.getFullYear()", helper)
        self.assertIn("d.getMonth()+1", helper)
        self.assertIn("d.getDate()", helper)
        self.assertNotIn("toISOString", helper)
