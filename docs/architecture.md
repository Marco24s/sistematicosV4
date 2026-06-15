# Arquitectura SISTEMATICOS V4

## Bounded contexts iniciales

- Configuration: catalogos configurables de modelos de aeronave, motores, tipos de componentes y reglas de compatibilidad.
- Assets: aeronaves, motores, componentes instalados e historial individual.
- Maintenance: mantenimiento preventivo, correctivo y pedidos de trabajo.
- Documents: certificados, documentacion tecnica, boletines, registros y evidencias.
- Logistics: cadena interna, almacenes, pedidos, reservas y movimientos.
- Quality: inspecciones, liberaciones, rechazos y conformidad tecnica.
- Engineering: reparaciones, evaluaciones tecnicas y desviaciones autorizadas.
- Personnel: habilitaciones, firmas, roles tecnicos y vencimientos de calificaciones.

## DDD

Cada modulo separa:

- domain: entidades, value objects, reglas y eventos de dominio.
- application: casos de uso, DTOs y orquestacion.
- infrastructure: persistencia, integraciones y adaptadores.
- api: routers REST.

## Event Driven Architecture

La primera version incluye un bus en memoria para eventos de dominio. Cuando el sistema crezca, puede reemplazarse por PostgreSQL outbox, RabbitMQ, Kafka o NATS sin cambiar el lenguaje del dominio.

Eventos iniciales:

- aircraft.registered
- component.registered
- component.installed
- component.removed
- airworthiness.assessed
- work_order.opened
- quality.release.approved
- quality.release.rejected

## Regla central de aeronavegabilidad

Una aeronave no debe operar si:

- algun componente instalado no esta serviceable;
- un componente requerido no tiene certificado tecnico;
- se supero limite de horas;
- se supero limite de ciclos;
- se vencio la vida calendario;
- existen ordenes de trabajo abiertas bloqueantes;
- calidad no libero la intervencion requerida;
- el personal firmante no tiene habilitacion vigente.

## Configuracion desde base de datos

No se codifican modelos de aeronaves ni motores en el codigo. Se administran mediante endpoints y tablas:

- aircraft_models
- engine_models
- component_types
- aircraft_model_allowed_components
