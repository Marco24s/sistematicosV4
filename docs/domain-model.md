# Modelo de dominio inicial

## Aircraft

Representa una aeronave identificable por matricula y numero de serie. Su modelo proviene de `aircraft_models`.

## Engine

Representa un motor con numero de serie propio. Su modelo proviene de `engine_models` y puede estar instalado en una aeronave.

## Component

Representa un componente individual trazable. No es solo un stock item: tiene serial, part number, certificado, condicion, vida consumida y posible instalacion.

## ComponentType

Define reglas configurables: si requiere certificado, limite de horas, limite de ciclos y limite calendario.

## WorkOrder

Pedido de trabajo tecnico. Puede ser preventivo, correctivo o reparacion de ingenieria.

## AirworthinessPolicy

Servicio de dominio que evalua si una aeronave puede considerarse aeronavegable a partir de sus componentes instalados y sus reglas.
