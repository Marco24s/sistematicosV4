'use client';

import React, { useEffect, useState } from 'react';
import { getAircraftList, getAircraftComponents, removeComponent, installComponent, fetchAPI } from '../../../../lib/api';

export default function ComponentesMantenimientoPage() {
  const [aeronaves, setAeronaves] = useState<any[]>([]);
  const [selectedAircraftId, setSelectedAircraftId] = useState('');
  const [componentesMontados, setComponentesMontados] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Lista de componentes disponibles en pañol para instalar (desacoplados/en stock)
  const [componentesLibres, setComponentesLibres] = useState<any[]>([]);
  const [selectedLibreId, setSelectedLibreId] = useState('');
  const [positionCode, setPositionCode] = useState('P-1');
  const [tecnico, setTecnico] = useState('TECH-801');

  const cargarDatos = async () => {
    try {
      setLoading(true);
      const list = await getAircraftList();
      setAeronaves(list);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    cargarDatos();
  }, []);

  const handleAircraftChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setSelectedAircraftId(id);
    setComponentesMontados([]);
    if (id) {
      try {
        const comps = await getAircraftComponents(id);
        setComponentesMontados(comps);
      } catch (err) {
        setComponentesMontados([]);
      }
    }
    cargarComponentesLibres();
  };

  // Buscar componentes que no estén montados para ofrecer en instalación
  const cargarComponentesLibres = async () => {
    try {
      // Como no hay endpoint general de listado de componentes en esta fase, no mockearemos stock temporalmente.
      setComponentesLibres([]);
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemover = async (compId: string) => {
    if (!selectedAircraftId) return;
    try {
      setLoading(true);
      const res = await removeComponent(selectedAircraftId, compId, tecnico);
      console.log("Remoción exitosa:", res);
      alert('Componente removido físicamente en el backend. Estado actualizado a UNSERVICEABLE y disponible en el pañol.');
      
      // Recargar componentes montados
      const comps = await getAircraftComponents(selectedAircraftId);
      setComponentesMontados(comps);
    } catch (err: any) {
      alert(`Error al remover componente: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleInstalar = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAircraftId || !selectedLibreId) return alert('Seleccione componentes');

    try {
      setLoading(true);
      const res = await installComponent(selectedAircraftId, selectedLibreId, positionCode, tecnico);
      console.log("Instalación exitosa:", res);
      alert('Componente instalado satisfactoriamente en el backend.');
      
      // Recargar
      const comps = await getAircraftComponents(selectedAircraftId);
      setComponentesMontados(comps);
      setSelectedLibreId('');
    } catch (err: any) {
      alert(`Error al instalar componente: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid-2">
      {/* Visualización de árbol físico */}
      <div className="panel">
        <h3 className="panel-title">Estructura Física y Componentes Montados</h3>
        <div className="form-group">
          <label className="form-label">Aeronave</label>
          <select
            className="form-control"
            value={selectedAircraftId}
            onChange={handleAircraftChange}
            required
          >
            <option value="">Seleccione matrícula...</option>
            {aeronaves.map((aero) => (
              <option key={aero.id} value={aero.id}>
                {aero.nomenclature} ({aero.serial_number})
              </option>
            ))}
          </select>
        </div>

        {selectedAircraftId ? (
          <div className="table-wrapper" style={{ marginTop: '16px' }}>
            <table className="mil-table">
              <thead>
                <tr>
                  <th>Nomenclatura</th>
                  <th>P/N</th>
                  <th>S/N</th>
                  <th>Acción</th>
                </tr>
              </thead>
              <tbody>
                {componentesMontados.map((comp) => (
                  <tr key={comp.id}>
                    <td style={{ fontWeight: 'bold' }}>{comp.nomenclature}</td>
                    <td>{comp.part_number}</td>
                    <td>{comp.serial_number}</td>
                    <td>
                      <button
                        onClick={() => handleRemover(comp.id)}
                        disabled={loading}
                        className="btn btn-danger"
                        style={{ padding: '4px 8px', fontSize: '0.75rem' }}
                      >
                        Remover
                      </button>
                    </td>
                  </tr>
                ))}
                {componentesMontados.length === 0 && (
                  <tr>
                    <td colSpan={4} style={{ textAlign: 'center', color: 'var(--text-dim)', padding: '20px' }}>
                      No hay componentes montados registrados en este momento.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)', border: '1px dashed var(--border-color)', fontSize: '0.8rem' }}>
            SELECCIONE UNA AERONAVE PARA VER LA CONFIGURACIÓN Y DESMONTAR COMPONENTES.
          </div>
        )}
      </div>

      {/* Formulario de montaje de componentes */}
      <div className="panel">
        <h3 className="panel-title">Montaje de Nuevos Componentes</h3>
        <form onSubmit={handleInstalar}>
          <div className="form-group">
            <label className="form-label">Componente del Pañol</label>
            <select
              className="form-control"
              value={selectedLibreId}
              onChange={(e) => setSelectedLibreId(e.target.value)}
              required
            >
              <option value="">Seleccione motor...</option>
              {componentesLibres.map((comp) => (
                <option key={comp.id} value={comp.id}>
                  {comp.nomenclature} (S/N: {comp.serial_number}) - P/N: {comp.part_number}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Código de Posición Física</label>
            <input
              type="text"
              className="form-control"
              value={positionCode}
              onChange={(e) => setPositionCode(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Técnico Habilitador (Firma)</label>
            <input
              type="text"
              className="form-control"
              value={tecnico}
              onChange={(e) => setTecnico(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading || !selectedAircraftId || !selectedLibreId}
            className="btn btn-primary"
            style={{ width: '100%', marginTop: '10px' }}
          >
            {loading ? 'REGISTRANDO MONTAJE...' : 'MONTAR COMPONENTE EN AERONAVE'}
          </button>
        </form>
      </div>
    </div>
  );
}
