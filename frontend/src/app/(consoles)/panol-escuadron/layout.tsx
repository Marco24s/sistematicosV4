'use client';

import React from 'react';
import Link from 'next/link';

export default function PanolEscuadronLayout({ children }: { children: React.ReactNode }) {
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
            color: '#fff'
          }}>PE</div>
          <span>PAÑOL ESCUADRÓN</span>
        </div>
        <nav className="console-sidebar-menu">
          <Link href="/panol-escuadron" className="console-sidebar-link active">
            Inventario Local
          </Link>
        </nav>
        <div className="console-sidebar-footer">
          <Link href="/" className="btn btn-secondary" style={{ width: '100%' }}>
            ◀ Volver al Launchpad
          </Link>
        </div>
      </aside>

      <div className="console-main">
        <header className="console-header">
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Puesto: Encargado de Pañol de Escuadrón</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Logística de Escuadrilla • Base Aeronaval</p>
          </div>
          <div>
            <span className="badge badge-info">SECTOR LOGÍSTICA</span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
