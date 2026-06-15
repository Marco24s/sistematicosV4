'use client';

import React, { useEffect, useState } from 'react';
import {
  getAircraftList,
  getAircraftComponents,
  getPendingMaintenance,
  getServiceableComponents,
  reportFailure,
  removeComponent,
  installComponent,
  login
} from '../../../lib/api';

export default function SquadronMaintenanceConsole() {
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState('');

  // App data
  const [aeronaves, setAeronaves] = useState<any[]>([]);
  const [fallas, setFallas] = useState<any[]>([]);
  const [selectedAero, setSelectedAero] = useState<any | null>(null);
  const [mountedComponents, setMountedComponents] = useState<any[]>([]);
  const [serviceableComponents, setServiceableComponents] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  // Forms state
  const [reportAeroId, setReportAeroId] = useState('');
  const [reportCompId, setReportCompId] = useState('');
  const [reportCompsList, setReportCompsList] = useState<any[]>([]);
  const [failureCode, setFailureCode] = useState('SYS-LEAK');
  const [severity, setSeverity] = useState('CRITICAL');
  const [description, setDescription] = useState('');
  const [reporterName, setReporterName] = useState('Jefe Mantenimiento');

  // Installation state
  const [installAeroId, setInstallAeroId] = useState('');
  const [installCompId, setInstallCompId] = useState('');
  const [positionCode, setPositionCode] = useState('HYDRAULIC_SLOT');
  const [installedBy, setInstalledBy] = useState('Mecanico Principal');

  // Status messages
  const [opMessage, setOpMessage] = useState('');
  const [opError, setOpError] = useState('');

  useEffect(() => {
    const savedToken = localStorage.getItem('token');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  useEffect(() => {
    if (token) {
      cargarDatos();
    }
  }, [token]);

  const cargarDatos = async () => {
    try {
      setLoading(true);
      const [listAero, listFallas, listServiceable] = await Promise.all([
        getAircraftList(),
        getPendingMaintenance(),
        getServiceableComponents()
      ]);
      setAeronaves(listAero);
      setFallas(listFallas);
      setServiceableComponents(listServiceable);

      if (selectedAero) {
        const updated = listAero.find((a: any) => a.id === selectedAero.id);
        if (updated) {
          setSelectedAero(updated);
          const comps = await getAircraftComponents(updated.id);
          setMountedComponents(comps);
        }
      }
    } catch (e: any) {
      console.error(e);
      if (e.message?.includes('401') || e.message?.includes('403')) {
        handleLogout();
      }
    } finally {
      setLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError('');
    try {
      const data = await login(username, password);
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
    } catch (err: any) {
      setLoginError(err.message || 'Error de inicio de sesión');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setAeronaves([]);
    setFallas([]);
    setSelectedAero(null);
    setMountedComponents([]);
    setServiceableComponents([]);
  };

  const handleSelectAero = async (aero: any) => {
    setSelectedAero(aero);
    try {
      const comps = await getAircraftComponents(aero.id);
      setMountedComponents(comps);
    } catch (e) {
      setMountedComponents([]);
    }
  };

  const handleReportAeroChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const id = e.target.value;
    setReportAeroId(id);
    setReportCompId('');
    if (id) {
      try {
        const comps = await getAircraftComponents(id);
        setReportCompsList(comps);
      } catch (err) {
        setReportCompsList([]);
      }
    } else {
      setReportCompsList([]);
    }
  };

  const handleReportarFalla = async (e: React.FormEvent) => {
    e.preventDefault();
    setOpMessage('');
    setOpError('');
    if (!reportAeroId || !reportCompId || !description) {
      return setOpError('Complete todos los campos necesarios para el reporte.');
    }

    try {
      setLoading(true);
      await reportFailure(
        reportAeroId,
        reportCompId,
        failureCode,
        severity,
        description,
        reporterName
      );
      setOpMessage('Falla registrada exitosamente. Grounding automático aplicado a la aeronave.');
      setReportAeroId('');
      setReportCompId('');
      setDescription('');
      cargarDatos();
    } catch (err: any) {
      setOpError(err.message || 'Error al reportar la falla.');
    } finally {
      setLoading(false);
    }
  };

  const handleRemoverComponente = async (componentId: string) => {
    if (!selectedAero) return;
    setOpMessage('');
    setOpError('');

    try {
      setLoading(true);
      const res = await removeComponent(selectedAero.id, componentId, 'Mecanico Hangar');
      setOpMessage(`Componente removido con éxito. Estado del componente: ${res.component_condition}. Custodio actualizado.`);
      cargarDatos();
    } catch (err: any) {
      setOpError(err.message || 'Error al remover componente.');
    } finally {
      setLoading(false);
    }
  };

  const handleInstalarComponente = async (e: React.FormEvent) => {
    e.preventDefault();
    setOpMessage('');
    setOpError('');
    if (!installAeroId || !installCompId) {
      return setOpError('Seleccione la aeronave y el componente para proceder.');
    }

    try {
      setLoading(true);
      const res = await installComponent(installAeroId, installCompId, positionCode, installedBy);
      setOpMessage(`Componente instalado con éxito. Estado operacional de aeronave: ${res.aircraft_status}. Apta para vuelo: ${res.is_airworthy}`);
      setInstallCompId('');
      cargarDatos();
    } catch (err: any) {
      setOpError(err.message || 'Error en la instalación o rechazo de LLP/Certificación.');
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '80vh' }}>
        <form onSubmit={handleLogin} className="panel" style={{ width: '100%', maxWidth: '400px', padding: '24px' }}>
          <h2 style={{ textAlign: 'center', marginBottom: '20px', color: '#fff', fontSize: '1.2rem', fontWeight: 'bold' }}>
            ACCESO DE MANTENIMIENTO DE ESCUADRÓN
          </h2>
          <div style={{ marginBottom: '16px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              CÓDIGO DE USUARIO
            </label>
            <input
              type="text"
              className="mil-input"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Ej. inspector_calidad, jefe_taller"
              required
              style={{ width: '100%', padding: '10px', background: '#07090b', border: '1px solid var(--border-color)', color: '#fff' }}
            />
          </div>
          <div style={{ marginBottom: '20px' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px' }}>
              CLAVE DE AUTORIZACIÓN
            </label>
            <input
              type="password"
              className="mil-input"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              style={{ width: '100%', padding: '10px', background: '#07090b', border: '1px solid var(--border-color)', color: '#fff' }}
            />
          </div>
          {loginError && (
            <p style={{ color: 'var(--mil-alert)', fontSize: '0.8rem', marginBottom: '14px', textAlign: 'center' }}>
              {loginError}
            </p>
          )}
          <button type="submit" className="btn btn-primary" style={{ width: '100%', padding: '10px' }}>
            ESTABLECER CONEXIÓN JWT
          </button>
        </form>
      </div>
    );
  }

  return (
    <div>
      <div className="panel" style={{ padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0a0d0f', border: '1px solid var(--border-color)', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>CONSOLA OPERATIVA DE MANTENIMIENTO</h2>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>SECCIÓN DE HANGAR Y DIQUE</span>
        </div>
        <div>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ fontSize: '0.75rem', padding: '6px 12px' }}>
            DESCONECTAR TERMINAL
          </button>
        </div>
      </div>

      {opMessage && (
        <div className="panel" style={{ borderColor: 'var(--mil-green)', color: 'var(--mil-green)', marginBottom: '16px', fontSize: '0.85rem' }}>
          {opMessage}
        </div>
      )}

      {opError && (
        <div className="panel" style={{ borderColor: 'var(--mil-alert)', color: 'var(--mil-alert)', marginBottom: '16px', fontSize: '0.85rem' }}>
          {opError}
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: '20px' }}>
        {/* A. List of assigned aircraft */}
        <div className="panel">
          <h3 className="panel-title">Estado de Aeronaves Asignadas</h3>
          <div className="table-wrapper">
            <table className="mil-table">
              <thead>
                <tr>
                  <th>Nomenclatura</th>
                  <th>Nro Serie</th>
                  <th>Estado</th>
                  <th>Horas</th>
                </tr>
              </thead>
              <tbody>
                {aeronaves.map((aero) => (
                  <tr key={aero.id} style={{ cursor: 'pointer' }} onClick={() => handleSelectAero(aero)}>
                    <td style={{ fontWeight: 'bold', color: '#fff' }}>{aero.nomenclature}</td>
                    <td>{aero.serial_number}</td>
                    <td>
                      <span className={`badge ${aero.current_status === 'RELEASED' ? 'badge-apto' : 'badge-fds'}`}>
                        {aero.current_status}
                      </span>
                    </td>
                    <td>{aero.total_hours} hs</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Selected Aircraft components & Uninstall (C) */}
        <div className="panel">
          <h3 className="panel-title">Árbol de Configuración Física y Desmontaje</h3>
          {selectedAero ? (
            <div>
              <p style={{ fontSize: '0.85rem', marginBottom: '10px' }}>
                Aeronave Seleccionada: <strong>{selectedAero.nomenclature} ({selectedAero.serial_number})</strong>
              </p>
              <div className="table-wrapper">
                <table className="mil-table" style={{ fontSize: '0.75rem' }}>
                  <thead>
                    <tr>
                      <th>Componente</th>
                      <th>Posición</th>
                      <th>P/N</th>
                      <th>S/N</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mountedComponents.map((comp) => (
                      <tr key={comp.id}>
                        <td>{comp.nomenclature}</td>
                        <td>{comp.position_code}</td>
                        <td>{comp.part_number}</td>
                        <td>{comp.serial_number}</td>
                        <td>
                          <button
                            onClick={() => handleRemoverComponente(comp.id)}
                            className="btn btn-secondary"
                            style={{ fontSize: '0.65rem', padding: '4px 8px', borderColor: 'var(--mil-alert)', color: 'var(--mil-alert)' }}
                          >
                            DESMONTAR
                          </button>
                        </td>
                      </tr>
                    ))}
                    {mountedComponents.length === 0 && (
                      <tr>
                        <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-dim)' }}>
                          No hay componentes instalados.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-dim)', fontSize: '0.8rem' }}>
              Seleccione una aeronave a la izquierda para ver su configuración y desmontar componentes.
            </div>
          )}
        </div>
      </div>

      <div className="grid-2">
        {/* D. Install serviceable component */}
        <div className="panel">
          <h3 className="panel-title">Instalación de Componentes Serviceable</h3>
          <form onSubmit={handleInstalarComponente}>
            <div className="form-group">
              <label className="form-label">Aeronave Destino</label>
              <select
                className="form-control"
                value={installAeroId}
                onChange={(e) => setInstallAeroId(e.target.value)}
                required
              >
                <option value="">Seleccione aeronave...</option>
                {aeronaves.map((aero) => (
                  <option key={aero.id} value={aero.id}>
                    {aero.nomenclature} ({aero.serial_number})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Componente Disponible en Pañol (Serviceable)</label>
              <select
                className="form-control"
                value={installCompId}
                onChange={(e) => setInstallCompId(e.target.value)}
                required
              >
                <option value="">Seleccione componente...</option>
                {serviceableComponents.map((comp) => (
                  <option key={comp.id} value={comp.id}>
                    {comp.nomenclature} (S/N: {comp.serial_number}) - PN: {comp.part_number}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Posición de Montaje</label>
              <select
                className="form-control"
                value={positionCode}
                onChange={(e) => setPositionCode(e.target.value)}
                required
              >
                <option value="HYDRAULIC_SLOT">HYDRAULIC_SLOT</option>
                <option value="ENGINE_SLOT_LEFT">ENGINE_SLOT_LEFT</option>
                <option value="ENGINE_SLOT_RIGHT">ENGINE_SLOT_RIGHT</option>
                <option value="ROTOR_SLOT">ROTOR_SLOT</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Mecánico Instalador Habilitado</label>
              <input
                type="text"
                className="form-control"
                value={installedBy}
                onChange={(e) => setInstalledBy(e.target.value)}
                required
              />
            </div>

            <button type="submit" disabled={loading} className="btn btn-primary" style={{ width: '100%' }}>
              {loading ? 'VALIDANDO E INSTALANDO...' : 'EJECUTAR MONTAJE E INSTALACIÓN'}
            </button>
          </form>
        </div>

        {/* B & E. Report failure & list open discrepancies */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* B. Report Failure */}
          <div className="panel">
            <h3 className="panel-title" style={{ color: 'var(--mil-alert)' }}>Registrar Falla Directa (Grounding Automático)</h3>
            <form onSubmit={handleReportarFalla}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div className="form-group">
                  <label className="form-label">Aeronave</label>
                  <select
                    className="form-control"
                    value={reportAeroId}
                    onChange={handleReportAeroChange}
                    required
                  >
                    <option value="">Seleccione...</option>
                    {aeronaves.map((aero) => (
                      <option key={aero.id} value={aero.id}>
                        {aero.nomenclature}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Componente afectado</label>
                  <select
                    className="form-control"
                    value={reportCompId}
                    onChange={(e) => setReportCompId(e.target.value)}
                    required
                  >
                    <option value="">Seleccione...</option>
                    {reportCompsList.map((comp) => (
                      <option key={comp.id} value={comp.id}>
                        {comp.nomenclature}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div className="form-group">
                  <label className="form-label">Código Falla</label>
                  <input
                    type="text"
                    className="form-control"
                    value={failureCode}
                    onChange={(e) => setFailureCode(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Criticidad</label>
                  <select
                    className="form-control"
                    value={severity}
                    onChange={(e) => setSeverity(e.target.value)}
                  >
                    <option value="CRITICAL">CRÍTICA (GROUNDING)</option>
                    <option value="MINOR">MENOR (DIFERIBLE)</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Descripción</label>
                <input
                  type="text"
                  className="form-control"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Ej. Fuga de líquido o fisura"
                  required
                />
              </div>

              <button type="submit" disabled={loading} className="btn btn-danger" style={{ width: '100%' }}>
                CONFIRMAR REPORTE Y APLICAR GROUNDING
              </button>
            </form>
          </div>

          {/* E. List open discrepancies */}
          <div className="panel">
            <h3 className="panel-title">Lista de Discrepancias Abiertas</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '250px', overflowY: 'auto' }}>
              {fallas.map((falla) => (
                <div key={falla.id} style={{
                  background: 'rgba(0,0,0,0.15)',
                  borderLeft: `3px solid ${falla.severity === 'CRITICAL' ? 'var(--mil-alert)' : 'var(--border-color)'}`,
                  padding: '8px',
                  fontSize: '0.75rem'
                }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontWeight: 'bold', color: '#fff' }}>
                    <span>{falla.aircraft_nomenclature}</span>
                    <span style={{ color: falla.severity === 'CRITICAL' ? 'var(--mil-alert)' : 'var(--text-muted)' }}>{falla.severity}</span>
                  </div>
                  <p style={{ margin: '4px 0' }}>{falla.component_nomenclature}: {falla.description}</p>
                  <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-dim)', fontSize: '0.7rem' }}>
                    <span>Por: {falla.reported_by}</span>
                    <span>Fecha: {falla.failure_date}</span>
                  </div>
                </div>
              ))}
              {fallas.length === 0 && (
                <p style={{ textAlign: 'center', padding: '10px', color: 'var(--text-dim)', fontSize: '0.75rem' }}>
                  No hay discrepancias abiertas.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
