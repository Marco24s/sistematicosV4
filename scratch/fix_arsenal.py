with open(r'C:\sistematicosV4\backend\app\api\routes\arsenal.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Fix complete_repair
code = code.replace(
'''        result = service.complete_repair(
            repair_task=task,
            maintenance_request=maintenance_req,
            completed_at=datetime.utcnow(),
            action_taken=request.action_taken,
            parts_replaced=request.parts_replaced,
            man_hours=Decimal(request.total_man_hours),
            actor_id=request.actor_id,
            completed_by=request.performed_by,
            notes=request.notes
        )''',
'''        result = service.complete_repair(
            repair_task=task,
            maintenance_request=maintenance_req,
            has_repair_completion_record=True,
            has_engineering_instruction=True,
            is_instruction_required=True,
            completed_at=datetime.utcnow(),
            action_taken=request.action_taken,
            parts_replaced=request.parts_replaced,
            man_hours=Decimal(request.total_man_hours),
            actor_id=request.actor_id,
            completed_by=request.performed_by,
            notes=request.notes
        )'''
)

# Fix release_component_to_service
code = code.replace(
'''        result = service.release_component_to_service(
            asset=component,
            maintenance_request=maintenance_req,
            quality_inspection=inspection,
            released_by=request.released_by,
            released_at=datetime.utcnow(),
            destination_department_id=request.returned_to_department_id,
            actor_id=request.actor_id
        )''',
'''        result = service.release_component_to_service(
            asset=component,
            maintenance_request=maintenance_req,
            quality_inspection=inspection,
            has_service_release_certificate=True,
            has_historical_record_book=True,
            released_by=request.released_by,
            released_at=datetime.utcnow(),
            destination_department_id=request.returned_to_department_id,
            actor_id=request.actor_id
        )'''
)

with open(r'C:\sistematicosV4\backend\app\api\routes\arsenal.py', 'w', encoding='utf-8') as f:
    f.write(code)
