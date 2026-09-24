import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from django.utils import timezone
from .models import Process, ProcessField, ProductionUnit, ProcessResult, AuditLog, SystemSettings


class DemoScenarioService:
    """Generates standard demo dataset for SUCCESS and FAIL scenarios for all 7 processes."""

    @staticmethod
    def get_demo_data(process_code, scenario='SUCCESS', barcode='DEMO20260924-001'):
        if scenario == 'SUCCESS':
            return DemoScenarioService._get_success_data(process_code, barcode)
        else:
            return DemoScenarioService._get_fail_data(process_code, barcode)

    @staticmethod
    def _get_success_data(code, barcode):
        base_info = {
            'barcode': barcode,
            'part_no': '84605-GB810FHV',
            'car_type': 'MQ4i',
            'alc': 'B81V',
            'lot_no': 'LOT20260924-01',
            'order_qty': 120,
            'production_qty': 42,
        }

        if code == 'P10':
            options = {
                'console': 'DLX',
                'drive': 'LHD',
                'mission': 'AUTO',
                'body_side_color': 'N2V',
                'armrest_type': 'STD',
                'armrest_color': 'BLACK',
            }
            subparts = [
                {'seq': 1, 'code': '93350-DY000', 'desc': 'Console Main ASSY', 'result': 'OK'},
                {'seq': 2, 'code': '93310-DY000', 'desc': 'Box ASSY', 'result': 'OK'},
                {'seq': 3, 'code': '84658-G8900', 'desc': 'Wiring ASSY', 'result': 'OK'},
                {'seq': 4, 'code': '12492-04121', 'desc': 'Switch ASSY', 'result': 'OK'},
            ]
            screws = [
                {'type': 'Type 1 – M4', 'required': 5, 'scanned': 5, 'status': 'OK'},
                {'type': 'Type 2 – M5', 'required': 4, 'scanned': 4, 'status': 'OK'},
            ]
        elif code == 'P30':
            options = {
                'console': 'DLX',
                'drive': 'LHD',
                'mission': 'AUTO',
            }
            subparts = [
                {'seq': 1, 'code': '84605-G8920', 'desc': 'Main Frame', 'result': 'OK'},
                {'seq': 2, 'code': '45711-G8100', 'desc': 'Cable ASSY', 'result': 'OK'},
                {'seq': 3, 'code': '12499-04120', 'desc': 'Cover ASSY', 'result': 'OK'},
            ]
            screws = [
                {'type': 'M4 Screw', 'required': 10, 'scanned': 10, 'status': 'OK'},
                {'type': 'M5 Screw', 'required': 4, 'scanned': 4, 'status': 'OK'},
            ]
        elif code == 'P40':
            options = {
                'console': 'DLX',
                'drive': 'LHD',
                'mission': 'AUTO',
                'body_side_color': 'N2V',
                'garnish_type': 'GLOSS',
                'garnish_color': 'SILVER',
            }
            subparts = [
                {'seq': 1, 'code': '84631-G8200', 'desc': 'Side Garnish LH', 'result': 'OK'},
                {'seq': 2, 'code': '84632-G8200', 'desc': 'Side Garnish RH', 'result': 'OK'},
            ]
            screws = [
                {'type': 'Garnish M4', 'required': 6, 'scanned': 6, 'status': 'OK'},
            ]
        elif code == 'P50':
            options = {
                'rrcvr_type': 'DLX',
                'rrcvr_color': 'BLACK',
                'armrest_type': 'LEATHER',
                'armrest_color': 'BLACK',
            }
            subparts = [
                {'seq': 1, 'code': '84640-G8500', 'desc': 'Rear Cover ASSY', 'result': 'OK'},
                {'seq': 2, 'code': '84645-G8100', 'desc': 'Armrest Hinge', 'result': 'OK'},
            ]
            screws = [
                {'type': 'M4 Screw', 'required': 4, 'scanned': 4, 'status': 'OK'},
                {'type': 'M5 Screw', 'required': 2, 'scanned': 2, 'status': 'OK'},
            ]
        elif code == 'P60':
            options = {
                'rrcvr_type': 'DLX',
                'rrcvr_color': 'BLACK',
                'rework_mode': 'NORMAL',
                'brk_info': 'STD(LR)',
            }
            subparts = [
                {'seq': 1, 'code': '84650-G8900', 'desc': 'RRCVR ASSY', 'result': 'OK'},
                {'seq': 2, 'code': '12488-05161', 'desc': 'Bracket ASSY', 'result': 'OK'},
            ]
            screws = [
                {'type': 'Type 1 – M4', 'required': 8, 'scanned': 8, 'status': 'OK'},
                {'type': 'Type 2 – M5', 'required': 4, 'scanned': 4, 'status': 'OK'},
            ]
        elif code == 'P41':
            options = {
                'console': 'DLX',
                'garnish_type': 'HIGH_GLOSS',
                'garnish_color': 'PIANO_BLACK',
                'work_order': 'WO-2026-0924-001',
                'worker': 'OP-001',
            }
            subparts = [
                {'seq': 1, 'code': '84631-G8200-P', 'desc': 'Garnish Main', 'result': 'OK'},
                {'seq': 2, 'code': '84632-G8200-P', 'desc': 'Garnish Sub', 'result': 'OK'},
            ]
            screws = [
                {'type': 'M4 Fastener', 'required': 6, 'scanned': 6, 'status': 'OK'},
            ]
        elif code == 'P51':
            options = {
                'rrcvr_type': 'PREMIUM',
                'rrcvr_color': 'BLACK',
                'armrest_type': 'HEATED',
                'armrest_color': 'BLACK',
                'work_order': 'WO-2026-0924-002',
                'worker': 'OP-001',
            }
            subparts = [
                {'seq': 1, 'code': '84640-G8500-C', 'desc': 'Rear Cover Cvr', 'result': 'OK'},
                {'seq': 2, 'code': '84645-G8100-H', 'desc': 'Armrest Module', 'result': 'OK'},
            ]
            screws = [
                {'type': 'M5 Heavy Bolt', 'required': 4, 'scanned': 4, 'status': 'OK'},
            ]
        else:
            options = {}
            subparts = []
            screws = []

        return {
            'base': base_info,
            'options': options,
            'subparts': subparts,
            'screws': screws,
            'result': 'PASS',
            'failure_reason': '',
        }

    @staticmethod
    def _get_fail_data(code, barcode):
        data = DemoScenarioService._get_success_data(code, barcode)
        data['result'] = 'FAIL'

        if code == 'P10':
            data['subparts'][2]['result'] = 'NG'
            data['subparts'][2]['desc'] += ' (MISMATCHED BARCODE)'
            data['screws'][0]['scanned'] = 3
            data['screws'][0]['status'] = 'NG'
            data['failure_reason'] = 'Sub-part 84658-G8900 code mismatch & Screw Type 1 count incomplete (3/5).'
        elif code == 'P30':
            data['screws'][0]['scanned'] = 7
            data['screws'][0]['status'] = 'NG'
            data['failure_reason'] = 'M4 Screw tightening count deficit (7/10 scanned).'
        elif code == 'P40':
            data['subparts'][1]['result'] = 'NG'
            data['failure_reason'] = 'Side Garnish RH color mismatch with vehicle specification.'
        elif code == 'P50':
            data['screws'][1]['scanned'] = 1
            data['screws'][1]['status'] = 'NG'
            data['failure_reason'] = 'M5 Screw missing (1/2 scanned).'
        elif code == 'P60':
            data['subparts'][0]['result'] = 'NG'
            data['failure_reason'] = 'RRCVR ASSY vision inspection verification failed (NG).'
        elif code == 'P41':
            data['options']['garnish_color'] = 'RED (WRONG)'
            data['failure_reason'] = 'Garnish Color option mismatch (RED selected vs SILVER expected).'
        elif code == 'P51':
            data['screws'][0]['scanned'] = 2
            data['screws'][0]['status'] = 'NG'
            data['failure_reason'] = 'Torque validation failed for M5 Heavy Bolt.'

        return data


