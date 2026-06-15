'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '../lib/api';

export default function Launchpad() {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState('');

  const consolas = [
    {
      id: 'supervision-sistema',
      nombre: 'COMMAND CENTER (MONITOREO GLOBAL)',
      descripcion: 'Monitoreo consolidado de flota, componentes, stock global, órdenes de trabajo y timeline de eventos en tiempo real.',
      ruta: '/supervision-sistema',
      rol: 'SUPERVISOR GLOBAL / COMMAND CENTER',
      username: 'jefe_supervision',
      password: 'pin_supervision',
      habilitada: true
    },
    {
      id: 'operaciones',
      nombre: '1. OPERATIONS CONSOLE',
      descripcion: 'Apertura y cierre de partes de vuelo, control de misiones y disponibilidad de dotación.',
      ruta: '/operaciones',
      rol: 'JEFE DE OPERACIONES / PILOTO',
      username: 'jefe_operaciones',
      password: 'pin_operaciones',
      habilitada: true
    },
    {
      id: 'mantenimiento-escuadron',
      nombre: '2. SQUADRON MAINTENANCE CONSOLE',
      descripcion: 'Reporte de fallas (grounding), tareas preventivas, remoción e instalación de componentes en hangar (O-Level).',
      ruta: '/mantenimiento-escuadron',
      rol: 'SUPERVISOR DE MANTENIMIENTO / MECÁNICO DE LÍNEA',
      username: 'mecanico_hangar',
      password: 'pin_mecanico',
      habilitada: true
    },
    {
      id: 'panol-escuadron',
      nombre: '3. SQUADRON STORAGE CONSOLE',
      descripcion: 'Gestión de stock local del escuadrón, componentes serviceable e inoperativos listos para envío al Arsenal.',
      ruta: '/panol-escuadron',
      rol: 'ENCARGADO DE PAÑOL DE ESCUADRÓN',
      username: 'panolero_escuadron',
      password: 'pin_panol_escuadron',
      habilitada: true
    },
    {
      id: 'panol-arsenal',
      nombre: '4. ARSENAL STORAGE CONSOLE',
      descripcion: 'Recepción física y documental de componentes inoperativos enviados por los escuadrones y custodia en Arsenal.',
      ruta: '/panol-arsenal',
      rol: 'ENCARGADO DE PAÑOL CENTRAL DE ARSENAL',
      username: 'panolero_arsenal',
      password: 'pin_panol_arsenal',
      habilitada: true
    },
    {
      id: 'taller-arsenal',
      nombre: '5. ARSENAL TECHNICAL CONSOLE',
      descripcion: 'Ejecución del procedimiento técnico en talleres del Arsenal (Motores, Hidráulica, Aviónica).',
      ruta: '/taller-arsenal',
      rol: 'JEFE DE TALLER / REPARADOR',
      username: 'mecanico_taller',
      password: 'pin_taller',
      habilitada: true
    },
    {
      id: 'control-calidad',
      nombre: '6. QUALITY CONTROL CONSOLE',
      descripcion: 'Inspección dual de seguridad de tareas críticas y firma digital de certificados de liberación.',
      ruta: '/control-calidad',
      rol: 'INSPECTOR DE CONTROL DE CALIDAD (DAC)',
      username: 'inspector_calidad',
      password: 'pin_inspector',
      habilitada: true
    },
    {
      id: 'estadisticas-escuadron',
      nombre: '7. SQUADRON STATISTICS CONSOLE',
      descripcion: 'Forecast de mantenimiento de célula, análisis de confiabilidad (MTBF, MTTR) e historial.',
      ruta: '/estadisticas-escuadron',
      rol: 'PLANIFICADOR DE ESTADÍSTICAS E CONFIBILIDAD',
      username: 'analista_estadisticas',
      password: 'pin_estadisticas',
      habilitada: true
    },
    {
      id: 'soporte-arsenal',
      nombre: '8. ARSENAL SUPPORT CONSOLE',
      descripcion: 'Planificación de producción (PCP) en talleres del Arsenal y asignación de órdenes de trabajo.',
      ruta: '/supervision-sistema', // Mapeado temporalmente
      rol: 'PLANIFICACIÓN Y CONTROL (PCP)',
      username: 'jefe_pcp',
      password: 'pin_pcp',
      habilitada: true
    },
    {
      id: 'ingenieria',
      nombre: '9. ENGINEERING CONSOLE',
      descripcion: 'Análisis de fallas complejas, límites de ciclos LLP y emisión de directivas de reparación.',
      ruta: '/supervision-sistema', // Mapeado temporalmente
      rol: 'INGENIERÍA AERONÁUTICA / DIRECCIÓN TÉCNICA',
      username: 'ingeniero_aero',
      password: 'pin_ingenieria',
      habilitada: true
    },
    {
      id: 'compras',
      nombre: '10. PROCUREMENT CONSOLE',
      descripcion: 'Gestión de solicitudes de abastecimiento y órdenes de compra con proveedores externos.',
      ruta: '/supervision-sistema', // Mapeado temporalmente
      rol: 'ENCARGADO DE COMPRAS / ADQUISICIONES',
      username: 'comprador',
      password: 'pin_compras',
      habilitada: true
    },
    {
      id: 'comando',
      nombre: '11. COMMAND CONSOLE',
      descripcion: 'Visión militar global de disponibilidad, overrides por fuerza mayor y auditorías de seguridad.',
      ruta: '/supervision-sistema', // Mapeado temporalmente
      rol: 'DIRECTOR DE MANTENIMIENTO AERONAVAL / COMANDANTE',
      username: 'comandante',
      password: 'pin_comando',
      habilitada: true
    }
  ];

  const handleSimulatedConnect = async (cons: typeof consolas[0]) => {
    setErrorMsg('');
    setLoading(cons.id);
    try {
      const res = await login(cons.username, cons.password);
      localStorage.setItem('token', res.access_token);
      localStorage.setItem('role', res.role);
      localStorage.setItem('username', cons.username);
      
      router.push(cons.ruta);
    } catch (err: any) {
      setErrorMsg(`Error al simular acceso de usuario: ${err.message}`);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', padding: '20px' }}>
      <header style={{
        background: 'var(--bg-sidebar)',
        border: '2px solid var(--border-color)',
        padding: '16px 24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '20px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: 'rgba(57, 255, 20, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: '0.9rem',
            color: 'var(--mil-green)',
            border: '1px solid var(--mil-green)'
          }}>
            ARA
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 700, letterSpacing: '0.1em' }}>SIMA :: LAUNCHPAD OPERACIONAL</h1>
            <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Sistema Integrado de Mantenimiento Aeronaval • Portal de Acceso Unificado
            </p>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span className="badge badge-fds blink">INTEGRADO CON JWT Y API REAL</span>
        </div>
      </header>

      <main style={{ flexGrow: 1 }}>
        <div className="panel" style={{ marginBottom: '20px', textAlign: 'center', borderStyle: 'double', borderWidth: '3px' }}>
          <h2 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '6px' }}>
            DESPACHO DE PUESTOS OPERATIVOS DEL ECOSISTEMA
          </h2>
          <p style={{ color: 'var(--text-muted)', maxWidth: '800px', margin: '0 auto', fontSize: '0.8rem' }}>
            El Launchpad realiza autenticaciones JWT reales contra el backend central. Al conectar a una terminal, se inyectan los claims de roles específicos del puesto militar y se aísla visualmente la navegación del operador.
          </p>
          {errorMsg && (
            <p style={{ color: 'var(--mil-alert)', fontSize: '0.8rem', marginTop: '10px', fontWeight: 'bold' }}>
              {errorMsg}
            </p>
          )}
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))',
          gap: '16px'
        }}>
          {consolas.map((cons) => (
            <div
              key={cons.id}
              style={{
                background: 'var(--bg-card)',
                border: '1px solid var(--mil-green)',
                padding: '16px',
                display: 'flex',
                flexDirection: 'column',
                position: 'relative'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 'bold', color: 'var(--text-muted)' }}>
                  {cons.rol}
                </span>
                <span className="badge badge-apto" style={{ fontSize: '0.65rem' }}>AUTÓNOMA</span>
              </div>

              <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#ffffff', marginBottom: '6px' }}>
                {cons.nombre}
              </h3>
              
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.4', flexGrow: 1, marginBottom: '14px' }}>
                {cons.descripcion}
              </p>

              <button
                onClick={() => handleSimulatedConnect(cons)}
                disabled={loading !== null}
                className="btn btn-primary"
                style={{ width: '100%', fontSize: '0.75rem', textAlign: 'center' }}
              >
                {loading === cons.id ? 'AUTENTICANDO...' : 'CONECTAR ESTACIÓN'}
              </button>
            </div>
          ))}
        </div>
      </main>

      <footer style={{
        marginTop: '20px',
        border: '1px solid var(--border-color)',
        padding: '10px',
        textAlign: 'center',
        fontSize: '0.75rem',
        color: 'var(--text-dim)',
        background: 'var(--bg-sidebar)'
      }}>
        REPÚBLICA ARGENTINA • COMANDO DE LA AVIACIÓN NAVAL • ACCESO DE FIRMAS MILITARES HABILITADAS
      </footer>
    </div>
  );
}
