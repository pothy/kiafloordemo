from django.db import models
from django.utils import timezone


class Process(models.Model):
    code = models.CharField(max_length=10, unique=True)  # P10, P30, P40, P50, P60, P41, P51
    name = models.CharField(max_length=100)  # Assembly #10, Garnish, Rear Cover, etc.
    sequence = models.IntegerField(default=1)
    before_process = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True, related_name='next_processes'
    )
    check_required = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    image_name = models.CharField(max_length=100, default='kia_console_assembly.png')

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"{self.code} - {self.name}"


class ProcessField(models.Model):
    FIELD_TYPES = (
        ('text', 'Text Input'),
        ('select', 'Dropdown Select'),
        ('number', 'Number Input'),
    )
    process = models.ForeignKey(Process, on_delete=models.CASCADE, related_name='fields')
    field_key = models.CharField(max_length=50)
    label = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES, default='select')
    sequence = models.IntegerField(default=1)
    options_json = models.JSONField(default=list, blank=True)
    is_required = models.BooleanField(default=True)

    class Meta:
        ordering = ['sequence']

    def __str__(self):
        return f"{self.process.code} - {self.label}"


class OperatorUser(models.Model):
    ROLE_CHOICES = (
        ('ADMIN', 'System Administrator'),
        ('OPERATOR', 'Station Operator'),
    )
    username = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    operator_id = models.CharField(max_length=20, unique=True)
    password_text = models.CharField(max_length=50, default='password')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OPERATOR')
    assigned_process = models.ForeignKey(Process, on_delete=models.SET_NULL, null=True, blank=True)
    station_code = models.CharField(max_length=20, default='ST-01')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)


    class Meta:
        ordering = ['role', 'operator_id']

    def __str__(self):
        proc_str = f" ({self.assigned_process.code})" if self.assigned_process else " (ADMIN)"
        return f"{self.full_name} [{self.operator_id}]{proc_str}"


class ProductionRequest(models.Model):
    STATUS_CHOICES = (
        ('WAITING', 'Waiting'),
        ('IN_PROGRESS', 'In Progress'),
        ('PAUSED', 'Paused'),
        ('STOPPED', 'Stopped'),
        ('COMPLETED', 'Completed'),
    )
    PRIORITY_CHOICES = (
        ('HIGH', 'High'),
        ('NORMAL', 'Normal'),
        ('LOW', 'Low'),
    )
    request_id = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=50)
    car_type = models.CharField(max_length=50, default='MQ4i')
    alc = models.CharField(max_length=50, default='B81V')
    part_no = models.CharField(max_length=100, default='84605-GB810FHV')
    lot_no = models.CharField(max_length=50, default='LOT20260924-01')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='NORMAL')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='WAITING')
    current_process = models.ForeignKey(Process, on_delete=models.SET_NULL, null=True, blank=True)
    assigned_operator = models.ForeignKey(OperatorUser, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.request_id} [{self.status}] - {self.current_process.code if self.current_process else 'NONE'}"


class ProductionUnit(models.Model):
    STATUS_CHOICES = (
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed / NG'),
    )
    barcode = models.CharField(max_length=50, unique=True)
    car_type = models.CharField(max_length=50, default='MQ4i')
    alc = models.CharField(max_length=50, default='B81V')
    part_no = models.CharField(max_length=100, default='84605-GB810FHV')
    lot_no = models.CharField(max_length=50, default='LOT20260924-01')
    order_qty = models.IntegerField(default=120)
    production_qty = models.IntegerField(default=42)
    current_process = models.ForeignKey(Process, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='IN_PROGRESS')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.barcode} ({self.car_type})"


class ProcessResult(models.Model):
    RESULT_CHOICES = (
        ('PASS', 'PASS'),
        ('FAIL', 'FAIL'),
    )
    production_unit = models.ForeignKey(ProductionUnit, on_delete=models.CASCADE, related_name='results')
    process = models.ForeignKey(Process, on_delete=models.CASCADE)
    operator_id = models.CharField(max_length=50, default='001')
    result = models.CharField(max_length=10, choices=RESULT_CHOICES)
    options_data = models.JSONField(default=dict)
    subparts_data = models.JSONField(default=list)
    screws_data = models.JSONField(default=list)
    failure_reason = models.TextField(blank=True, null=True)
    rework_mode = models.BooleanField(default=False)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.production_unit.barcode} | {self.process.code} | {self.result}"


class AuditLog(models.Model):
    operator = models.CharField(max_length=50)
    action = models.CharField(max_length=100)
    details = models.TextField()
    ip_address = models.CharField(max_length=50, default='127.0.0.1')
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-timestamp']


class SystemSettings(models.Model):
    db_server_ip = models.CharField(max_length=100, default='192.168.0.122')
    db_port = models.IntegerField(default=1433)
    db_name = models.CharField(max_length=100, default='INDIA_FLOOR_KY1')
    db_username = models.CharField(max_length=100, default='sa')
    db_password = models.CharField(max_length=100, default='••••••••')
    scanner_sim_enabled = models.BooleanField(default=True)
    plc_sim_enabled = models.BooleanField(default=True)
    screw_sim_enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"System Config ({self.db_name})"
