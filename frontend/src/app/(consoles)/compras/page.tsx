'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getGlobalEngineAssets } from '../../../lib/api';

export default function GlobalStockEngine() {
  const router = useRouter();
  const [assets, setAssets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');

  useEffect(() => {
    const fetchAssets = async () => {
      try {
        const data = await getGlobalEngineAssets();
        setAssets(data);
      } catch (err: any) {
        setErrorMsg('Error al obtener la base de activos: ' + err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchAssets();
  }, []);

  const filteredAssets = assets.filter(a => {
    const matchesSearch = a.nomenclature.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          a.serial_number.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          a.part_number.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesType = filterType === 'ALL' || a.type_category === filterType;
    return matchesSearch && matchesType;
  });

  const getConditionColor = (cond: string) => {
    switch (cond) {
      case 'SERVICEABLE': return 'var(--mil-green)';
      case 'UNSERVICEABLE': return 'var(--mil-alert)';
      case 'REPAIRABLE': return 'var(--mil-warning)';
      default: return 'var(--text-muted)';
    }
  };

  const getAirworthinessColor = (status: string) => {
    switch (status) {
      case 'AIRWORTHY': return 'var(--mil-green)';
      case 'NON_AIRWORTHY': return 'var(--mil-alert)';
      case 'RESTRICTED': return 'var(--mil-warning)';
      case 'AWAITING_CERTIFICATION': return '#00d2ff';
      default: return 'var(--text-muted)';
    }
  };

  return (
    <div style={{ padding: '20px', minHeight: '100vh', background: 'var(--bg-main)' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h1 style={{ color: 'var(--text-primary)', fontSize: '2rem', letterSpacing: '2px', margin: '0 0 8px 0' }}>
            PROCUREMENT & STOCK GLOBAL ENGINE
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', margin: 0 }}>
            VISOR CENTRAL DE ACTIVOS, CONDICIÓN LOGÍSTICA Y AERONAVEGABILIDAD
          </p>
        </div>
        <button onClick={() => router.push('/')} className="btn" style={{ padding: '8px 16px' }}>
          &larr; VOLVER AL LAUNCHPAD
        </button>
      </header>

      <div className="panel" style={{ padding: '20px', marginBottom: '20px', display: 'flex', gap: '16px', alignItems: 'center' }}>
        <input 
          type="text" 
          placeholder="BUSCAR POR N/P, N/S O NOMENCLATURA..." 
          className="mil-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          style={{ flex: 1, padding: '12px', background: '#0a0d14', color: '#fff', border: '1px solid var(--border-color)' }}
        />
        <select 
          className="mil-input"
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          style={{ padding: '12px', background: '#0a0d14', color: '#fff', border: '1px solid var(--border-color)', minWidth: '200px' }}
        >
          <option value="ALL">TODAS LAS CATEGORÍAS</option>
          <option value="AIRCRAFT">AERONAVES</option>
          <option value="ENGINE">MOTORES</option>
          <option value="ROTOR">ROTORES</option>
          <option value="COMPONENT">COMPONENTES MENORES</option>
        </select>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', color: 'var(--mil-blue)', padding: '40px', fontFamily: 'monospace' }}>
          SINCRONIZANDO CON BASE DE DATOS LOGÍSTICA...
        </div>
      ) : errorMsg ? (
        <div style={{ color: 'var(--mil-alert)', border: '1px solid var(--mil-alert)', padding: '20px', background: 'rgba(255, 68, 68, 0.1)' }}>
          {errorMsg}
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table className="mil-table" style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: 'var(--bg-sidebar)', color: 'var(--mil-blue)', textAlign: 'left', borderBottom: '2px solid var(--border-color)' }}>
                <th style={{ padding: '12px' }}>N/P</th>
                <th style={{ padding: '12px' }}>N/S</th>
                <th style={{ padding: '12px' }}>NOMENCLATURA</th>
                <th style={{ padding: '12px' }}>CATEGORÍA</th>
                <th style={{ padding: '12px' }}>UBICACIÓN FÍSICA</th>
                <th style={{ padding: '12px' }}>TENEDOR (CUSTODIO)</th>
                <th style={{ padding: '12px' }}>ORG DUEÑA</th>
                <th style={{ padding: '12px' }}>ESTADO LOGÍSTICO</th>
                <th style={{ padding: '12px' }}>CONDICIÓN</th>
                <th style={{ padding: '12px' }}>AERONAVEGABILIDAD</th>
              </tr>
            </thead>
            <tbody>
              {filteredAssets.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                    NO SE ENCONTRARON ACTIVOS
                  </td>
                </tr>
              ) : (
                filteredAssets.map((asset) => (
                  <tr key={asset.id} style={{ borderBottom: '1px solid #1a2b3c' }}>
                    <td style={{ padding: '12px', fontFamily: 'monospace' }}>{asset.part_number}</td>
                    <td style={{ padding: '12px', fontFamily: 'monospace', color: '#fff' }}>{asset.serial_number}</td>
                    <td style={{ padding: '12px' }}>{asset.nomenclature}</td>
                    <td style={{ padding: '12px' }}>{asset.type_category}</td>
                    <td style={{ padding: '12px' }}>{asset.location}</td>
                    <td style={{ padding: '12px' }}>{asset.custodian}</td>
                    <td style={{ padding: '12px', color: 'var(--mil-blue)' }}>{asset.owner}</td>
                    <td style={{ padding: '12px' }}>{asset.status}</td>
                    <td style={{ padding: '12px', color: getConditionColor(asset.condition), fontWeight: 'bold' }}>
                      {asset.condition}
                    </td>
                    <td style={{ padding: '12px', color: getAirworthinessColor(asset.airworthiness_status), fontWeight: 'bold' }}>
                      {asset.airworthiness_status}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
