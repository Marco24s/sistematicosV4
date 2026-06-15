'use client';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { getMe } from '../lib/api';

const roleAccessMap: Record<string, string[]> = {
  "COMMAND_OFFICER": ['comando', 'estadisticas-escuadron'],
  "MAINTENANCE_CHIEF": ['operaciones', 'mantenimiento-escuadron', 'panol-escuadron', 'panol-arsenal', 'taller-arsenal', 'estadisticas-escuadron', 'soporte-arsenal', 'ingenieria', 'compras'],
  "TECHNICIAN": ['mantenimiento-escuadron', 'panol-escuadron', 'taller-arsenal'],
  "INSPECTOR": ['control-calidad'],
  "SYSTEM_ADMIN": ['comando', 'gestion-activos']
};

const consolas = [
  {
    id: 'gestion-activos',
    nombre: 'SYSTEM CONFIGURATION PHASE',
    descripcion: 'Asset Commissioning Workflow. Alta técnica de aeronaves y configuración basal. Solo ADMIN.',
    ruta: '/gestion-activos'
  },
  {
    id: 'comando',
    nombre: 'COMMAND CENTER (MONITOREO GLOBAL)',
    descripcion: 'Monitoreo consolidado de flota, componentes, stock global, órdenes de trabajo y timeline de eventos en tiempo real.',
    ruta: '/comando'
  },
  {
    id: 'operaciones',
    nombre: '1. OPERATIONS CONSOLE',
    descripcion: 'Apertura y cierre de partes de vuelo, control de misiones y disponibilidad de dotación.',
    ruta: '/operaciones'
  },
  {
    id: 'mantenimiento-escuadron',
    nombre: '2. SQUADRON MAINTENANCE CONSOLE',
    descripcion: 'Reporte de fallas (grounding), tareas preventivas, remoción e instalación de componentes en hangar (O-Level).',
    ruta: '/mantenimiento-escuadron'
  },
  {
    id: 'panol-escuadron',
    nombre: '3. SQUADRON STORAGE CONSOLE',
    descripcion: 'Gestión de stock local del escuadrón, componentes serviceable e inoperativos listos para envío al Arsenal.',
    ruta: '/panol-escuadron'
  },
  {
    id: 'panol-arsenal',
    nombre: '4. ARSENAL STORAGE CONSOLE',
    descripcion: 'Recepción física y documental de componentes inoperativos enviados por los escuadrones y custodia en Arsenal.',
    ruta: '/panol-arsenal'
  },
  {
    id: 'taller-arsenal',
    nombre: '5. ARSENAL TECHNICAL CONSOLE',
    descripcion: 'Ejecución del procedimiento técnico en talleres del Arsenal (Motores, Hidráulica, Aviónica).',
    ruta: '/taller-arsenal'
  },
  {
    id: 'control-calidad',
    nombre: '6. QUALITY CONTROL CONSOLE',
    descripcion: 'Inspección dual de seguridad de tareas críticas y firma digital de certificados de liberación.',
    ruta: '/control-calidad'
  },
  {
    id: 'estadisticas-escuadron',
    nombre: '7. SQUADRON STATISTICS CONSOLE',
    descripcion: 'Forecast de mantenimiento de célula, análisis de confiabilidad (MTBF, MTTR) e historial.',
    ruta: '/estadisticas-escuadron'
  },
  {
    id: 'soporte-arsenal',
    nombre: '8. ARSENAL SUPPORT CONSOLE',
    descripcion: 'Planificación de producción (PCP) en talleres del Arsenal y asignación de órdenes de trabajo.',
    ruta: '/soporte-arsenal'
  },
  {
    id: 'ingenieria',
    nombre: '9. ENGINEERING CONSOLE',
    descripcion: 'Análisis de fallas complejas, límites de ciclos LLP y emisión de directivas de reparación.',
    ruta: '/ingenieria'
  },
  {
    id: 'compras',
    nombre: '10. PROCUREMENT CONSOLE',
    descripcion: 'Gestión de solicitudes de abastecimiento y órdenes de compra con proveedores externos.',
    ruta: '/compras'
  }
];

