# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase

class TestCarbonLedgerFlow(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # NOTE (port 19.0->18.0, batch 5 + follow-up co2e_amount): this test
        # covers the fuel-log -> carbon-ledger bridge (equipment_log_extension),
        # which was trimmed with the farm_equipment dependency (see
        # __manifest__.py). setUpClass itself needs farm_equipment fields
        # (maintenance.equipment.is_agri_machinery / fuel_type), so skip the
        # whole class while farm_equipment is not installed. Dormant until
        # batch 6, when the bridge is restored WITH the field fix below.
        try:
            cls.env['farm.equipment.log']
        except KeyError:
            cls.skipTest('farm.equipment.log not installed (farm_equipment trimmed in batch 5); bridge test dormant until batch 6.')

        # 1. Create a Unit of Measure (Liters)
        try:
            cls.uom_liter = cls.env.ref('uom.product_uom_litre')
        except ValueError:
            cls.uom_liter = cls.env['uom.uom'].search([('name', '=', 'L')], limit=1)

        # 2. Create the Diesel Product
        cls.diesel_product = cls.env['product.template'].create({
            'name': 'Diesel Fuel',
            'type': 'consu',
            'uom_id': cls.uom_liter.id,
            'uom_po_id': cls.uom_liter.id,
        })
        
        # 3. Create Carbon Factor for Diesel (e.g., 2.68 kg CO2e per Liter)
        cls.carbon_factor = cls.env['agri.carbon.factor'].create({
            'name': 'Diesel Combustion',
            'product_id': cls.diesel_product.id,
            'category': 'energy',
            'emission_factor': 2.68,
            'uom_id': cls.uom_liter.id,
            'source': 'IPCC'
        })
        
        # 4. Create a Tractor
        cls.tractor = cls.env['maintenance.equipment'].create({
            'name': 'John Deere 5075E',
            'is_agri_machinery': True,
            'fuel_type': 'diesel',
        })
        
        # 5. Create a Land Parcel (Location)
        cls.parcel = cls.env['farm.location'].create({
            'name': 'Field B2'
        })

    def test_01_equipment_fuel_log_triggers_carbon_ledger(self):
        """
        Scenario:
        1. A tractor consumes 50L of diesel during an operation.
        2. A fuel log is created.
        3. The system automatically intercepts this log, finds the IPCC carbon factor,
           and writes an entry into the Carbon Ledger for Scope 1 emissions.
        """
        # Create fuel log
        log = self.env['farm.equipment.log'].create({
            'equipment_id': self.tractor.id,
            'date': '2026-05-16',
            'engine_hours': 4.5,
            'fuel_consumed': 50.0,
            'notes': 'Ploughing Field B2'
        })
        
        # In the implementation, we might need a method or an override on create/write
        # Verify that a carbon ledger entry was created
        # NOTE (follow-up co2e_amount): upstream's bridge looked the ledger up by
        # ('origin', '=', 'Equipment Log: ...'), but agri.carbon.ledger has NO
        # 'origin' field — restoring the bridge ALSO requires adding an
        # 'origin' (Char) field (and a 'scope' Selection if Scope 1/2/3
        # traceability is wanted) to agri.carbon.ledger first, or changing
        # this lookup to factor_id/quantity/date.
        ledgers = self.env['agri.carbon.ledger'].search([
            ('origin', '=', f'Equipment Log: {log.id}')
        ])

        self.assertTrue(ledgers, "A carbon ledger entry must be automatically created when fuel is logged.")
        self.assertEqual(len(ledgers), 1)
        ledger = ledgers[0]

        self.assertEqual(ledger.scope, 'scope1', "Diesel combustion by owned tractor should be Scope 1.")
        self.assertEqual(ledger.impact_type, 'emission', "Fuel burning is an emission.")

        # 50L * 2.68 = 134.0 kg CO2e
        # NOTE (follow-up co2e_amount): upstream asserted ledger.co2e_amount,
        # a field that does NOT exist on agri.carbon.ledger — the real field
        # is the computed stored 'total_co2e' (quantity x factor, signed by
        # impact_type; farm_carbon_accounting.py). Upstream's bridge also
        # wrote three more nonexistent ledger fields (scope, source_factor_id,
        # origin) — a restored bridge must pass factor_id + quantity only and
        # let the compute derive total_co2e; it must NOT write total_co2e
        # directly (computed field, no inverse).
        self.assertAlmostEqual(ledger.total_co2e, 134.0, places=2, msg="Carbon calculation must match Factor * Consumed Volume.")

