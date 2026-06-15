'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function CommandLayout({ children }: { children: React.ReactNode }) {
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
            CM
          </div>
          <span>COMANDO</span>
        </div>
        <nav className="console-sidebar-menu">
          <Link href="/comando" className={`console-sidebar-link ${pathname === '/comando' ? 'active' : ''}`}>
            Director Mantenimiento
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
              Puesto: Director de Mantenimiento Aeronaval
            </h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Readiness, AOG, cuellos de botella, confiabilidad, auditoria y autoridad operacional.
            </p>
          </div>
          <div>
            <span className="badge badge-info">COMANDO MRO</span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
