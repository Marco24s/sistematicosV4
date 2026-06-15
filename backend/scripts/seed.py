import sys
from uuid import uuid4
from sqlalchemy.orm import Session

# Import all models to ensure SQLAlchemy's registry is populated
from app.modules.arsenal_workflow.domain import models as arsenal_workflow_models
from app.modules.assets.domain import models as asset_models
from app.modules.document_management.domain import models as document_management_models
from app.modules.flight_operations.domain import models as flight_operations_models
from app.modules.maintenance.domain import models as maintenance_models
from app.modules.organization.domain import models as organization_models
from app.modules.personnel_certification.domain import models as personnel_certification_models
from app.modules.squadron_operations.domain import models as squadron_operations_models
from app.modules.supply_chain.domain import models as supply_chain_models
from app.shared.infrastructure import event_store as event_store_models
from app.modules.workflow_orchestration.domain import models as workflow_models
from app.modules.tool_calibration.domain import models as tool_calibration_models
from app.modules.authorization.domain import models as authorization_models
from app.modules.engine_management.domain import models as engine_management_models
from app.modules.reporting_analytics.domain import models as reporting_analytics_models
from app.modules.flight_release_control.domain import models as flight_release_control_models
from app.modules.airworthiness_engine.domain import models as airworthiness_engine_models
from app.modules.disposal_management.domain import models as disposal_management_models
from app.modules.asset_reallocation.domain import models as asset_reallocation_models
from app.modules.configuration_baseline.domain import models as configuration_baseline_models
from app.modules.structural_fatigue.domain import models as structural_fatigue_models
from app.modules.maintenance_human_factors.domain import models as maintenance_human_factors_models
from app.modules.reliability_engine.domain import models as reliability_engine_models
from app.modules.fod_management.domain import models as fod_management_models

from app.core.database import SessionLocal, Base, engine
from app.modules.organization.domain.models import Organization, OrganizationType, Department, DepartmentType
from app.modules.assets.domain.models import Asset, AssetType, AssetCondition, AssetStatus, AssetClassification
from app.modules.engine_management.domain.models import EngineAssembly


