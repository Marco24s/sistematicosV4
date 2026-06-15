'use client';

import React from 'react';
import Link from 'next/link';

export default function PanolArsenalLayout({ children }: { children: React.ReactNode }) {
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
          }}>PA</div>
          <span>PAÑOL ARSENAL</span>
        </div>
        <nav className="console-sidebar-menu">
          <Link href="/panol-arsenal" className="console-sidebar-link active">
            Recepción de Piezas
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
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Puesto: Encargado de Pañol Central de Arsenal</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Recepción y Custodia Física • Arsenal Aeronaval</p>
          </div>
          <div>
            <span className="badge badge-info">ARSENAL CENTRAL</span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
