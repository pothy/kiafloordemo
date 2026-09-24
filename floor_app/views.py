import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from .models import Process, ProcessField, ProductionUnit, ProcessResult, AuditLog, SystemSettings, OperatorUser, ProductionRequest
from .services import DemoScenarioService, ValidationService, ProductionService, ReportService


def get_current_user(request):
    """Helper to retrieve current active operator session user."""
    user_id = request.session.get('user_id')
    if user_id:
        user = OperatorUser.objects.filter(id=user_id).first()
        if user:
            return user
    return None


@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        user = OperatorUser.objects.filter(username__iexact=username).first()
        if not user:
            user = OperatorUser.objects.filter(operator_id__iexact=username).first()

        if user:
            request.session['user_id'] = user.id
            if user.role == 'OPERATOR' and user.assigned_process:
                return redirect('process_validation', process_code=user.assigned_process.code)
            return redirect('dashboard')
        else:
            return render(request, 'login.html', {'error_msg': f"Employee ID or User '{username}' not found."})

    return render(request, 'login.html')



def logout_view(request):
    request.session.flush()
    return redirect('login')


def dashboard_view(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    # If operator is station-restricted, redirect them to their assigned process
    if user.role == 'OPERATOR' and user.assigned_process:
        return redirect('process_validation', process_code=user.assigned_process.code)

    # Request statistics matching top-right quadrant reference mockup
    all_requests = ProductionRequest.objects.all().select_related('current_process', 'assigned_operator')
    total_requests = all_requests.count()
    in_progress_count = all_requests.filter(status='IN_PROGRESS').count()
    waiting_count = all_requests.filter(status='WAITING').count()
    paused_count = all_requests.filter(status='PAUSED').count()
    completed_today = 28  # demo counter matching UI

    active_request = all_requests.filter(status__in=['IN_PROGRESS', 'PAUSED']).first()
    waiting_requests = all_requests.filter(status='WAITING')

    all_processes = Process.objects.filter(is_active=True).order_by('sequence')
    all_users = OperatorUser.objects.all().select_related('assigned_process')

    # Operator Statuses Grid
    operator_statuses = []
    for u in all_users.filter(role='OPERATOR'):
        is_working = active_request and active_request.assigned_operator and active_request.assigned_operator.id == u.id
        status_text = 'In Progress' if is_working else ('Paused' if active_request and active_request.status == 'PAUSED' and is_working else 'Idle')
        operator_statuses.append({
            'user': u,
            'status': status_text,
            'is_working': is_working
        })

    context = {
        'total_requests': total_requests,
        'in_progress_count': in_progress_count,
        'waiting_count': waiting_count,
        'paused_count': paused_count,
        'completed_today': completed_today,
        'active_request': active_request,
        'waiting_requests': waiting_requests,
        'all_processes': all_processes,
        'operator_statuses': operator_statuses,
        'active_tab': 'dashboard',
        'current_user': user,
        'all_users': all_users,
    }
    return render(request, 'dashboard.html', context)


def process_validation_view(request, process_code='P10'):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    target_process = get_object_or_404(Process, code=process_code)
    all_processes = Process.objects.filter(is_active=True).order_by('sequence')
    all_users = OperatorUser.objects.all().select_related('assigned_process')

    # RBAC ACCESS CHECK
    if user.role == 'OPERATOR' and user.assigned_process:
        if user.assigned_process.code != target_process.code:
            return render(request, 'access_denied.html', {
                'current_user': user,
                'target_process': target_process,
                'assigned_process': user.assigned_process,
                'all_processes': all_processes,
                'all_users': all_users,
                'active_tab': 'validation',
            })

    # REQUEST MANAGEMENT INTERLOCK EVALUATION FOR OPERATORS
    active_request = ProductionRequest.objects.filter(status__in=['IN_PROGRESS', 'PAUSED', 'WAITING']).first()

    # Case 1: No active request exists in system or assigned
    if not active_request:
        return render(request, 'operator_no_request.html', {
            'current_user': user,
            'target_process': target_process,
            'all_processes': all_processes,
            'all_users': all_users,
            'active_tab': 'validation',
        })

    # Case 2: Request is currently at a DIFFERENT process (preceding or future)
    if active_request.current_process and active_request.current_process.code != target_process.code:
        # Check if request is currently at a preceding process (e.g. P10 when user is P30)
        if active_request.current_process.sequence < target_process.sequence:
            return render(request, 'operator_please_wait.html', {
                'current_user': user,
                'target_process': target_process,
                'active_request': active_request,
                'all_processes': all_processes,
                'all_users': all_users,
                'active_tab': 'validation',
            })
        elif active_request.current_process.sequence > target_process.sequence:
            # Request already passed this process!
            return render(request, 'operator_passed_notice.html', {
                'current_user': user,
                'target_process': target_process,
                'active_request': active_request,
                'all_processes': all_processes,
                'all_users': all_users,
                'active_tab': 'validation',
            })

    # Case 3: Request is AT target process! Check if PAUSED or STOPPED
    if active_request.status == 'PAUSED':
        return render(request, 'operator_request_paused.html', {
            'current_user': user,
            'target_process': target_process,
            'active_request': active_request,
            'all_processes': all_processes,
            'all_users': all_users,
            'active_tab': 'validation',
        })

    # Case 4: Request is IN_PROGRESS at target process -> Render full validation form
    barcode = active_request.barcode
    scenario = request.GET.get('scenario', 'SUCCESS')
    unit = ProductionService.get_or_create_unit(barcode)

    process_tabs = []
    for proc in all_processes:
        can_access = True
        if user.role == 'OPERATOR' and user.assigned_process and user.assigned_process.code != proc.code:
            can_access = False

        is_unlocked, unlock_msg = ValidationService.is_process_unlocked(unit, proc)
        passed = ProcessResult.objects.filter(production_unit=unit, process=proc, result='PASS').exists()
        failed = ProcessResult.objects.filter(production_unit=unit, process=proc, result='FAIL').exists()
        
        status = 'PENDING'
        if passed:
            status = 'COMPLETED'
        elif failed:
            status = 'FAILED'
        elif proc.code == process_code:
            status = 'CURRENT'
        elif not is_unlocked or not can_access:
            status = 'LOCKED'

        process_tabs.append({
            'process': proc,
            'is_unlocked': is_unlocked and can_access,
            'can_access': can_access,
            'status': status,
            'unlock_msg': unlock_msg if is_unlocked else "Prerequisite process incomplete",
        })

    is_current_unlocked, current_unlock_msg = ValidationService.is_process_unlocked(unit, target_process)
    demo_data = DemoScenarioService.get_demo_data(process_code, scenario, barcode)

    context = {
        'target_process': target_process,
        'process_tabs': process_tabs,
        'unit': unit,
        'active_request': active_request,
        'demo_data': demo_data,
        'scenario': scenario,
        'is_unlocked': is_current_unlocked,
        'unlock_msg': current_unlock_msg,
        'active_tab': 'validation',
        'current_user': user,
        'all_users': all_users,
    }
    return render(request, 'process_validation.html', context)


def api_get_demo_scenario(request):
    process_code = request.GET.get('process_code', 'P10')
    scenario = request.GET.get('scenario', 'SUCCESS')
    barcode = request.GET.get('barcode', 'DEMO20260924-001')

    data = DemoScenarioService.get_demo_data(process_code, scenario, barcode)
    return JsonResponse({'status': 'ok', 'data': data})


@csrf_exempt
def api_submit_process_result(request):
    if request.method == 'POST':
        try:
            user = get_current_user(request)
            if not user:
                return JsonResponse({'status': 'error', 'message': 'Unauthenticated'}, status=401)

            body = json.loads(request.body.decode('utf-8'))
            barcode = body.get('barcode')
            process_code = body.get('process_code')
            demo_result = body.get('demo_result', 'SUCCESS')
            options_data = body.get('options_data', {})
            subparts_data = body.get('subparts_data', [])
            screws_data = body.get('screws_data', [])
            operator_id = user.operator_id

            unit = ProductionService.get_or_create_unit(barcode)
            process = get_object_or_404(Process, code=process_code)

            if demo_result == 'SUCCESS':
                result_status = 'PASS'
                failure_reason = ''
            else:
                result_status = 'FAIL'
                failure_reason = body.get('failure_reason', 'Manual NG trigger in demo mode.')

            res_obj = ProductionService.record_process_result(
                unit=unit,
                process=process,
                result_status=result_status,
                options_data=options_data,
                subparts_data=subparts_data,
                screws_data=screws_data,
                failure_reason=failure_reason,
                operator_id=operator_id
            )

            # Update ProductionRequest stage if PASS
            active_req = ProductionRequest.objects.filter(barcode=barcode).first()
            next_proc = Process.objects.filter(sequence=process.sequence + 1).first()

            if active_req and result_status == 'PASS':
                if next_proc:
                    active_req.current_process = next_proc
                    # Find next operator assigned to next process
                    next_op = OperatorUser.objects.filter(assigned_process=next_proc).first()
                    active_req.assigned_operator = next_op
                    active_req.save()
                else:
                    active_req.status = 'COMPLETED'
                    active_req.save()

            next_code = None
            if next_proc and result_status == 'PASS':
                if user.role == 'ADMIN' or (user.assigned_process and user.assigned_process.code == next_proc.code):
                    next_code = next_proc.code

            return JsonResponse({
                'status': 'ok',
                'result': result_status,
                'next_process': next_code,
                'unit_status': unit.status,
                'message': f"Process {process.code} result recorded as {result_status} by {user.full_name}."
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_admin_request_action(request):
    """API for Admin control over production requests (Pause, Stop, Pass to Next, Assign)."""
    user = get_current_user(request)
    if not user or user.role != 'ADMIN':
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403)

    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            action = body.get('action')
            req_id = body.get('request_id')

            req_obj = ProductionRequest.objects.filter(request_id=req_id).first()
            if not req_obj and action != 'create':
                return JsonResponse({'status': 'error', 'message': 'Request not found'}, status=404)

            if action == 'pause':
                if req_obj.status == 'PAUSED':
                    req_obj.status = 'IN_PROGRESS'
                else:
                    req_obj.status = 'PAUSED'
                req_obj.save()
            elif action == 'stop':
                req_obj.status = 'STOPPED'
                req_obj.save()
            elif action == 'pass_next':
                current_p = req_obj.current_process
                next_p = Process.objects.filter(sequence=current_p.sequence + 1).first() if current_p else None
                if next_p:
                    req_obj.current_process = next_p
                    req_obj.assigned_operator = OperatorUser.objects.filter(assigned_process=next_p).first()
                    req_obj.status = 'IN_PROGRESS'
                    req_obj.save()
                else:
                    req_obj.status = 'COMPLETED'
                    req_obj.save()
            elif action == 'assign':
                first_p = Process.objects.filter(sequence=1).first()
                req_obj.current_process = first_p
                req_obj.assigned_operator = OperatorUser.objects.filter(assigned_process=first_p).first()
                req_obj.status = 'IN_PROGRESS'
                req_obj.save()
            elif action == 'create':
                num = ProductionRequest.objects.count() + 1
                date_str = timezone.now().strftime('%Y%m%d')
                new_req_id = f"REQ-{date_str}-{num:03d}"
                new_bc = f"DEMO{date_str}-{num:03d}"
                first_p = Process.objects.filter(sequence=1).first()
                op_p10 = OperatorUser.objects.filter(assigned_process=first_p).first()
                
                req_obj = ProductionRequest.objects.create(
                    request_id=new_req_id,
                    barcode=new_bc,
                    car_type='MQ4i',
                    alc='B81V',
                    priority='HIGH',
                    status='IN_PROGRESS',
                    current_process=first_p,
                    assigned_operator=op_p10
                )

            return JsonResponse({
                'status': 'ok',
                'message': f"Request action '{action}' executed successfully.",
                'new_status': req_obj.status if req_obj else 'CREATED'
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)


@csrf_exempt
def api_generate_barcode(request):
    import random
    num = random.randint(100, 999)
    date_str = timezone.now().strftime('%Y%m%d')
    new_barcode = f"DEMO{date_str}-{num}"
    ProductionService.get_or_create_unit(new_barcode)
    return JsonResponse({'status': 'ok', 'barcode': new_barcode})


def reports_view(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    results = ProcessResult.objects.all().select_related('production_unit', 'process').order_by('-timestamp')
    processes = Process.objects.filter(is_active=True).order_by('sequence')
    all_users = OperatorUser.objects.all().select_related('assigned_process')

    process_filter = request.GET.get('process')
    if process_filter:
        results = results.filter(process__code=process_filter)

    result_filter = request.GET.get('result')
    if result_filter:
        results = results.filter(result=result_filter)

    q = request.GET.get('q')
    if q:
        results = results.filter(production_unit__barcode__icontains=q) | results.filter(production_unit__part_no__icontains=q)

    context = {
        'results': results,
        'processes': processes,
        'active_tab': 'reports',
        'current_user': user,
        'all_users': all_users,
        'current_process_filter': process_filter or '',
        'current_result_filter': result_filter or '',
        'search_query': q or '',
    }
    return render(request, 'reports.html', context)


def export_excel_view(request):
    wb = ReportService.export_work_history_excel()
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="KIA_Floor_Work_History.xlsx"'
    wb.save(response)
    return response


def settings_view(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')
    if user.role == 'OPERATOR':
        if user.assigned_process:
            return redirect('process_validation', process_code=user.assigned_process.code)

    settings_obj, _ = SystemSettings.objects.get_or_create(id=1)
    processes = Process.objects.all().order_by('sequence')
    all_users = OperatorUser.objects.all().select_related('assigned_process')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save_db_settings':
            settings_obj.db_server_ip = request.POST.get('db_server_ip', '192.168.0.122')
            settings_obj.db_port = int(request.POST.get('db_port', 1433))
            settings_obj.db_name = request.POST.get('db_name', 'INDIA_FLOOR_KY1')
            settings_obj.db_username = request.POST.get('db_username', 'sa')
            settings_obj.db_password = request.POST.get('db_password', '')
            settings_obj.save()
            AuditLog.objects.create(
                operator=user.operator_id,
                action='UPDATE_DB_SETTINGS',
                details=f"Updated database connection: {settings_obj.db_server_ip}:{settings_obj.db_port}"
            )
        elif action == 'save_process_config':
            for proc in processes:
                seq_val = request.POST.get(f'seq_{proc.id}')
                dep_val = request.POST.get(f'dep_{proc.id}')
                active_val = request.POST.get(f'active_{proc.id}') == 'on'

                if seq_val:
                    proc.sequence = int(seq_val)
                if dep_val and dep_val != 'none':
                    proc.before_process = Process.objects.filter(id=int(dep_val)).first()
                else:
                    proc.before_process = None
                proc.is_active = active_val
                proc.save()
            return redirect('settings')

    context = {
        'settings': settings_obj,
        'processes': processes,
        'active_tab': 'settings',
        'current_user': user,
        'all_users': all_users,
    }
    return render(request, 'settings.html', context)


def users_view(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    all_users = OperatorUser.objects.all().select_related('assigned_process')
    processes = Process.objects.filter(is_active=True).order_by('sequence')
    production_units = ProductionUnit.objects.all().select_related('current_process')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_user':
            username = request.POST.get('username')
            full_name = request.POST.get('full_name')
            operator_id = request.POST.get('operator_id')
            role = request.POST.get('role', 'OPERATOR')
            proc_id = request.POST.get('assigned_process')
            station_code = request.POST.get('station_code', 'ST-01')

            assigned_proc = Process.objects.filter(id=proc_id).first() if proc_id and proc_id != 'none' else None

            OperatorUser.objects.create(
                username=username,
                full_name=full_name,
                operator_id=operator_id,
                role=role,
                assigned_process=assigned_proc,
                station_code=station_code
            )
            return redirect('users')

    context = {
        'current_user': user,
        'all_users': all_users,
        'processes': processes,
        'production_units': production_units,
        'active_tab': 'users',
    }
    return render(request, 'users.html', context)


def admin_set_stage_view(request):
    user = get_current_user(request)
    if user and user.role == 'ADMIN' and request.method == 'POST':
        action = request.POST.get('action')
        if action == 'set_stage':
            barcode = request.POST.get('barcode')
            target_stage_code = request.POST.get('target_stage')
            unit = ProductionUnit.objects.filter(barcode=barcode).first()
            target_proc = Process.objects.filter(code=target_stage_code).first()
            if unit and target_proc:
                unit.current_process = target_proc
                unit.status = 'IN_PROGRESS'
                unit.save()

                # Update active request as well
                req = ProductionRequest.objects.filter(barcode=barcode).first()
                if req:
                    req.current_process = target_proc
                    req.assigned_operator = OperatorUser.objects.filter(assigned_process=target_proc).first()
                    req.status = 'IN_PROGRESS'
                    req.save()

                AuditLog.objects.create(
                    operator=user.operator_id,
                    action='ADMIN_SET_STAGE',
                    details=f"Admin set stage for {barcode} to {target_stage_code}"
                )
        elif action == 'reset_all':
            ProcessResult.objects.all().delete()
            first_proc = Process.objects.filter(sequence=1).first()
            ProductionUnit.objects.all().update(status='IN_PROGRESS', current_process=first_proc)
            
            # Reset requests to start
            op_p10 = OperatorUser.objects.filter(assigned_process=first_proc).first()
            ProductionRequest.objects.all().update(status='WAITING')
            first_req = ProductionRequest.objects.first()
            if first_req:
                first_req.status = 'IN_PROGRESS'
                first_req.current_process = first_proc
                first_req.assigned_operator = op_p10
                first_req.save()

            AuditLog.objects.create(
                operator=user.operator_id,
                action='ADMIN_RESET_DEMO',
                details="Admin reset all demo process results and production unit stages."
            )
    return redirect('users')


@csrf_exempt
def api_switch_user(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = OperatorUser.objects.filter(id=user_id).first()
        if not user:
            op_id = request.POST.get('operator_id')
            user = OperatorUser.objects.filter(operator_id=op_id).first()
        if user:
            request.session['user_id'] = user.id
            target_url = '/dashboard/'
            if user.role == 'OPERATOR' and user.assigned_process:
                target_url = f'/validation/{user.assigned_process.code}/'
            return JsonResponse({
                'status': 'ok',
                'user_id': user.id,
                'full_name': user.full_name,
                'role': user.role,
                'target_url': target_url
            })
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


api_switch_operator = api_switch_user
