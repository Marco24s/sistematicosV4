import React, { useState, useEffect } from 'react';
import { fetchAPI } from '../../../lib/api';

export default function AssetCommissioningConsole() {
  const [formData, setFormData] = useState({
    serial_number: '',
    asset_type_id: '',
    organization_id: '',
    classification: 'REPAIRABLE',
    part_number: '',
    nomenclature: ''
  });
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  
  const [assetTypes, setAssetTypes] = useState<any[]>([]);
  const [organizations, setOrganizations] = useState<any[]>([]);

  // New Asset Type State
  const [showNewTypeForm, setShowNewTypeForm] = useState(false);
  const [newTypeData, setNewTypeData] = useState({ name: '', category: 'AIRCRAFT' });
  const [creatingType, setCreatingType] = useState(false);

  useEffect(() => {
    fetchAPI('/assets/types').then(setAssetTypes).catch(console.error);
    fetchAPI('/assets/organizations').then(setOrganizations).catch(console.error);
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleNewTypeChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    setNewTypeData({ ...newTypeData, [e.target.name]: e.target.value });
  };

  const handleCreateType = async (e: React.FormEvent) => {
    e.preventDefault();
    setCreatingType(true);
    setErrorMsg('');
    try {
      const res = await fetchAPI('/assets/types', {
        method: 'POST',
        body: JSON.stringify(newTypeData)
      });
      setAssetTypes([...assetTypes, res]);
      setFormData({ ...formData, asset_type_id: res.id });
      setShowNewTypeForm(false);
      setNewTypeData({ name: '', category: 'AIRCRAFT' });
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al crear el nuevo Modelo.');
    } finally {
      setCreatingType(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const payload = {
        ...formData,
        origin_terminal: window.location.hostname || "ADMIN-CONSOLE"
      };

      const res = await fetchAPI('/assets/register', {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      setSuccessMsg(`ACTIVO COMISIONADO CORRECTAMENTE: ${res.serial_number} [ID: ${res.id}]. Estado: ${res.status}. Registro de Auditoría generado.`);
      setFormData({
        serial_number: '',
        asset_type_id: '',
        organization_id: '',
        classification: 'REPAIRABLE',
        part_number: '',
        nomenclature: ''
      });
    } catch (err: any) {
      setErrorMsg(err.message || 'Error al comisionar el activo.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto', color: '#e2e8f0' }}>
      <header style={{ marginBottom: '2rem', borderBottom: '1px solid #1e293b', paddingBottom: '1rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#38bdf8' }}>FASE DE CONFIGURACIÓN DE SISTEMA</h1>
        <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>FLUJO DE ALTA TÉCNICA Y PUESTA EN SERVICIO (MODO ESTRICTO)</p>
      </header>

      {successMsg && (
        <div style={{ background: 'rgba(34, 197, 94, 0.1)', borderLeft: '4px solid #22c55e', padding: '1rem', marginBottom: '2rem' }}>
          <p style={{ color: '#22c55e', margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>{successMsg}</p>
        </div>
      )}

      {errorMsg && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', borderLeft: '4px solid #ef4444', padding: '1rem', marginBottom: '2rem' }}>
          <p style={{ color: '#ef4444', margin: 0, fontSize: '0.875rem', fontWeight: 600 }}>{errorMsg}</p>
        </div>
      )}

      <form onSubmit={handleRegister} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', background: '#0f172a', padding: '2rem', borderRadius: '8px', border: '1px solid #1e293b' }}>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>NÚMERO DE SERIE (SN)</label>
            <input name="serial_number" value={formData.serial_number} onChange={handleChange} required style={{ background: '#1e293b', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }} placeholder="ej. SN-A320-999" />
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>NÚMERO DE PARTE (PN)</label>
            <input name="part_number" value={formData.part_number} onChange={handleChange} required style={{ background: '#1e293b', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }} placeholder="ej. PN-12345" />
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>NOMENCLATURA / DESCRIPCIÓN</label>
          <input name="nomenclature" value={formData.nomenclature} onChange={handleChange} required style={{ background: '#1e293b', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }} placeholder="ej. Bomba Hidráulica Principal" />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>MODELO / TIPO DE ACTIVO</label>
              {!showNewTypeForm && (
                <button type="button" onClick={() => setShowNewTypeForm(true)} style={{ fontSize: '0.75rem', color: '#38bdf8', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}>
                  + Crear Nuevo Modelo
                </button>
              )}
            </div>
            
            {showNewTypeForm ? (
              <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '4px', border: '1px dashed #334155', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <input name="name" value={newTypeData.name} onChange={handleNewTypeChange} placeholder="Nombre del Modelo (ej. F-16 Falcon)" style={{ background: '#0f172a', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }} />
                <select name="category" value={newTypeData.category} onChange={handleNewTypeChange} style={{ background: '#0f172a', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }}>
                  <option value="AIRCRAFT">AERONAVE (AIRCRAFT)</option>
                  <option value="ENGINE">MOTOR (ENGINE)</option>
                  <option value="COMPONENT">COMPONENTE</option>
                  <option value="TOOL">HERRAMIENTA (TOOL)</option>
                </select>
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                  <button type="button" onClick={handleCreateType} disabled={creatingType || !newTypeData.name} style={{ flex: 1, background: '#10b981', color: 'white', border: 'none', padding: '0.5rem', borderRadius: '4px', cursor: 'pointer', fontWeight: 600 }}>{creatingType ? 'Guardando...' : 'Guardar'}</button>
                  <button type="button" onClick={() => setShowNewTypeForm(false)} style={{ flex: 1, background: 'transparent', color: '#94a3b8', border: '1px solid #334155', padding: '0.5rem', borderRadius: '4px', cursor: 'pointer' }}>Cancelar</button>
                </div>
              </div>
            ) : (
              <select name="asset_type_id" value={formData.asset_type_id} onChange={handleChange} required style={{ background: '#1e293b', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }}>
                <option value="">Seleccione un Tipo...</option>
                {assetTypes.map(t => (
                  <option key={t.id} value={t.id}>{t.name} ({t.category})</option>
                ))}
              </select>
            )}
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>ORGANIZACIÓN DUEÑA</label>
            <select name="organization_id" value={formData.organization_id} onChange={handleChange} required style={{ background: '#1e293b', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }}>
              <option value="">Seleccione Organización...</option>
              {organizations.map(o => (
                <option key={o.id} value={o.id}>{o.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <label style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8' }}>CLASIFICACIÓN LOGÍSTICA</label>
          <select name="classification" value={formData.classification} onChange={handleChange} style={{ background: '#1e293b', border: '1px solid #334155', color: 'white', padding: '0.5rem', borderRadius: '4px' }}>
            <option value="REPAIRABLE">REPARABLE</option>
            <option value="CONSUMABLE">CONSUMIBLE</option>
            <option value="ROTABLE">ROTATORIO</option>
            <option value="LIFE_LIMITED">VIDA LÍMITE</option>
          </select>
        </div>

        <div style={{ borderTop: '1px solid #1e293b', paddingTop: '1.5rem', marginTop: '1rem' }}>
          <p style={{ fontSize: '0.75rem', color: '#64748b', marginBottom: '1rem' }}>
            ADVERTENCIA: Registrar un activo clase AERONAVE (AIRCRAFT) disparará automáticamente la creación de su Configuración Basal, Libros Históricos y Registros de Auditoría. Todos los activos nacen en estado PENDIENTE DE ALTA y CUARENTENA.
          </p>
          <button type="submit" disabled={loading || showNewTypeForm} style={{ background: '#0284c7', color: 'white', padding: '0.75rem 1.5rem', borderRadius: '4px', border: 'none', fontWeight: 600, cursor: loading ? 'not-allowed' : 'pointer', width: '100%', letterSpacing: '0.05em' }}>
            {loading ? 'PROCESANDO ALTA TÉCNICA...' : 'EJECUTAR ALTA DE ACTIVO'}
          </button>
        </div>

      </form>
    </div>
  );
}