export default function Launchpad() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    getMe()
      .then(data => {
        setProfile(data);
      })
      .catch(err => {
        console.error("Auth error:", err);
        localStorage.removeItem('token');
        router.push('/login');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [router]);

  if (loading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <p style={{ color: 'var(--mil-blue)', fontFamily: 'monospace', fontSize: '1.2rem', letterSpacing: '2px' }}>
          VERIFYING CLEARANCE...
        </p>
      </div>
    );
  }

  if (!profile) return null;

  const allowedConsolas = consolas.filter(c => {
    const roleAccess = roleAccessMap[profile.role_name] || [];
    return roleAccess.includes(c.id);
  });

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    router.push('/login');
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', padding: '20px' }}>
      <header style={{
        background: 'var(--bg-sidebar)',
        border: '2px solid var(--border-color)',
        padding: '16px 24px',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        marginBottom: '20px',
        position: 'relative'
      }}>
        {/* Decorative corner */}
        <div style={{ position: 'absolute', top: '-2px', left: '-2px', width: '20px', height: '20px', borderTop: '2px solid var(--mil-blue)', borderLeft: '2px solid var(--mil-blue)' }}></div>
        
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h1 style={{ color: 'var(--text-primary)', fontSize: '1.8rem', fontWeight: 'bold', letterSpacing: '2px', margin: 0 }}>
              SISTEMA INTEGRAL DE MANTENIMIENTO AERONAVAL
            </h1>
            <p style={{ color: 'var(--mil-blue)', fontSize: '0.9rem', letterSpacing: '1px', margin: '4px 0 0 0' }}>
              MILITARY LAUNCHPAD - V4.0
            </p>
          </div>
          
          <button onClick={handleLogout} className="btn" style={{ background: 'transparent', border: '1px solid var(--mil-alert)', color: 'var(--mil-alert)' }}>
            LOGOUT / TERMINATE
          </button>
        </div>

        {/* HUD Identity Panel */}
        <div style={{
          display: 'flex',
          background: '#04070a',
          border: '1px solid var(--border-color)',
          padding: '12px 16px',
          gap: '24px',
          fontFamily: 'monospace',
          fontSize: '0.9rem',
          color: 'var(--text-muted)'
        }}>
          <div><span style={{ color: 'var(--mil-blue)' }}>OPERATIVE ID:</span> {profile.username.toUpperCase()}</div>
          <div><span style={{ color: 'var(--mil-blue)' }}>ORG:</span> {profile.organization_name.toUpperCase()}</div>
          <div><span style={{ color: 'var(--mil-blue)' }}>DEPT:</span> {profile.department_name.toUpperCase()}</div>
          <div><span style={{ color: 'var(--mil-blue)' }}>CLEARANCE ROLE:</span> {profile.role_name.replace('_', ' ')}</div>
        </div>
      </header>

      <main style={{ flex: 1 }}>
        {allowedConsolas.length === 0 ? (
          <div style={{ padding: '40px', textAlign: 'center', border: '1px dashed var(--mil-alert)', color: 'var(--mil-alert)' }}>
            <h2>ACCESO DENEGADO</h2>
            <p>Su perfil no cuenta con permisos para acceder a ninguna consola operativa.</p>
          </div>
        ) : (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
            gap: '20px'
          }}>
            {allowedConsolas.map((cons) => (
              <div 
                key={cons.id}
                onClick={() => router.push(cons.ruta)}
                style={{
                  background: 'var(--bg-panel)',
                  border: '1px solid var(--border-color)',
                  padding: '24px',
                  cursor: 'pointer',
                  position: 'relative',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '12px',
                  transition: 'all 0.2s ease',
                }}
                className="hover-panel"
              >
                {/* Visual accent top */}
                <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'var(--mil-blue)', opacity: 0.5 }}></div>
                
                <h2 style={{ fontSize: '1.1rem', color: '#fff', margin: 0 }}>
                  {cons.nombre}
                </h2>
                
                <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.5', margin: 0, flex: 1 }}>
                  {cons.descripcion}
                </p>

                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '12px', marginTop: 'auto' }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--mil-blue)', fontFamily: 'monospace' }}>
                    STATUS: ONLINE
                  </span>
                  <span style={{ fontSize: '0.75rem', color: '#fff', fontFamily: 'monospace', padding: '4px 8px', background: 'rgba(255,255,255,0.1)', borderRadius: '2px' }}>
                    ENTER &rarr;
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      <footer style={{ marginTop: '40px', padding: '20px', borderTop: '1px solid var(--border-color)', display: 'flex', justifyContent: 'space-between', color: 'var(--text-muted)', fontSize: '0.8rem', fontFamily: 'monospace' }}>
        <span>CONEXIÓN CIFRADA / CLASIFICACIÓN: RESTRINGIDO</span>
        <span>ID DE CONEXIÓN: {profile.id.split('-')[0].toUpperCase()}</span>
      </footer>

      <style jsx global>{`
        .hover-panel:hover {
          background: rgba(0, 195, 255, 0.05) !important;
          border-color: var(--mil-blue) !important;
          transform: translateY(-2px);
          box-shadow: 0 4px 20px rgba(0, 195, 255, 0.1);
        }
        .hover-panel:hover > div:first-child {
          opacity: 1 !important;
        }
      `}</style>
    </div>
  );
}