class ValidationService:
    """Core logic engine for verifying process dependency and field rules."""

    @staticmethod
    def is_process_unlocked(unit, target_process):
        """Determines if target_process can be accessed by the given unit."""
        if not target_process.before_process:
            return True, "No prior dependency"

        prereq = target_process.before_process
        prior_result = ProcessResult.objects.filter(
            production_unit=unit,
            process=prereq,
            result='PASS'
        ).first()

        if prior_result:
            return True, f"Prerequisite process {prereq.code} passed"
        else:
            return False, f"Prerequisite process {prereq.code} ({prereq.name}) has not PASSED yet."

    @staticmethod
    def validate_submission(process, form_data, subparts, screws):
        """Validates submitted inputs against process rules."""
        errors = []

        # Validate subparts
        for sp in subparts:
            if sp.get('result') != 'OK':
                errors.append(f"Sub-part '{sp.get('desc')}' status is NG.")

        # Validate screws
        for sc in screws:
            req = int(sc.get('required', 0))
            scn = int(sc.get('scanned', 0))
            if scn < req:
                errors.append(f"Screw '{sc.get('type')}' scanned count ({scn}) is less than required ({req}).")

        is_valid = len(errors) == 0
        return is_valid, errors


class ProductionService:
    """Manages unit lifecycle and process progression."""

    @staticmethod
    def get_or_create_unit(barcode):
        unit, created = ProductionUnit.objects.get_or_create(
            barcode=barcode,
            defaults={
                'car_type': 'MQ4i',
                'alc': 'B81V',
                'part_no': '84605-GB810FHV',
                'lot_no': f"LOT{timezone.now().strftime('%Y%m%d')}-01",
                'order_qty': 120,
                'production_qty': 42,
                'current_process': Process.objects.filter(sequence=1).first()
            }
        )
        return unit

    @staticmethod
    def record_process_result(unit, process, result_status, options_data, subparts_data, screws_data, failure_reason='', operator_id='001'):
        result_obj = ProcessResult.objects.create(
            production_unit=unit,
            process=process,
            operator_id=operator_id,
            result=result_status,
            options_data=options_data,
            subparts_data=subparts_data,
            screws_data=screws_data,
            failure_reason=failure_reason
        )

        if result_status == 'PASS':
            # Unlock next process if exists
            next_proc = Process.objects.filter(sequence=process.sequence + 1).first()
            if next_proc:
                unit.current_process = next_proc
                unit.status = 'IN_PROGRESS'
            else:
                unit.status = 'COMPLETED'
            unit.save()
        else:
            unit.status = 'FAILED'
            unit.save()

        # Audit log
        AuditLog.objects.create(
            operator=operator_id,
            action=f"PROCESS_{result_status}",
            details=f"Barcode: {unit.barcode} | Process: {process.code} | Result: {result_status} | Reason: {failure_reason}"
        )

        return result_obj