def seed_data():
    # Recreate all tables using populated metadata
    Base.metadata.create_all(bind=engine)
    
    db: Session = SessionLocal()
    try:
        print("Iniciando la carga de datos (seeding)...")
        
        # 0. Crear Tipos Documentales Obligatorios
        from app.modules.document_management.domain.models import DocumentType
        mandatory_docs = [
            "Flight Sheet", "Failure Report", "Maintenance Action Form", 
            "Work Order", "Engineering Instruction", "Repair Completion Record", 
            "Service Release Certificate", "Historical Record Book"
        ]
        for dname in mandatory_docs:
            dt = db.query(DocumentType).filter_by(name=dname).first()
            if not dt:
                db.add(DocumentType(id=uuid4(), name=dname, mandatory=True, description=f"Documento obligatorio: {dname}"))
        db.commit()
        print("Tipos Documentales sembrados.")
        
        # 1. Crear Organización Principal
        comando = db.query(Organization).filter_by(name="Comando Aviación Naval").first()
        if not comando:
            comando = Organization(
                id=uuid4(),
                name="Comando Aviación Naval",
                organization_type=OrganizationType.ARSENAL
            )
            db.add(comando)
            db.commit()
            db.refresh(comando)
            print("Creado: Comando Aviación Naval")
        else:
            print("Ya existe: Comando Aviación Naval")

        # 2. Crear Unidades (Escuadrillas)
        unidades_nombres = [
            "Segunda Escuadrilla Aeronaval de Helicópteros",
            "Escuadrilla Aeronaval Antisubmarina",
            "Escuadrilla Aeronaval de Caza y Ataque"
        ]
        
        unidades = {}
        for nombre in unidades_nombres:
            org = db.query(Organization).filter_by(name=nombre).first()
            if not org:
                org = Organization(
                    id=uuid4(),
                    name=nombre,
                    organization_type=OrganizationType.SQUADRON
                )
                db.add(org)
                db.commit()
                db.refresh(org)
                print(f"Creado Unidad: {nombre}")
            else:
                print(f"Ya existe Unidad: {nombre}")
            unidades[nombre] = org

        # 3. Crear Secciones (Departamentos) para cada Unidad y el Comando
        secciones_mapping = [
            ("Motores", DepartmentType.ENGINES),
            ("Hidráulica", DepartmentType.HYDRAULICS),
            ("Ingeniería", DepartmentType.ENGINEERING),
            ("Calidad", DepartmentType.QUALITY),
            ("Electricidad", DepartmentType.ELECTRICAL_ACCESSORIES),
            ("Compras", DepartmentType.PROCUREMENT)
        ]

        all_orgs = [comando] + list(unidades.values())
        for org in all_orgs:
            for sec_name, sec_type in secciones_mapping:
                dep = db.query(Department).filter_by(organization_id=org.id, name=sec_name).first()
                if not dep:
                    dep = Department(
                        id=uuid4(),
                        organization_id=org.id,
                        name=sec_name,
                        department_type=sec_type
                    )
                    db.add(dep)
                    print(f"Creado Sección '{sec_name}' para {org.name}")
            db.commit()

        # 4. Crear Categorías de Componentes (AssetTypes)
        aircraft_type = db.query(AssetType).filter_by(category="AIRCRAFT").first()
        if not aircraft_type:
            aircraft_type = AssetType(
                id=uuid4(),
                name="Aeronave Militar",
                category="AIRCRAFT"
            )
            db.add(aircraft_type)
            db.commit()
            db.refresh(aircraft_type)
            print("Creado Tipo: Aeronave Militar")

        engine_type = db.query(AssetType).filter_by(category="ENGINE").first()
        if not engine_type:
            engine_type = AssetType(
                id=uuid4(),
                name="Motor Aeronáutico",
                category="ENGINE"
            )
            db.add(engine_type)
            db.commit()
            db.refresh(engine_type)
            print("Creado Tipo: Motor Aeronáutico")

        # 5. Crear Aeronaves (Assets)
        aeronaves_data = [
            ("Sikorsky SH-3 Sea King", "SH3-01", "2-H-231"),
            ("Grumman S-2 Tracker", "S2-01", "2-AS-23"),
            ("Super Étendard Modernisé", "SEM-01", "3-A-201")
        ]

        for nomenclature, part_no, serial in aeronaves_data:
            existing_aircraft = db.query(Asset).filter_by(serial_number=serial).first()
            if not existing_aircraft:
                aircraft = Asset(
                    id=uuid4(),
                    asset_type_id=aircraft_type.id,
                    part_number=part_no,
                    serial_number=serial,
                    nomenclature=nomenclature,
                    condition=AssetCondition.SERVICEABLE,
                    current_status=AssetStatus.RELEASED,
                    classification=AssetClassification.REPAIRABLE
                )
                db.add(aircraft)
                print(f"Creada Aeronave: {nomenclature} ({serial})")
            else:
                print(f"Ya existe Aeronave: {nomenclature} ({serial})")
        db.commit()

        # 6. Crear Motores (Assets y EngineAssemblies)
        motores_data = [
            ("T58-GE-10", "T58-01", "ENG-T58-991"),
            ("Allison 501", "AL-501", "ENG-AL-442"),
            ("Atar 8K50", "AT-8K50", "ENG-ATAR-502")
        ]

        for nomenclature, part_no, serial in motores_data:
            existing_engine_asset = db.query(Asset).filter_by(serial_number=serial).first()
            if not existing_engine_asset:
                engine_asset = Asset(
                    id=uuid4(),
                    asset_type_id=engine_type.id,
                    part_number=part_no,
                    serial_number=serial,
                    nomenclature=nomenclature,
                    condition=AssetCondition.SERVICEABLE,
                    current_status=AssetStatus.RELEASED,
                    classification=AssetClassification.REPAIRABLE
                )
                db.add(engine_asset)
                db.commit()
                db.refresh(engine_asset)
                print(f"Creado Asset de Motor: {nomenclature} ({serial})")
            else:
                engine_asset = existing_engine_asset

            existing_assembly = db.query(EngineAssembly).filter_by(serial_number=serial).first()
            if not existing_assembly:
                assembly = EngineAssembly(
                    id=uuid4(),
                    asset_id=engine_asset.id,
                    engine_model=nomenclature,
                    serial_number=serial
                )
                db.add(assembly)
                print(f"Creado EngineAssembly: {nomenclature} ({serial})")
            else:
                print(f"Ya existe EngineAssembly: {nomenclature} ({serial})")
        db.commit()

        # 7. Crear Personal de Mantenimiento e Inspectores con Certificaciones y Firmas
        from datetime import datetime, date, timedelta
        from decimal import Decimal
        from app.modules.personnel_certification.domain.models import (
            TechnicianProfile,
            TechnicianCertification,
            CertificationLevel,
            TechnicalSpecialization,
        )
        from app.modules.authorization.domain.models import DigitalSignatureCertificate
        from app.modules.tool_calibration.domain.models import Tool, CalibrationCertificate

        # Especialidad Hidráulica
        specialization = db.query(TechnicalSpecialization).filter_by(name="HYDRAULIC_SYSTEMS").first()
        if not specialization:
            specialization = TechnicalSpecialization(
                id=uuid4(),
                name="HYDRAULIC_SYSTEMS",
                description="Habilitación para sistemas hidráulicos y mandos de vuelo."
            )
            db.add(specialization)
            db.commit()
            print("Creada Especialidad: HYDRAULIC_SYSTEMS")

        # Técnico LEVEL_B
        tech = db.query(TechnicianProfile).filter_by(technical_code="TECH-801").first()
        if not tech:
            tech = TechnicianProfile(
                id=uuid4(),
                personnel_id=uuid4(),
                technical_code="TECH-801",
                join_date=date.today() - timedelta(days=500),
                current_level=CertificationLevel.LEVEL_B,
                years_of_experience=Decimal("3.50"),
                active=True
            )
            db.add(tech)
            db.commit()
            print("Creado Perfil Técnico: TECH-801")

            # Certificación para el técnico
            tech_cert = TechnicianCertification(
                id=uuid4(),
                technician_profile_id=tech.id,
                specialization_id=specialization.id,
                certification_level=CertificationLevel.LEVEL_B,
                issued_date=date.today() - timedelta(days=100),
                expiration_date=date.today() + timedelta(days=250),
                issued_by="División Calidad",
                active=True
            )
            db.add(tech_cert)
            db.commit()
            print("Creada Certificación Hidráulica para TECH-801")

        # Inspector
        inspector = db.query(TechnicianProfile).filter_by(technical_code="INSP-901").first()
        if not inspector:
            inspector = TechnicianProfile(
                id=uuid4(),
                personnel_id=uuid4(),
                technical_code="INSP-901",
                join_date=date.today() - timedelta(days=1200),
                current_level=CertificationLevel.INSPECTOR,
                years_of_experience=Decimal("8.50"),
                active=True
            )
            db.add(inspector)
            db.commit()
            print("Creado Perfil Inspector: INSP-901")

            # Certificación para el inspector
            inspector_cert = TechnicianCertification(
                id=uuid4(),
                technician_profile_id=inspector.id,
                specialization_id=specialization.id,
                certification_level=CertificationLevel.INSPECTOR,
                issued_date=date.today() - timedelta(days=200),
                expiration_date=date.today() + timedelta(days=350),
                issued_by="División Calidad",
                active=True
            )
            db.add(inspector_cert)

            # Firma digital activa para el inspector
            inspector_sig = DigitalSignatureCertificate(
                id=uuid4(),
                user_id=inspector.id,
                certificate_serial="SIG-INSP-901",
                issued_at=datetime.utcnow() - timedelta(days=15),
                expires_at=datetime.utcnow() + timedelta(days=350),
                active=True
            )
            db.add(inspector_sig)
            db.commit()
            print("Creada Certificación y Firma Digital para INSP-901")

        # 8. Crear Herramientas Calibradas
        tool = db.query(Tool).filter_by(tool_serial="TQ-M-112").first()
        if not tool:
            tool = Tool(
                id=uuid4(),
                tool_serial="TQ-M-112",
                name="Torquímetro de Click 1/2 pulgada",
                active=True
            )
            db.add(tool)
            db.commit()
            print("Creada Herramienta: TQ-M-112")

            tool_cal = CalibrationCertificate(
                id=uuid4(),
                tool_id=tool.id,
                calibration_date=date.today() - timedelta(days=15),
                calibration_due_date=date.today() + timedelta(days=165),
                certification_document_code="CERT-CAL-112"
            )
            db.add(tool_cal)
            db.commit()
            print("Creado Certificado de Calibración para TQ-M-112")

        # 9. Crear RBAC: Permisos, Roles, y SystemUsers
        from app.modules.authorization.domain.models import SystemUser, UserAssignment, OrganizationRole, Permission
        import bcrypt

        # Permisos base (extraídos de policies.py)
        perms = [
            "CREATE_MISSION", "CLOSE_FLIGHT", "INSTALL_COMPONENT", "VALIDATE_FLIGHT_RELEASE", 
            "AUTHORIZE_REPAIR_TASK", "APPROVE_QUALITY_INSPECTION", "ISSUE_AIRWORTHINESS_BLOCK", 
            "APPROVE_PURCHASE_ORDER"
        ]
        db_perms = {}
        for p in perms:
            perm = db.query(Permission).filter_by(name=p).first()
            if not perm:
                perm = Permission(id=uuid4(), name=p)
                db.add(perm)
            db_perms[p] = perm
        db.commit()

        # Roles
        roles_config = {
            "COMMAND_OFFICER": ["CREATE_MISSION", "APPROVE_PURCHASE_ORDER"],
            "MAINTENANCE_CHIEF": ["VALIDATE_FLIGHT_RELEASE", "ISSUE_AIRWORTHINESS_BLOCK", "AUTHORIZE_REPAIR_TASK"],
            "INSPECTOR": ["APPROVE_QUALITY_INSPECTION", "VALIDATE_FLIGHT_RELEASE"],
            "TECHNICIAN": ["CLOSE_FLIGHT", "INSTALL_COMPONENT"]
        }
        db_roles = {}
        for role_name, role_perms in roles_config.items():
            role = db.query(OrganizationRole).filter_by(name=role_name).first()
            if not role:
                role = OrganizationRole(id=uuid4(), name=role_name)
                db.add(role)
            # Assign perms
            for p_name in role_perms:
                if db_perms[p_name] not in role.permissions:
                    role.permissions.append(db_perms[p_name])
            db_roles[role_name] = role
        db.commit()

        # Users and Assignments
        users_config = [
            ("comando", "comando123", "COMMAND_OFFICER", comando.id, comando.id), # just map to Comando for testing
            ("jefe", "jefe123", "MAINTENANCE_CHIEF", unidades["Segunda Escuadrilla Aeronaval de Helicópteros"].id, unidades["Segunda Escuadrilla Aeronaval de Helicópteros"].id),
            ("inspector", "inspector123", "INSPECTOR", unidades["Segunda Escuadrilla Aeronaval de Helicópteros"].id, unidades["Segunda Escuadrilla Aeronaval de Helicópteros"].id),
            ("tech", "tech123", "TECHNICIAN", unidades["Segunda Escuadrilla Aeronaval de Helicópteros"].id, unidades["Segunda Escuadrilla Aeronaval de Helicópteros"].id)
        ]

        for username, password, role_key, org_id, dep_id in users_config:
            user = db.query(SystemUser).filter_by(username=username).first()
            if not user:
                user = SystemUser(
                    id=uuid4(),
                    username=username,
                    password_hash=bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                    is_active=True
                )
                db.add(user)
                db.commit()
                db.refresh(user)
                print(f"Creado SystemUser: {username}")
                
            # Create UserAssignment if missing
            assignment = db.query(UserAssignment).filter_by(user_id=user.id).first()
            if not assignment:
                assignment = UserAssignment(
                    id=uuid4(),
                    user_id=user.id,
                    organization_id=org_id,
                    department_id=dep_id,
                    role_id=db_roles[role_key].id,
                    active=True
                )
                db.add(assignment)
                db.commit()

        # Seed Procurement Components
        from app.modules.supply_chain.domain.models import Supplier, InventoryLocation, InventoryLocationType

        suppliers_data = [
            ("General Electric Aviation", "SUP-GE-001", "GE Defense Contact", "military@ge.com", "1-800-GE-DEF"),
            ("Safran Helicopters", "SUP-SAF-002", "Safran Sales", "sales@safran.fr", "+33 1 23 45 67")
        ]

        for name, code, contact, email, phone in suppliers_data:
            existing_sup = db.query(Supplier).filter_by(supplier_code=code).first()
            if not existing_sup:
                sup = Supplier(
                    id=uuid4(),
                    name=name,
                    supplier_code=code,
                    contact_name=contact,
                    email=email,
                    phone=phone,
                    active=True
                )
                db.add(sup)
                print(f"Creado Supplier: {name}")

        arsenal_storage = db.query(InventoryLocation).filter_by(location_type=InventoryLocationType.TECHNICAL_SECTION_STORAGE).first()
        if not arsenal_storage:
            ars_loc = InventoryLocation(
                id=uuid4(),
                name="Pañol Central de Arsenal",
                organization_id=comando.id,
                location_type=InventoryLocationType.TECHNICAL_SECTION_STORAGE,
                active=True
            )
            db.add(ars_loc)
            print("Creado InventoryLocation: Pañol Central de Arsenal")
            
        purchase_storage = db.query(InventoryLocation).filter_by(location_type=InventoryLocationType.PURCHASE_WAREHOUSE).first()
        if not purchase_storage:
            pur_loc = InventoryLocation(
                id=uuid4(),
                name="Depósito de Recepción Compras",
                organization_id=comando.id,
                location_type=InventoryLocationType.PURCHASE_WAREHOUSE,
                active=True
            )
            db.add(pur_loc)
            print("Creado InventoryLocation: Depósito de Recepción Compras")
            
        db.commit()

        print("Carga de datos iniciales finalizada con éxito.")

    except Exception as e:
        db.rollback()
        print(f"Error durante el seeding: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
