'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function CalidadLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <div className="console-layout">
      <aside className="console-sidebar">
        <div className="console-sidebar-brand">
          <div style={{
            width: '24px',
            height: '24px',
            borderRadius: '50%',
            background: 'var(--mil-green)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.7rem',
            fontWeight: 'bold',
            color: '#000',
          }}>
            CC
          </div>
          <span>CONTROL DE CALIDAD</span>
        </div>
        <nav className="console-sidebar-menu">
          <Link href="/control-calidad" className={`console-sidebar-link ${pathname === '/control-calidad' ? 'active' : ''}`}>
            Inspeccion final
          </Link>
        </nav>
        <div className="console-sidebar-footer">
          <Link href="/" className="btn btn-secondary" style={{ width: '100%' }}>
            Volver al Launchpad
          </Link>
        </div>
      </aside>

      <div className="console-main">
        <header className="console-header">
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>
              Puesto: Inspector de Control de Calidad
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Inspeccion dual, firma digital y liberacion a condicion serviceable.
            </p>
          </div>
          <div>
            <span className="badge badge-info" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#f59e0b', borderColor: '#f59e0b' }}>
              INSPECTOR DAC
            </span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
