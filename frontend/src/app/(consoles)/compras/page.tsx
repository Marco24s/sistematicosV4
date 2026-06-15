'use client';

import React, { useEffect, useState } from 'react';
import { fetchAPI } from '../../../lib/api';

export default function ProcurementConsole() {
  const [activeTab, setActiveTab] = useState('DEMANDS');
  const [loading, setLoading] = useState(false);
  const [output, setOutput] = useState('');

  // Data states
  const [provisionReqs, setProvisionReqs] = useState<any[]>([]);
  const [purchaseReqs, setPurchaseReqs] = useState<any[]>([]);
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [purchaseOrders, setPurchaseOrders] = useState<any[]>([]);
  const [goodsReceptions, setGoodsReceptions] = useState<any[]>([]);

  // Forms states
  const [prForm, setPrForm] = useState({ asset_type: '', quantity: 1, justification: '', priority: 'NORMAL' });
  const [poForm, setPoForm] = useState({ purchase_request_id: '', supplier_id: '', order_number: '' });
  const [receptionForm, setReceptionForm] = useState({ purchase_order_id: '', received_by: 'Logistics Officer' });
  
  const [inspectionForm, setInspectionForm] = useState({
    goods_reception_id: '',
    inspector_id: 'a102f90a-1123-488b-a78b-d72b0c102501',
    supplier_verified: false,
    po_validated: false,
    pn_validated: false,
    sn_validated: false,
    coc_attached: false,
    mfg_cert_attached: false,
    packaging_inspected: false,
    shelf_life_verified: false,
    batch_verified: false,
    physical_condition_valid: false,
    serial_number: '',
    notes: ''
  });

  const loadData = async () => {
    setLoading(true);
    try {
      const [provs, prs, sups, pos, recs] = await Promise.all([
        fetchAPI('/procurement/provision-requests').catch(() => []),
        fetchAPI('/procurement/purchase-requests').catch(() => []),
        fetchAPI('/procurement/suppliers').catch(() => []),
        fetchAPI('/procurement/purchase-orders').catch(() => []),
        fetchAPI('/procurement/goods-receptions').catch(() => [])
      ]);
      setProvisionReqs(provs);
      setPurchaseReqs(prs);
      setSuppliers(sups);
      setPurchaseOrders(pos);
      setGoodsReceptions(recs);
    } catch (e: any) {
      setOutput('Error loading data: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleCreatePR = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await fetchAPI('/procurement/purchase-requests', {
        method: 'POST',
        body: JSON.stringify({
          requested_by_department: 'b102f90a-1123-488b-a78b-d72b0c102502',
          ...prForm
        })
      });
      setOutput('Purchase Request generada exitosamente.');
      setPrForm({ asset_type: '', quantity: 1, justification: '', priority: 'NORMAL' });
      await loadData();
    } catch (err: any) {
      setOutput('Error PR: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePO = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await fetchAPI('/procurement/purchase-orders', {
        method: 'POST',
        body: JSON.stringify(poForm)
      });
      setOutput('Purchase Order generada exitosamente.');
      setPoForm({ purchase_request_id: '', supplier_id: '', order_number: '' });
      await loadData();
    } catch (err: any) {
      setOutput('Error PO: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReceiveGoods = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      await fetchAPI(/procurement/purchase-orders/ + receptionForm.purchase_order_id + /receive, {
        method: 'POST',
        body: JSON.stringify({ received_by: receptionForm.received_by })
      });
      setOutput('Recepción registrada. Paquete en Cuarentena Logística.');
      setReceptionForm({ purchase_order_id: '', received_by: 'Logistics Officer' });
      await loadData();
    } catch (err: any) {
      setOutput('Error Recepción: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleInspection = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await fetchAPI(/procurement/receptions/ + inspectionForm.goods_reception_id + /inspect, {
        method: 'POST',
        body: JSON.stringify(inspectionForm)
      });
      if (res.approved) {
        setOutput('✅ INSPECCIÓN APROBADA. Custodia transferida automáticamente al Arsenal.');
      } else {
        setOutput('❌ INSPECCIÓN RECHAZADA. Componente no ingresa al stock operativo.');
      }
      await loadData();
    } catch (err: any) {
      setOutput('Error Inspección: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const renderTabs = () => (
    <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '10px' }}>
      {['DEMANDS', 'PURCHASE_REQUESTS', 'PURCHASE_ORDERS', 'DOCK_RECEPTION', 'LOGISTICS_INSPECTION'].map(tab => (
        <button 
          key={tab}
          onClick={() => setActiveTab(tab)}
          className={tn }
          style={{ fontSize: '0.75rem' }}
        >
          {tab.replace('_', ' ')}
        </button>
      ))}
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-dark)', padding: '20px' }}>
      <header style={{ marginBottom: '20px' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 'bold', color: 'var(--mil-info)' }}>
          DEPARTAMENTO DE COMPRAS Y ADQUISICIONES
        </h2>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          Cadena de Suministro y Validaciones Logísticas • Procurement Console
        </p>
      </header>

      {output && (
        <div style={{ padding: '10px', background: 'rgba(57, 255, 20, 0.1)', border: '1px solid var(--mil-green)', marginBottom: '20px', fontSize: '0.8rem', color: 'var(--mil-green)' }}>
          {output}
        </div>
      )}

      {renderTabs()}

      {activeTab === 'DEMANDS' && (
        <div className="panel">
          <h3 className="panel-title">Demandas de Stock (Provision Requests)</h3>
          <table className="mil-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Repuesto Solicitado</th>
                <th>Cantidad</th>
                <th>Prioridad</th>
                <th>Estado</th>
              </tr>
            </thead>
            <tbody>
              {provisionReqs.map(p => (
                <tr key={p.id}>
                  <td>{p.id.substring(0,8)}</td>
                  <td>{p.asset_type_requested}</td>
                  <td>{p.quantity}</td>
                  <td><span className="badge badge-alert">{p.priority}</span></td>
                  <td>{p.status}</td>
                </tr>
              ))}
              {provisionReqs.length === 0 && (
                <tr><td colSpan={5} style={{ textAlign: 'center' }}>No hay demandas registradas</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'PURCHASE_REQUESTS' && (
        <div className="grid-2">
          <div className="panel">
            <h3 className="panel-title">Generar Purchase Request</h3>
            <form onSubmit={handleCreatePR} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <input type="text" className="form-control" placeholder="Tipo de Componente (ej. Motor T58)" value={prForm.asset_type} onChange={e => setPrForm({...prForm, asset_type: e.target.value})} required />
              <input type="number" className="form-control" placeholder="Cantidad" value={prForm.quantity} onChange={e => setPrForm({...prForm, quantity: parseInt(e.target.value)})} required />
              <textarea className="form-control" placeholder="Justificación" value={prForm.justification} onChange={e => setPrForm({...prForm, justification: e.target.value})} required />
              <select className="form-control" value={prForm.priority} onChange={e => setPrForm({...prForm, priority: e.target.value})}>
                <option value="LOW">LOW</option>
                <option value="NORMAL">NORMAL</option>
                <option value="HIGH">HIGH</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
              <button type="submit" className="btn btn-primary" disabled={loading}>CREAR PR</button>
            </form>
          </div>
          <div className="panel">
            <h3 className="panel-title">Historial de PRs</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {purchaseReqs.map(pr => (
                <li key={pr.id} style={{ padding: '8px', borderBottom: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                  <strong>{pr.asset_type}</strong> (Cant: {pr.quantity}) - Estado: <span className="badge badge-info">{pr.status}</span>
                  <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>PR ID: {pr.id}</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'PURCHASE_ORDERS' && (
        <div className="grid-2">
          <div className="panel">
            <h3 className="panel-title">Emitir Purchase Order</h3>
            <form onSubmit={handleCreatePO} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <select className="form-control" value={poForm.purchase_request_id} onChange={e => setPoForm({...poForm, purchase_request_id: e.target.value})} required>
                <option value="">Seleccione PR (Solo APPROVED)</option>
                {purchaseReqs.filter(pr => pr.status === 'APPROVED').map(pr => (
                  <option key={pr.id} value={pr.id}>{pr.asset_type} (PR: {pr.id.substring(0,6)})</option>
                ))}
              </select>
              <select className="form-control" value={poForm.supplier_id} onChange={e => setPoForm({...poForm, supplier_id: e.target.value})} required>
                <option value="">Seleccione Proveedor</option>
                {suppliers.map(s => <option key={s.id} value={s.id}>{s.name} ({s.supplier_code})</option>)}
              </select>
              <input type="text" className="form-control" placeholder="Número de Orden (ej. PO-2026-991)" value={poForm.order_number} onChange={e => setPoForm({...poForm, order_number: e.target.value})} required />
              <button type="submit" className="btn btn-primary" disabled={loading}>EMITIR PO</button>
            </form>
          </div>
          <div className="panel">
            <h3 className="panel-title">Órdenes Emitidas</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {purchaseOrders.map(po => (
                <li key={po.id} style={{ padding: '8px', borderBottom: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                  <strong>{po.order_number}</strong> - Estado: <span className="badge badge-info">{po.status}</span>
                  <div style={{ color: 'var(--text-dim)', fontSize: '0.7rem' }}>PO ID: {po.id}</div>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'DOCK_RECEPTION' && (
        <div className="grid-2">
          <div className="panel">
            <h3 className="panel-title">Dock de Recepción Física</h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '10px' }}>
              Registra el ingreso de cajas físicas desde el transporte. El componente pasará a Cuarentena Logística.
            </p>
            <form onSubmit={handleReceiveGoods} style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <select className="form-control" value={receptionForm.purchase_order_id} onChange={e => setReceptionForm({...receptionForm, purchase_order_id: e.target.value})} required>
                <option value="">Seleccione PO Esperada</option>
                {purchaseOrders.filter(po => po.status === 'SENT').map(po => (
                  <option key={po.id} value={po.id}>{po.order_number}</option>
                ))}
              </select>
              <input type="text" className="form-control" value={receptionForm.received_by} onChange={e => setReceptionForm({...receptionForm, received_by: e.target.value})} required />
              <button type="submit" className="btn btn-primary" disabled={loading}>REGISTRAR ARRIBO FÍSICO</button>
            </form>
          </div>
          <div className="panel" style={{ borderLeft: '4px solid var(--mil-alert)' }}>
            <h3 className="panel-title" style={{ color: 'var(--mil-alert)' }}>En Cuarentena Logística</h3>
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {goodsReceptions.filter(gr => gr.status === 'PENDING_LOGISTICS_INSPECTION').map(gr => (
                <li key={gr.id} style={{ padding: '8px', borderBottom: '1px solid var(--border-color)', fontSize: '0.8rem' }}>
                  <strong>ID Recepción:</strong> {gr.id.substring(0,8)} <span className="badge badge-alert">PENDING_INSPECTION</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {activeTab === 'LOGISTICS_INSPECTION' && (
        <div className="panel" style={{ border: '2px solid var(--mil-alert)' }}>
          <h3 className="panel-title" style={{ color: 'var(--mil-alert)' }}>INSPECCIÓN LOGÍSTICA ESTRICTA (10 PUNTOS)</h3>
          <form onSubmit={handleInspection} className="grid-2" style={{ gap: '20px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <select className="form-control" value={inspectionForm.goods_reception_id} onChange={e => setInspectionForm({...inspectionForm, goods_reception_id: e.target.value})} required>
                <option value="">Seleccione Recepción Pendiente</option>
                {goodsReceptions.filter(gr => gr.status === 'PENDING_LOGISTICS_INSPECTION').map(gr => (
                  <option key={gr.id} value={gr.id}>Recepción ID: {gr.id.substring(0,8)}</option>
                ))}
              </select>
              <input type="text" className="form-control" placeholder="Serial Number (Extraído del componente)" value={inspectionForm.serial_number} onChange={e => setInspectionForm({...inspectionForm, serial_number: e.target.value})} required />
              <textarea className="form-control" placeholder="Observaciones de Inspección..." value={inspectionForm.notes} onChange={e => setInspectionForm({...inspectionForm, notes: e.target.value})}></textarea>
            </div>
            
            <div style={{ background: '#0a0d10', padding: '16px', borderRadius: '4px', border: '1px solid var(--border-color)' }}>
              <p style={{ fontSize: '0.8rem', color: 'var(--mil-alert)', marginBottom: '10px', fontWeight: 'bold' }}>CHECKLIST OBLIGATORIO DE FIRMA DIGITAL</p>
              
              {[
                { key: 'supplier_verified', label: 'Verificación de Proveedor (Vendor Check)' },
                { key: 'po_validated', label: 'Validación de Purchase Order' },
                { key: 'pn_validated', label: 'Part Number correcto (Data Plate)' },
                { key: 'sn_validated', label: 'Serial Number validado' },
                { key: 'coc_attached', label: 'Certificate of Conformity (CoC) Adjunto' },
                { key: 'mfg_cert_attached', label: 'Manufacturer Certification (8130-3 / EASA Form 1)' },
                { key: 'packaging_inspected', label: 'Inspección de Embalaje / Precintos' },
                { key: 'shelf_life_verified', label: 'Verificación de Shelf life / Vencimiento' },
                { key: 'batch_verified', label: 'Validación de Batch/Lot Traceability' },
                { key: 'physical_condition_valid', label: 'Condición Física (Sin daños, sin corrosión)' },
              ].map(item => (
                <label key={item.key} style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '0.8rem', marginBottom: '8px', cursor: 'pointer' }}>
                  <input 
                    type="checkbox" 
                    checked={(inspectionForm as any)[item.key]} 
                    onChange={e => setInspectionForm({...inspectionForm, [item.key]: e.target.checked})}
                  />
                  <span style={{ color: (inspectionForm as any)[item.key] ? 'var(--mil-green)' : '#fff' }}>{item.label}</span>
                </label>
              ))}
              
              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginTop: '16px' }} disabled={loading}>
                EJECUTAR FIRMA DE INSPECCIÓN LOGÍSTICA
              </button>
            </div>
          </form>
        </div>
      )}

    </div>
  );
}