class ReportService:
    """Generates Excel files for production history."""

    @staticmethod
    def export_work_history_excel():
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Floor Work History"

        # Headers
        headers = ['#', 'Timestamp', 'Barcode', 'Process Code', 'Process Name', 'Part No', 'Result', 'Operator', 'Failure Reason']
        
        # Styles
        header_fill = PatternFill(start_color="1F2937", end_color="1F2937", fill_type="solid")
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        center_align = Alignment(horizontal="center", vertical="center")

        ws.append(headers)
        for col in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = center_align

        results = ProcessResult.objects.all().select_related('production_unit', 'process')
        pass_fill = PatternFill(start_color="D1FAE5", end_color="D1FAE5", fill_type="solid")
        fail_fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
        pass_font = Font(name="Segoe UI", color="065F46", bold=True)
        fail_font = Font(name="Segoe UI", color="991B1B", bold=True)

        for idx, r in enumerate(results, start=1):
            row_data = [
                idx,
                r.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                r.production_unit.barcode,
                r.process.code,
                r.process.name,
                r.production_unit.part_no,
                r.result,
                r.operator_id,
                r.failure_reason or '-'
            ]
            ws.append(row_data)

            # Styling the result cell
            result_cell = ws.cell(row=idx + 1, column=7)
            if r.result == 'PASS':
                result_cell.fill = pass_fill
                result_cell.font = pass_font
            else:
                result_cell.fill = fail_fill
                result_cell.font = fail_font

        # Auto column width
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

        return wb
