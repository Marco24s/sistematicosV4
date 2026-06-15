'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function SquadronStatisticsLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const links = [
    { href: '/estadisticas-escuadron', label: 'Control estadistico' },
  ];

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
            ST
          </div>
          <span>ESTADISTICA</span>
        </div>
        <nav className="console-sidebar-menu">
          {links.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`console-sidebar-link ${isActive ? 'active' : ''}`}
              >
                {link.label}
              </Link>
            );
          })}
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
              Puesto: Estadistica y Confiabilidad de Escuadrilla
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              MTBF, MTTR, forecast de vencimientos y trazabilidad tecnica.
            </p>
          </div>
          <div>
            <span className="badge badge-apto blink">EN LINEA</span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
