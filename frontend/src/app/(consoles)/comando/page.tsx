'use client';
import React from 'react';

export default function ModuleUnderConstruction() {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '70vh', flexDirection: 'column', gap: '16px' }}>
      <div style={{ fontSize: '3rem' }}>🚧</div>
      <h2 style={{ color: 'var(--mil-alert)', fontWeight: 700, letterSpacing: '0.1em' }}>
        MÓDULO EN CONSTRUCCIÓN
      </h2>
      <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        PENDIENTE DE INTEGRACIÓN CON BACKEND REAL.
      </p>
      <p style={{ color: 'var(--text-dim)', fontSize: '0.75rem', maxWidth: '500px', textAlign: 'center' }}>
        En cumplimiento de la Directiva de Estabilización del Sistema, las simulaciones locales han sido neutralizadas. Esta consola se desarrollará según el roadmap operacional estricto.
      </p>
    </div>
  );
}
