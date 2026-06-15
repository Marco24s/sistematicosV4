'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function OperacionesLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  const links = [
    { href: '/operaciones', label: 'Dashboard Operativo' },
  ];

  return (
    <div className="console-layout">
      {/* Sidebar de Operaciones */}
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
          }}>OP</div>
          <span>OPERACIONES</span>
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
            ◀ Volver al Launchpad
          </Link>
        </div>
      </aside>

      {/* Main Area */}
      <div className="console-main">
        <header className="console-header">
          <div>
            <h2 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Puesto: Jefe de Operaciones Aeronavales</h2>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Despacho y Control de Misiones</p>
          </div>
          <div>
            <span className="badge badge-apto blink">OPERATIVO</span>
          </div>
        </header>
        <main className="console-content">
          {children}
        </main>
      </div>
    </div>
  );
}
