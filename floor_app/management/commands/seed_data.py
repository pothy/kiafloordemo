from django.core.management.base import BaseCommand
from floor_app.models import Process, ProcessField, ProductionUnit, ProcessResult, SystemSettings, OperatorUser, ProductionRequest
from floor_app.services import DemoScenarioService, ProductionService
from django.utils import timezone
import datetime


class Command(BaseCommand):
    help = 'Seeds initial database for KIA Floor Process Validation System'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("Seeding initial KIA Floor processes, requests & demo data..."))

        SystemSettings.objects.get_or_create(id=1)

        # 1. Create Processes
        p10, _ = Process.objects.get_or_create(code='P10', defaults={'name': 'Assembly #10', 'sequence': 1, 'image_name': 'kia_console_assembly.png'})
        p30, _ = Process.objects.get_or_create(code='P30', defaults={'name': 'Assembly #30', 'sequence': 2, 'before_process': p10, 'image_name': 'kia_console_assembly.png'})
        p40, _ = Process.objects.get_or_create(code='P40', defaults={'name': 'Assembly #40', 'sequence': 3, 'before_process': p30, 'image_name': 'kia_console_assembly.png'})
        p50, _ = Process.objects.get_or_create(code='P50', defaults={'name': 'Assembly #50', 'sequence': 4, 'before_process': p40, 'image_name': 'kia_console_assembly.png'})
        p60, _ = Process.objects.get_or_create(code='P60', defaults={'name': 'Assembly #60', 'sequence': 5, 'before_process': p50, 'image_name': 'kia_console_assembly.png'})
        p41, _ = Process.objects.get_or_create(code='P41', defaults={'name': 'Garnish', 'sequence': 6, 'before_process': p40, 'image_name': 'kia_console_assembly.png'})
        p51, _ = Process.objects.get_or_create(code='P51', defaults={'name': 'RRCVR', 'sequence': 7, 'before_process': p60, 'image_name': 'kia_console_assembly.png'})

        # 2. Create Operator Users matching user image exact specifications
        operators = [
            ("admin", "Administrator", "admin", "ADMIN", None, "ST-HQ"),
            ("EMP010", "P10 Operator", "EMP010", "OPERATOR", p10, "ST-01"),
            ("EMP030", "P30 Operator", "EMP030", "OPERATOR", p30, "ST-02"),
            ("EMP040", "P40 Operator", "EMP040", "OPERATOR", p40, "ST-03"),
            ("EMP050", "P50 Operator", "EMP050", "OPERATOR", p50, "ST-04"),
            ("EMP060", "P60 Operator", "EMP060", "OPERATOR", p60, "ST-05"),
            ("EMP041", "Garnish Operator", "EMP041", "OPERATOR", p41, "ST-06"),
            ("EMP051", "RRCVR Operator", "EMP051", "OPERATOR", p51, "ST-07"),
        ]

        OperatorUser.objects.all().delete()

        user_map = {}
        for uname, fname, op_id, role, proc, st in operators:
            u = OperatorUser.objects.create(
                username=uname,
                full_name=fname,
                operator_id=op_id,
                role=role,
                assigned_process=proc,
                station_code=st,
            )
            user_map[op_id] = u

        # 3. Create Sample Production Requests matching reference image
        ProductionRequest.objects.all().delete()
        requests_data = [
            ("REQ-20260924-001", "DEMO20260924-001", "MQ4i", "B81V", "NORMAL", "IN_PROGRESS", p30, user_map.get("EMP030")),
            ("REQ-20260924-002", "DEMO20260924-002", "MQ4i", "B81V", "HIGH", "WAITING", p10, None),
            ("REQ-20260924-003", "DEMO20260924-003", "MQ4i", "B81V", "NORMAL", "WAITING", p10, None),
            ("REQ-20260924-004", "DEMO20260924-004", "EV6", "B82V", "NORMAL", "WAITING", p10, None),
            ("REQ-20260924-005", "DEMO20260924-005", "MQ4i", "B81V", "LOW", "WAITING", p10, None),
        ]

        for req_id, bc, car, alc, prio, st, proc, op in requests_data:
            ProductionRequest.objects.create(
                request_id=req_id,
                barcode=bc,
                car_type=car,
                alc=alc,
                priority=prio,
                status=st,
                current_process=proc,
                assigned_operator=op
            )

        # 4. Create Sample Production Units
        sample_barcodes = [
            ("DEMO20260924-001", "MQ4i", "B81V", "84605-GB810FHV", "LOT20260924-01", p30, "IN_PROGRESS"),
            ("DEMO20260924-002", "MQ4i", "B81V", "84605-GB810FHV", "LOT20260924-01", p51, "COMPLETED"),
            ("DEMO20260924-003", "MQ4i", "B81V", "84605-GB810FHV", "LOT20260924-01", p30, "FAILED"),
        ]

        now = timezone.now()
        for idx, (bc, car, alc, part, lot, proc, status) in enumerate(sample_barcodes):
            unit, _ = ProductionUnit.objects.get_or_create(
                barcode=bc,
                defaults={
                    'car_type': car,
                    'alc': alc,
                    'part_no': part,
                    'lot_no': lot,
                    'order_qty': 120,
                    'production_qty': 42 + idx * 5,
                    'current_process': proc,
                    'status': status
                }
            )

            if idx == 0:  # DEMO...-001 passed P10 and P30
                if not ProcessResult.objects.filter(production_unit=unit, process=p10).exists():
                    ProcessResult.objects.create(
                        production_unit=unit, process=p10,
                        operator_id='EMP010',
                        result='PASS',
                        options_data={'console': 'DLX', 'drive': 'LHD', 'mission': 'AUTO'},
                        subparts_data=[{'code': '93350-DY000', 'desc': 'Console Main ASSY', 'result': 'OK'}],
                        screws_data=[{'type': 'Type 1 - M4', 'required': 5, 'scanned': 5, 'status': 'OK'}],
                        timestamp=now - datetime.timedelta(minutes=40)
                    )

        self.stdout.write(self.style.SUCCESS("Database seeding with Production Requests completed!"))
