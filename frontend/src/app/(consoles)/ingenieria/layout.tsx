'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function EngineeringLayout({ children }: { children: React.ReactNode }) {
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
            IN
          </div>
          <span>INGENIERIA</span>
        </div>
        <nav className="console-sidebar-menu">
          <Link href="/ingenieria" className={`console-sidebar-link ${pathname === '/ingenieria' ? 'active' : ''}`}>
            Dictamen tecnico
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
              Puesto: Ingenieria Aeronautica / Direccion Tecnica
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Analisis de falla, instrucciones tecnicas y decisiones de reparabilidad.
            </p>
          </div>
          <div>
            <span className="badge badge-info">DIRECCION TECNICA</span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
