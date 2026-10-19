import './budget-module.css';

export function renderBudgetModule(ctx) {
  const root = ctx.root, db = ctx.db, can = ctx.can;
  const canEdit = can('presupuestos', 'edit');
  const canReadCosts = can('presupuestos', 'costs');
  const canEditCosts = can('presupuestos', 'costs-edit');
  const catalog = Array.isArray(ctx.laborCatalog) ? ctx.laborCatalog : [];
  let activeTab = ctx.pendingLaborId && canEdit ? 'formal' : (ctx.initialTab || (canEdit ? 'formal' : (canReadCosts ? 'costs' : 'records')));
  let editingQuote = null, selectedCostId = '', pendingLaborId = ctx.pendingLaborId || '';

  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const parseMoney = value => {
    const raw = String(value ?? '').trim().replace(/[\s$]/g, '');
    if (!raw) return 0;
    const normalized = raw.includes(',') ? raw.replace(/\./g, '').replace(',', '.') : raw.replace(/\./g, '');
    const n = Number(normalized); return Number.isFinite(n) ? n : 0;
  };
  const money = value => new Intl.NumberFormat('es-AR', {minimumFractionDigits:0, maximumFractionDigits:2}).format(Number(value) || 0);
  const moneyInput = value => {
    const n = parseMoney(value);
    if (!Number.isFinite(n)) return '';
    const parts = Math.abs(n).toFixed(2).replace(/0+$/, '').replace(/\.$/, '').split('.');
    return (n < 0 ? '-' : '') + parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (parts[1] ? ',' + parts[1] : '');
  };
  const inputMoney = value => {
    const raw = String(value ?? '').replace(/[^\d,]/g, '');
    if (!raw) return '';
    const split = raw.split(',');
    const integerDigits = (split.shift() || '').replace(/\D/g, '');
    const decimal = split.join('').replace(/\D/g, '').slice(0, 2);
    return integerDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (raw.includes(',') ? ',' + decimal : '');
  };
  const dateToday = () => typeof ctx.today === 'function' ? ctx.today() : new Date().toISOString().slice(0,10);
  const customerName = id => { const c = db.clientes.find(x => String(x.id) === String(id)); return c ? String(c.nombre || '') + (c.empresa ? ' · ' + c.empresa : '') : 'Sin cliente asignado'; };
  const vehicleName = id => { const v = db.vehiculos.find(x => String(x.id) === String(id)); return v ? [v.patente,v.marca,v.modelo,v.anio ? 'Año '+v.anio : ''].filter(Boolean).join(' · ') : 'Sin vehículo asignado'; };
  const vehicleLabel = v => [v.patente,v.marca,v.modelo,v.anio ? 'Año '+v.anio : ''].filter(Boolean).join(' · ');
  const workName = id => { const w = db.trabajos.find(x => String(x.id) === String(id)); return w ? [w.numero,vehicleName(w.vehiculoId),w.trabajo||w.problema].filter(Boolean).join(' · ') : 'Sin orden vinculada'; };
  const options = (items,labeler,selected,placeholder) => '<option value="">' + esc(placeholder || '— Seleccionar —') + '</option>' + items.map(item => '<option value="' + esc(item.id) + '"' + (String(item.id) === String(selected ?? '') ? ' selected' : '') + '>' + esc(labeler(item)) + '</option>').join('');
  const amount = value => '$ ' + money(value);
  const formalQuotes = () => db.presupuestos.filter(q => q && q.tipo !== 'Orientativo');
  const quoteTitle = q => (q.tipo === 'Orientativo' ? 'Consulta orientativa' : 'Presupuesto') + ' · ' + (q.fecha || '') + ' · ' + (q.vehiculoReferencia || (q.vehiculoId ? vehicleName(q.vehiculoId) : customerName(q.clienteId)));
  const quoteText = q => {
    const total = q.tipo === 'Orientativo' ? parseMoney(q.estimacionMinima) : parseMoney(q.importe);
    const price = q.tipo === 'Orientativo' && q.usarRangoPrecio && Math.abs(parseMoney(q.estimacionMaxima)-total) > .005
      ? amount(total) + ' a ' + amount(q.estimacionMaxima) : amount(total);
    const scope = String(q.alcanceOrientativo || q.alcanceTrabajo || q.detalle || '').trim();
    const count = Number(q.ofrecerCuotasFormal ? q.cantidadCuotasFormal : q.cantidadCuotasQuick) || 0;
    const installments = (q.ofrecerCuotasFormal || q.ofrecerCuotasQuick) && count > 1
      ? '\n\nAlternativa de pago: ' + count + ' cuotas estimadas de ' + amount(total/count) + ((q.condicionesCuotasFormal || q.condicionesCuotasQuick) ? '. Condición: ' + (q.condicionesCuotasFormal || q.condicionesCuotasQuick) : '') + '.' : '';
    return 'Hola, te comparto ' + (q.tipo === 'Orientativo' ? 'una consulta orientativa' : 'el presupuesto de reparación') + ' para ' +
      (q.trabajoOrientativo || q.detalle || 'el trabajo consultado') + (q.vehiculoReferencia ? ' en '+q.vehiculoReferencia : (q.vehiculoId ? ' para '+vehicleName(q.vehiculoId) : '')) +
      '.\n\nImporte: ' + price + (scope ? '\n\nAlcance: '+scope : '') +
      (q.tipo === 'Orientativo' ? '\n\nEs una referencia inicial, no un presupuesto definitivo. El alcance y los repuestos deben confirmarse.' : '') +
      installments + '\n\nServicios Mecánicos Enzo';
  };
  const customerDocument = q => {
    const rows = [];
    const add = (label,value) => { if(value !== undefined && value !== null && String(value).trim() !== '') rows.push('<tr><th>'+esc(label)+'</th><td>'+esc(value)+'</td></tr>'); };
    add('Fecha',q.fecha || dateToday());
    if(q.tipo === 'Orientativo'){
      add('Vehículo / referencia',q.vehiculoReferencia); add('Trabajo consultado',q.trabajoOrientativo);
      add('Precio estimado',q.usarRangoPrecio && Math.abs(parseMoney(q.estimacionMaxima)-parseMoney(q.estimacionMinima))>.005 ? amount(q.estimacionMinima)+' a '+amount(q.estimacionMaxima) : amount(q.estimacionMinima));
      add('Qué podría incluir / qué falta confirmar',q.alcanceOrientativo);
      add('Nota importante','Referencia orientativa. El alcance y los repuestos deben confirmarse al revisar el vehículo. No se realizarán trabajos adicionales sin autorización.');
    } else {
      add('Cliente',customerName(q.clienteId)); add('Vehículo',q.vehiculoId ? vehicleName(q.vehiculoId) : q.vehiculoReferencia);
      add('Orden relacionada',q.trabajoId ? workName(q.trabajoId) : '');
      add('Diagnóstico comunicado',q.diagnosticoCliente); add('Solución recomendada',q.solucionRecomendada);
      add('Alcance / tareas incluidas',q.alcanceTrabajo || q.detalle);
      add('Mano de obra',amount(q.manoObra)); add('Repuestos y materiales',amount(q.repuestos));
      add('Servicios externos, insumos y otros trabajos',amount(q.otrosConceptos)); add('Detalle de conceptos adicionales',q.detalleOtrosConceptos);
      add('Total propuesto',amount(q.importe));
      if(q.ofrecerCuotasFormal && Number(q.cantidadCuotasFormal)>1){
        add('Alternativa de pago',q.cantidadCuotasFormal+' cuotas estimadas de '+amount(parseMoney(q.importe)/Number(q.cantidadCuotasFormal)));
        add('Condición del medio de pago',q.condicionesCuotasFormal);
      }
      add('Validez de la propuesta',q.vigenciaDias ? q.vigenciaDias+' días' : ''); add('Plazo estimado de entrega',q.plazoEstimado);
      add('Condiciones de pago',q.condicionesPago); add('Garantía / condiciones aplicables',q.condicionesGarantia);
      add('Trabajos o repuestos no incluidos',q.trabajosExcluidos);
      add('Control posterior',q.controlPosterior==='si' ? (q.condicionesControl || 'Control posterior a coordinar') : '');
      add('Aclaraciones',q.notaCliente); add('Importante','No se realizarán trabajos adicionales sin autorización del cliente. Conservá una copia de esta propuesta.');
    }
    return rows.join('');
  };
  const buildDocumentHtml = q => '<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>' +
    esc(q.tipo==='Orientativo'?'Consulta orientativa':'Presupuesto de reparación') +
    '</title><style>@page{size:auto;margin:10mm}*{box-sizing:border-box;-webkit-print-color-adjust:exact;print-color-adjust:exact}body{font:12pt/1.45 Arial,sans-serif;color:#222;margin:0}header{border-bottom:3px solid #b99861;padding:0 0 12px;margin-bottom:16px;color:#173a3e}h1{font:700 23pt Georgia,serif;margin:0 0 4px}h2{font:600 18pt Georgia,serif;margin:10px 0;color:#173a3e}p{margin:6px 0 12px}table{width:100%;border-collapse:collapse;table-layout:fixed}th,td{border:1px solid #c6c2b8;padding:9px;vertical-align:top;overflow-wrap:anywhere;white-space:pre-wrap}th{width:32%;text-align:left;background:#f4efe5}footer{border-top:1px solid #bbb;margin-top:20px;padding-top:8px;font-size:9pt;color:#555}@media print{tr{break-inside:avoid}body{font-size:12pt}}</style></head><body><header><h1>Servicios Mecánicos Enzo</h1><p>El oficio de siempre, al servicio de hoy.</p></header><h2>' +
    esc(q.tipo==='Orientativo'?'Consulta orientativa':'Presupuesto de reparación') + '</h2><table>' + customerDocument(q) +
    '</table><footer>Documento para el cliente. Los costos, márgenes y cálculos internos del taller no forman parte de este documento.</footer></body></html>';

  const filteredQuotes = () => [...db.presupuestos].filter(q => {
    const f = ctx.relatedFilter; if(!f) return true;
    if(f.clientId && String(q.clienteId || '') !== String(f.clientId)) return false;
    if(f.vehicleId && String(q.vehiculoId || '') !== String(f.vehicleId)) return false;
    if(f.workId && String(q.trabajoId || '') !== String(f.workId)) return false;
    return true;
  }).reverse();
  const statusOptions = ['Borrador','Enviado al cliente','Aprobado','Rechazado','Vencido','En ejecución','Pendiente de pago','Entregado','Finalizado','Cancelado'];
  const laborMarkup = prefix => '<section class="sme-budget-v2-time"><div class="sme-budget-v2-section-heading"><h3>Asistente de tiempos orientativos</h3><span>Referencia, no tarifa</span></div>' +
    '<p class="muted">Buscá una operación o motor, elegí una referencia y definí tu tarifa. Nada cambia un presupuesto guardado hasta que decidas aplicarlo y guardes el formulario.</p>' +
    '<label>Buscar trabajo o motor<input id="'+prefix+'-time-search" type="search" placeholder="Ej.: junta tapa 8v, distribución K4M, embrague" autocomplete="off"></label>' +
    '<div id="'+prefix+'-time-selected" class="sme-budget-v2-time-selected" hidden></div>' +
    '<div id="'+prefix+'-time-calc" class="sme-budget-v2-time-calc" hidden><div class="sme-budget-v2-grid"><label>Horas mínimas<input id="'+prefix+'-hours-min" type="number" min="0.25" step="0.25"></label><label>Horas habituales<input id="'+prefix+'-hours" type="number" min="0.25" step="0.25"></label><label>Horas máximas<input id="'+prefix+'-hours-max" type="number" min="0.25" step="0.25"></label><label>Tu tarifa por hora ($)<input id="'+prefix+'-rate" data-money type="text" inputmode="numeric" autocomplete="off" placeholder="Ingresala vos"></label><label>Otros costos mínimos ($)<input id="'+prefix+'-other-min" data-money type="text" inputmode="numeric" value="0"></label><label>Otros costos máximos ($)<input id="'+prefix+'-other-max" data-money type="text" inputmode="numeric" value="0"></label></div><p id="'+prefix+'-time-preview" class="muted" aria-live="polite">Ingresá las horas y la tarifa para ver el cálculo.</p><button type="button" class="secondary" id="'+prefix+'-apply-time" disabled>Usar cálculo</button></div>' +
    '<div id="'+prefix+'-time-results" class="sme-budget-v2-time-results" aria-live="polite"><p class="muted">Escribí el nombre del trabajo o motor para ver coincidencias.</p></div><div class="quick"><button type="button" class="secondary" data-budget-open-times>Abrir tabla completa de tiempos</button></div></section>';
  const installmentMarkup = (kind,q) => {
    const formal = kind==='formal', checked = formal ? !!q.ofrecerCuotasFormal : !!q.ofrecerCuotasQuick;
    const count = formal ? (q.cantidadCuotasFormal || '3') : (q.cantidadCuotasQuick || '3');
    const terms = formal ? (q.condicionesCuotasFormal || '') : (q.condicionesCuotasQuick || '');
    return '<section class="sme-budget-v2-installments"><h3>Opciones de cuotas para el cliente</h3><p class="muted">Mostrá esta alternativa únicamente cuando las condiciones reales del medio de pago la permitan.</p><label class="sme-budget-v2-check"><input type="checkbox" name="offerInstallments" '+(checked?'checked':'')+'> Ofrecer cuotas fijas sin interés</label><div data-installment-fields '+(checked?'':'hidden')+'><label>Cantidad de cuotas<select name="installmentCount"><option value="2"'+(String(count)==='2'?' selected':'')+'>2 cuotas</option><option value="3"'+(String(count)==='3'?' selected':'')+'>3 cuotas</option><option value="6"'+(String(count)==='6'?' selected':'')+'>6 cuotas</option><option value="12"'+(String(count)==='12'?' selected':'')+'>12 cuotas</option></select></label><label>Condición del medio de pago (opcional)<input name="installmentTerms" maxlength="220" value="'+esc(terms)+'" placeholder="Ej.: plan confirmado por el proveedor"></label><p class="sme-budget-v2-installment-preview" data-installment-preview>Completá los importes para ver el valor por cuota.</p></div></section>';
  };
  const quickMarkup = q => {
    const edit = q && q.tipo==='Orientativo' ? q : {}, min = edit.estimacionMinima ?? '', max = edit.estimacionMaxima ?? '';
    return '<section class="panel"><h3>'+(editingQuote?'Editar consulta orientativa':'Consulta rápida')+'</h3><p class="muted">Para responder sin exigir cliente ni vehículo registrado. Por defecto se ofrece un precio único; el rango es opcional.</p>' +
      '<form id="sme-budget-quick-form" novalidate><div class="sme-budget-v2-grid"><label>Vehículo / referencia<input name="vehicleReference" maxlength="120" required value="'+esc(edit.vehiculoReferencia||'')+'" placeholder="Ej.: Volkswagen Gol, motor por confirmar"></label><label>Trabajo consultado<input name="jobReference" maxlength="160" required value="'+esc(edit.trabajoOrientativo||'')+'" placeholder="Ej.: cambio de junta de tapa"></label></div>' +
      '<label>Precio único al cliente ($)<input name="quickPrice" data-money type="text" inputmode="numeric" required value="'+esc(moneyInput(min))+'" placeholder="Ej.: 250.000"></label>' +
      '<label class="sme-budget-v2-check"><input type="checkbox" name="usePriceRange" '+(edit.usarRangoPrecio?'checked':'')+'> Ofrecer un rango de precios en lugar de un precio único</label><div data-price-range-fields '+(edit.usarRangoPrecio?'':'hidden')+'><label>Precio máximo / hasta ($)<input name="quickPriceMax" data-money type="text" inputmode="numeric" '+(edit.usarRangoPrecio?'required':'disabled')+' value="'+esc(moneyInput(max))+'" placeholder="Ej.: 300.000"></label></div>' +
      '<label>Qué podría incluir / qué falta confirmar<textarea name="quickScope" rows="3" maxlength="1000" placeholder="Mano de obra, repuestos, rectificadora y verificaciones; sujeto a diagnóstico.">'+esc(edit.alcanceOrientativo||'')+'</textarea></label>' +
      '<input type="hidden" name="laborTimeId" value="'+esc(edit.operacionTiempoOrientativa||'')+'"><input type="hidden" name="hoursEstimatedMin" value="'+esc(edit.horasEstimadasMinimas||'')+'"><input type="hidden" name="hoursEstimatedUsual" value="'+esc(edit.horasEstimadasHabituales||'')+'"><input type="hidden" name="hoursEstimatedMax" value="'+esc(edit.horasEstimadasMaximas||'')+'"><input type="hidden" name="rateEstimated" value="'+esc(edit.tarifaHoraOrientativa||'')+'"><input type="hidden" name="otherCostMin" value="'+esc(edit.costoAdicionalMinimo||'')+'"><input type="hidden" name="otherCostMax" value="'+esc(edit.costoAdicionalMaximo||'')+'">' +
      laborMarkup('quick')+installmentMarkup('quick',edit)+'<div class="sme-budget-v2-error" data-budget-error role="alert"></div><button type="submit" class="accent">'+(editingQuote?'Guardar cambios':'Guardar consulta rápida')+'</button><button type="button" class="secondary" data-budget-cancel-edit '+(editingQuote?'':'hidden')+'>Cancelar edición</button></form></section>';
  };
  const formalMarkup = q => {
    const edit = q && q.tipo!=='Orientativo' ? q : {}, linked = db.trabajos.find(x=>String(x.id)===String(edit.trabajoId||''));
    const selectedClient = edit.clienteId || (linked && linked.clienteId) || '';
    const selectedVehicle = edit.vehiculoId || (linked && linked.vehiculoId) || '';
    const clientOptions = options(db.clientes,x=>x.nombre+(x.empresa?' · '+x.empresa:''),selectedClient,'Seleccioná un cliente');
    const vehicleOptions = options(db.vehiculos.filter(x=>!selectedClient||String(x.clienteId||'')===String(selectedClient)),vehicleLabel,selectedVehicle,'Seleccioná un vehículo');
    const orderOptions = options(db.trabajos,x=>[x.numero,x.trabajo||x.problema||'Orden de trabajo'].filter(Boolean).join(' · '),edit.trabajoId||'','Sin orden vinculada');
    const labor=edit.manoObra??'', parts=edit.repuestos??'', other=edit.otrosConceptos??'', total=parseMoney(labor)+parseMoney(parts)+parseMoney(other);
    return '<section class="panel"><h3>'+(editingQuote?'Editar presupuesto formal':'Presupuesto formal')+'</h3><p class="muted">Propuesta vinculada al cliente y al vehículo. El total suma mano de obra, repuestos, servicios externos e insumos.</p>' +
      '<form id="sme-budget-formal-form" novalidate><div class="sme-budget-v2-grid"><label>Fecha<input type="date" name="fecha" required value="'+esc(edit.fecha||dateToday())+'"></label><label>Estado<select name="estado">'+statusOptions.map(s=>'<option value="'+esc(s)+'"'+(String(edit.estado||'Borrador')===s?' selected':'')+'>'+esc(s)+'</option>').join('')+'</select></label></div>' +
      '<label>Cliente<select name="clienteId" required>'+clientOptions+'</select></label><label>Vehículo<select name="vehiculoId" required>'+vehicleOptions+'</select></label><label>Orden de trabajo relacionada (opcional)<select name="trabajoId">'+orderOptions+'</select></label>' +
      '<label>Detalle / trabajo a realizar<textarea name="detalle" rows="3" maxlength="1400" required placeholder="Describí con claridad el trabajo que se cotiza.">'+esc(edit.detalle||'')+'</textarea></label>' +
      '<div class="sme-budget-v2-grid"><label>Mano de obra ($)<input name="laborAmount" data-money type="text" inputmode="numeric" required value="'+esc(moneyInput(labor))+'"></label><label>Repuestos y materiales ($)<input name="partsAmount" data-money type="text" inputmode="numeric" required value="'+esc(moneyInput(parts))+'"></label><label>Servicios externos, insumos y otros trabajos ($)<input name="otherAmount" data-money type="text" inputmode="numeric" value="'+esc(moneyInput(other))+'"></label><label>Total propuesto ($)<input name="budgetTotal" type="text" readonly value="'+esc(moneyInput(total))+'"></label></div>' +
      '<input type="hidden" name="laborTimeId" value="'+esc(edit.operacionTiempoOrientativa||'')+'"><input type="hidden" name="hoursEstimatedMin" value="'+esc(edit.horasEstimadasMinimas||'')+'"><input type="hidden" name="hoursEstimatedUsual" value="'+esc(edit.horasEstimadasHabituales||'')+'"><input type="hidden" name="hoursEstimatedMax" value="'+esc(edit.horasEstimadasMaximas||'')+'"><input type="hidden" name="rateEstimated" value="'+esc(edit.tarifaHoraOrientativa||'')+'"><input type="hidden" name="otherCostMin" value="'+esc(edit.costoAdicionalMinimo||'')+'"><input type="hidden" name="otherCostMax" value="'+esc(edit.costoAdicionalMaximo||'')+'">' +
      laborMarkup('formal')+installmentMarkup('formal',edit)+'<details class="sme-budget-v2-details"><summary>Condiciones y presentación para el cliente</summary>' +
      '<label>Motivo / diagnóstico comunicado al cliente<textarea name="diagnosticoCliente" rows="2" maxlength="900">'+esc(edit.diagnosticoCliente||'')+'</textarea></label><label>Solución recomendada y por qué<textarea name="solucionRecomendada" rows="3" maxlength="1200">'+esc(edit.solucionRecomendada||'')+'</textarea></label><label>Alcance / tareas incluidas<textarea name="alcanceTrabajo" rows="3" maxlength="1400">'+esc(edit.alcanceTrabajo||'')+'</textarea></label>' +
      '<div class="sme-budget-v2-grid"><label>Validez de la propuesta<select name="vigenciaDias">'+['3','7','10','15'].map(d=>'<option value="'+d+'"'+(String(edit.vigenciaDias||'7')===d?' selected':'')+'>'+d+' días</option>').join('')+'</select></label><label>Plazo estimado de entrega<input name="plazoEstimado" maxlength="120" value="'+esc(edit.plazoEstimado||'')+'" placeholder="A confirmar según diagnóstico y repuestos"></label></div>' +
      '<label>Condiciones de pago<input name="condicionesPago" maxlength="240" value="'+esc(edit.condicionesPago||'')+'"></label><label>Garantía / condiciones aplicables<textarea name="condicionesGarantia" rows="2" maxlength="500">'+esc(edit.condicionesGarantia||'')+'</textarea></label><label>Detalle de servicios externos, insumos y otros trabajos<textarea name="detalleOtrosConceptos" rows="2" maxlength="700">'+esc(edit.detalleOtrosConceptos||'')+'</textarea></label><label>Trabajos o repuestos no incluidos<textarea name="trabajosExcluidos" rows="2" maxlength="700">'+esc(edit.trabajosExcluidos||'')+'</textarea></label>' +
      '<label>Control posterior ofrecido<select name="controlPosterior"><option value="no"'+(String(edit.controlPosterior||'no')==='no'?' selected':'')+'>No incluir una oferta de control posterior</option><option value="si"'+(String(edit.controlPosterior||'')==='si'?' selected':'')+'>Incluir control posterior (si está confirmado)</option></select></label><label>Detalle del control posterior<input name="condicionesControl" maxlength="180" value="'+esc(edit.condicionesControl||'')+'"></label><label>Detalle adicional para el cliente<textarea name="notaCliente" rows="2" maxlength="500">'+esc(edit.notaCliente||'')+'</textarea></label></details>' +
      '<div class="sme-budget-v2-error" data-budget-error role="alert"></div><button type="submit" class="accent">'+(editingQuote?'Guardar cambios':'Guardar presupuesto')+'</button><button type="button" class="secondary" data-budget-cancel-edit '+(editingQuote?'':'hidden')+'>Cancelar edición</button></form></section>';
  };
  function historyItemsMarkup(list) {
    if(!list.length) return '<div class="panel muted">Todavía no hay presupuestos ni consultas guardadas.</div>';
    return list.map(q => {
      const orientative=q.tipo==='Orientativo', customer=q.clienteId?customerName(q.clienteId):'Consulta sin cliente', vehicle=q.vehiculoId?vehicleName(q.vehiculoId):(q.vehiculoReferencia||'Sin vehículo');
      const total=orientative ? (q.usarRangoPrecio&&Math.abs(parseMoney(q.estimacionMaxima)-parseMoney(q.estimacionMinima))>.005 ? amount(q.estimacionMinima)+' a '+amount(q.estimacionMaxima) : amount(q.estimacionMinima)) : amount(q.importe);
      return '<article class="sme-budget-v2-record"><div class="sme-budget-v2-record-heading"><div><h4>'+esc(quoteTitle(q))+'</h4><p>'+esc(customer)+' · '+esc(vehicle)+'</p></div><strong>'+esc(total)+'</strong></div><p class="sme-budget-v2-record-detail">'+esc(q.trabajoOrientativo||q.detalle||'')+'</p><div class="sme-budget-v2-tags"><span>'+esc(orientative?'Consulta rápida':'Formal')+'</span><span>'+esc(q.estado||'Borrador')+'</span></div><div class="quick">' +
        (canEdit ? '<button type="button" class="secondary" data-budget-edit="'+esc(q.id)+'">Editar</button><button type="button" class="secondary" data-budget-delete="'+esc(q.id)+'">Eliminar</button>' : '') +
        '<button type="button" class="secondary" data-budget-print="'+esc(q.id)+'">Imprimir / PDF</button><button type="button" class="secondary" data-budget-share="'+esc(q.id)+'">Compartir</button>' +
        (q.clienteId?'<button type="button" class="secondary" data-budget-related="clientes" data-budget-client="'+esc(q.clienteId)+'">Ver cliente</button>':'') +
        (q.vehiculoId?'<button type="button" class="secondary" data-budget-related="vehiculos" data-budget-vehicle="'+esc(q.vehiculoId)+'">Ver vehículo</button>':'') +
        (q.trabajoId?'<button type="button" class="secondary" data-budget-related="trabajos" data-budget-work="'+esc(q.trabajoId)+'">Ver orden</button>':'') + '</div></article>';
    }).join('');
  }
  function costField(name,label,defaultValue,type='text') {
    const numeric=type==='number';
    return '<label>'+esc(label)+'<input name="'+name+'" data-cost-field="'+name+'" type="'+(numeric?'number':'text')+'"'+(numeric?' step="0.25" min="0" inputmode="decimal":' data-money inputmode="numeric")+' value="'+esc(defaultValue)+'"'+(canEditCosts?'':' disabled')+'></label>';
  }
  const costMarkup = () => {
    const quotes=formalQuotes();
    return '<section class="panel sme-budget-v2-cost"><div class="sme-budget-v2-section-heading"><h3>Costos internos y rentabilidad</h3><span class="sme-budget-v2-private">SOLO USO INTERNO</span></div><p class="muted">Esta sección nunca se incorpora al documento ni al mensaje enviado al cliente. Son estimaciones internas del taller.</p>' +
      (quotes.length ? '<label>Presupuesto formal<select id="sme-budget-cost-quote">'+options(quotes,q=>quoteTitle(q)+' · '+amount(q.importe),selectedCostId||quotes[0].id,'Seleccioná un presupuesto')+'</select></label><form id="smeInternalCostForm" novalidate><div class="sme-budget-v2-grid">' +
      costField('hours','Horas previstas','0','number')+costField('hourlyCost','Costo interno de mano de obra por hora ($)','0')+costField('partsCost','Costo interno de repuestos ($)','0')+costField('externalCost','Servicios externos ($)','0')+costField('consumablesCost','Insumos ($)','0')+costField('shippingCost','Traslados y logística ($)','0')+costField('overheadCost','Gastos indirectos asignados ($)','0')+costField('paymentFeePct','Comisión de cobro (%)','0','number')+costField('paymentFeeFixed','Costo fijo por cobro ($)','0')+costField('taxRatePct','Impuestos estimados sobre venta (%)','0','number')+costField('targetMarginPct','Margen objetivo (%)','25','number') +
      '</div><div id="sme-budget-cost-summary" class="sme-budget-v2-cost-summary" aria-live="polite"></div><div class="quick"><button type="submit" class="accent" '+(canEditCosts?'':'disabled')+'>Guardar análisis interno</button><button type="button" class="secondary" id="sme-budget-apply-price" '+(canEditCosts?'':'disabled')+'>Aplicar precio mínimo al borrador</button></div></form>'
      : '<div class="muted">Primero guardá un presupuesto formal para analizar sus costos.</div>') + '</section>';
  };
  function draw(tab=activeTab) {
    activeTab=tab;
    const allowedTabs=[];
    if(canEdit) allowedTabs.push(['quick','Consulta rápida'],['formal','Presupuesto formal']);
    if(canReadCosts) allowedTabs.push(['costs','Costos internos']);
    allowedTabs.push(['records','Historial']);
    if(!allowedTabs.some(item=>item[0]===activeTab)) activeTab=allowedTabs[0][0];
    const filterNotice=ctx.relatedFilter?'<div class="panel muted">Mostrando presupuestos vinculados. <button type="button" class="secondary" data-budget-clear-related>Ver todos</button></div>':'';
    root.innerHTML='<section class="sme-budget-v2"><header class="sme-budget-v2-header"><p class="sme-budget-v2-eyebrow">SERVICIOS MECÁNICOS ENZO</p><h2 class="section-title">Presupuestos</h2><p class="muted">Propuestas claras para el cliente; costos y márgenes siempre separados para uso interno.</p></header>'+filterNotice+
      '<div class="sme-budget-v2-tabs" role="tablist" aria-label="Secciones de presupuestos">'+allowedTabs.map(item=>'<button type="button" data-budget-tab="'+item[0]+'" aria-pressed="'+(item[0]===activeTab?'true':'false')+'">'+item[1]+'</button>').join('')+'</div>' +
      (canEdit?'<section data-budget-pane="quick" '+(activeTab==='quick'?'':'hidden')+'>'+quickMarkup(editingQuote&&editingQuote.tipo==='Orientativo'?editingQuote:null)+'</section><section data-budget-pane="formal" '+(activeTab==='formal'?'':'hidden')+'>' +
        (!db.clientes.length?'<div class="panel muted">Para un presupuesto formal necesitás registrar primero al cliente y su vehículo. La consulta rápida no tiene ese requisito.</div>':'')+formalMarkup(editingQuote&&editingQuote.tipo!=='Orientativo'?editingQuote:null)+'</section>':'') +
      (canReadCosts?'<section data-budget-pane="costs" '+(activeTab==='costs'?'':'hidden')+'>'+costMarkup()+'</section>':'') +
      '<section data-budget-pane="records" '+(activeTab==='records'?'':'hidden')+'><section class="sme-budget-v2-history"><div class="sme-budget-v2-section-heading"><h3>Historial de presupuestos</h3><span>'+filteredQuotes().length+' registros</span></div><label>Buscar en el historial<input id="sme-budget-history-search" type="search" placeholder="Cliente, vehículo, trabajo, estado o importe"></label><div id="sme-budget-history-list">'+historyItemsMarkup(filteredQuotes())+'</div></section></section></section>';
    root.querySelectorAll('[data-budget-tab]').forEach(button=>button.addEventListener('click',()=>draw(button.dataset.budgetTab)));
    root.querySelector('[data-budget-clear-related]')?.addEventListener('click',()=>ctx.clearRelated?.());
    root.querySelectorAll('[data-budget-open-times]').forEach(button=>button.addEventListener('click',()=>ctx.navigate('tiempos')));
    root.querySelectorAll('[data-budget-cancel-edit]').forEach(button=>button.addEventListener('click',()=>{editingQuote=null;draw(activeTab)}));
    bindQuickForm(); bindFormalForm(); bindCostForm(); bindHistory();
    if(activeTab==='quick'||activeTab==='formal') initializeLaborAssist(activeTab);
    if(ctx.clearPendingLaborId&&pendingLaborId){ctx.clearPendingLaborId();pendingLaborId='';}
  }
  function bindMoneyInputs(scope) {
    scope.querySelectorAll('[data-money]').forEach(input=>{
      input.addEventListener('input',()=>{
        const old=input.value, pos=input.selectionStart??old.length, digitsBefore=old.slice(0,pos).replace(/\D/g,'').length, hadComma=old.slice(0,pos).includes(',');
        input.value=inputMoney(old);
        let seen=0,next=0;while(next<input.value.length&&seen<digitsBefore){if(/\d/.test(input.value[next]))seen++;next++}
        if(hadComma&&input.value[next]===',')next++;try{input.setSelectionRange(next,next)}catch(_){}
      });
      input.addEventListener('blur',()=>{if(input.value)input.value=moneyInput(input.value)});
      if(input.value)input.value=moneyInput(input.value);
    });
  }
  function bindInstallments(form,totalFn) {
    const check=form.elements.offerInstallments, fields=form.querySelector('[data-installment-fields]'), preview=form.querySelector('[data-installment-preview]');
    const paint=()=>{
      if(!fields||!check||!preview)return;
      fields.hidden=!check.checked;
      const count=Number(form.elements.installmentCount?.value||3),total=totalFn();
      preview.textContent=check.checked&&total>0&&count>1
        ? count+' cuotas estimadas de '+amount(total/count)+'. Confirmá que el medio de pago realmente ofrece esta condición.'
        : 'Completá los importes para ver el valor por cuota.';
    };
    form.addEventListener('input',paint);form.addEventListener('change',paint);paint();return paint;
  }
  function bindQuickForm() {
    const form=root.querySelector('#sme-budget-quick-form');if(!form)return;
    bindMoneyInputs(form);
    const min=form.elements.quickPrice,max=form.elements.quickPriceMax,useRange=form.elements.usePriceRange,range=form.querySelector('[data-price-range-fields]');
    const total=()=>parseMoney(min.value);
    const paintInstallments=bindInstallments(form,total);
    const paintRange=()=>{range.hidden=!useRange.checked;max.disabled=!useRange.checked;max.required=useRange.checked;paintInstallments()};
    useRange.addEventListener('change',paintRange);
    form.addEventListener('input',()=>{const error=form.querySelector('[data-budget-error]');if(error)error.textContent='';paintInstallments()});
    paintRange();
    form.onsubmit=async event=>{
      event.preventDefault();if(!canEdit)return;
      const values=new FormData(form), low=parseMoney(values.get('quickPrice')), high=parseMoney(values.get('quickPriceMax')), requestedRange=values.get('usePriceRange')==='on';
      const error=form.querySelector('[data-budget-error]');
      if(!String(values.get('vehicleReference')||'').trim()||!String(values.get('jobReference')||'').trim()){error.textContent='Completá el vehículo o referencia y el trabajo consultado.';return}
      if(low<=0){error.textContent='Ingresá un precio mayor que cero.';return}
      if(requestedRange&&(high<low||high<=0)){error.textContent='El precio máximo debe ser igual o mayor que el mínimo.';return}
      const old=[...db.presupuestos];
      const quote={...(editingQuote||{}),id:editingQuote?editingQuote.id:ctx.newId(),tipo:'Orientativo',fecha:dateToday(),clienteId:'',vehiculoId:'',trabajoId:'',
        vehiculoReferencia:String(values.get('vehicleReference')||'').trim(),trabajoOrientativo:String(values.get('jobReference')||'').trim(),
        estimacionMinima:String(low),estimacionMaxima:String(requestedRange?high:low),usarRangoPrecio:!!requestedRange,
        alcanceOrientativo:String(values.get('quickScope')||'').trim(),detalle:String(values.get('jobReference')||'').trim(),estado:editingQuote?.estado||'Borrador',
        operacionTiempoOrientativa:values.get('laborTimeId')||'',horasEstimadasMinimas:values.get('hoursEstimatedMin')||'',horasEstimadasHabituales:values.get('hoursEstimatedUsual')||'',
        horasEstimadasMaximas:values.get('hoursEstimatedMax')||'',tarifaHoraOrientativa:values.get('rateEstimated')||'',costoAdicionalMinimo:values.get('otherCostMin')||'',costoAdicionalMaximo:values.get('otherCostMax')||'',
        ofrecerCuotasQuick:values.get('offerInstallments')==='on',cantidadCuotasQuick:values.get('installmentCount')||'3',condicionesCuotasQuick:String(values.get('installmentTerms')||'').trim()};
      if(await persistQuote(quote,old,error,form)){editingQuote=null;draw('records')}
    };
  }
  function bindFormalForm() {
    const form=root.querySelector('#sme-budget-formal-form');if(!form)return;
    bindMoneyInputs(form);
    const client=form.elements.clienteId, vehicle=form.elements.vehiculoId, work=form.elements.trabajoId;
    const labor=form.elements.laborAmount, parts=form.elements.partsAmount, other=form.elements.otherAmount, total=form.elements.budgetTotal;
    const totalValue=()=>parseMoney(labor.value)+parseMoney(parts.value)+parseMoney(other.value);
    const paintTotal=()=>{total.value=moneyInput(totalValue());const error=form.querySelector('[data-budget-error]');if(error)error.textContent=''};
    [labor,parts,other].forEach(input=>input.addEventListener('input',paintTotal));
    const updateVehicles=(current='')=>{vehicle.innerHTML=options(db.vehiculos.filter(v=>!client.value||String(v.clienteId||'')===String(client.value)),vehicleLabel,current,'Seleccioná un vehículo')};
    client.addEventListener('change',()=>updateVehicles(''));
    work.addEventListener('change',()=>{
      const order=db.trabajos.find(item=>String(item.id)===String(work.value));
      if(order){client.value=order.clienteId||'';updateVehicles(order.vehiculoId||'')}
    });
    const paintInstallments=bindInstallments(form,totalValue);form.addEventListener('input',paintInstallments);paintTotal();
    form.onsubmit=async event=>{
      event.preventDefault();if(!canEdit)return;
      const values=new FormData(form), laborValue=parseMoney(values.get('laborAmount')), partsValue=parseMoney(values.get('partsAmount')), otherValue=parseMoney(values.get('otherAmount'));
      const error=form.querySelector('[data-budget-error]');
      if(!values.get('clienteId')||!values.get('vehiculoId')){error.textContent='Seleccioná un cliente y un vehículo para el presupuesto formal.';return}
      if(!String(values.get('detalle')||'').trim()){error.textContent='Describí el trabajo que se cotiza.';return}
      if([laborValue,partsValue,otherValue].some(n=>!Number.isFinite(n)||n<0)){error.textContent='Los importes no pueden ser negativos.';return}
      if(laborValue+partsValue+otherValue<=0){error.textContent='El total propuesto debe ser mayor que cero.';return}
      const old=[...db.presupuestos];
      const quote={...(editingQuote||{}),id:editingQuote?editingQuote.id:ctx.newId(),tipo:'Formal',fecha:values.get('fecha')||dateToday(),clienteId:String(values.get('clienteId')||''),vehiculoId:String(values.get('vehiculoId')||''),trabajoId:String(values.get('trabajoId')||''),
        detalle:String(values.get('detalle')||'').trim(),manoObra:String(laborValue),repuestos:String(partsValue),otrosConceptos:String(otherValue),importe:String(laborValue+partsValue+otherValue),
        estado:String(values.get('estado')||'Borrador'),diagnosticoCliente:String(values.get('diagnosticoCliente')||'').trim(),solucionRecomendada:String(values.get('solucionRecomendada')||'').trim(),
        alcanceTrabajo:String(values.get('alcanceTrabajo')||'').trim(),vigenciaDias:values.get('vigenciaDias')||'7',plazoEstimado:String(values.get('plazoEstimado')||'').trim(),
        condicionesPago:String(values.get('condicionesPago')||'').trim(),condicionesGarantia:String(values.get('condicionesGarantia')||'').trim(),detalleOtrosConceptos:String(values.get('detalleOtrosConceptos')||'').trim(),
        trabajosExcluidos:String(values.get('trabajosExcluidos')||'').trim(),controlPosterior:values.get('controlPosterior')||'no',condicionesControl:String(values.get('condicionesControl')||'').trim(),notaCliente:String(values.get('notaCliente')||'').trim(),
        operacionTiempoOrientativa:values.get('laborTimeId')||'',horasEstimadasMinimas:values.get('hoursEstimatedMin')||'',horasEstimadasHabituales:values.get('hoursEstimatedUsual')||'',horasEstimadasMaximas:values.get('hoursEstimatedMax')||'',
        tarifaHoraOrientativa:values.get('rateEstimated')||'',costoAdicionalMinimo:values.get('otherCostMin')||'',costoAdicionalMaximo:values.get('otherCostMax')||'',
        ofrecerCuotasFormal:values.get('offerInstallments')==='on',cantidadCuotasFormal:values.get('installmentCount')||'3',condicionesCuotasFormal:String(values.get('installmentTerms')||'').trim()};
      if(await persistQuote(quote,old,error,form)){editingQuote=null;draw('records')}
    };
  }
  async function persistQuote(quote,old,errorBox,form) {
    const submit=form.querySelector('button[type="submit"]'), label=submit?.textContent;
    if(submit){submit.disabled=true;submit.textContent='Guardando…'}
    try{
      if(editingQuote){const index=db.presupuestos.findIndex(item=>String(item.id)===String(editingQuote.id));if(index<0)throw new Error('El presupuesto que intentás editar ya no existe.');db.presupuestos[index]=quote}
      else db.presupuestos.push(quote);
      const ok=await ctx.save();
      if(!ok){db.presupuestos.splice(0,db.presupuestos.length,...old);if(errorBox)errorBox.textContent='No se confirmó el guardado. Los datos del formulario siguen disponibles; revisá el mensaje de almacenamiento e intentá nuevamente.';return false}
      try{localStorage.removeItem('sme_form_draft_v1:presupuestos:'+form.id)}catch(_){}
      return true;
    }catch(error){
      db.presupuestos.splice(0,db.presupuestos.length,...old);if(errorBox)errorBox.textContent='No se pudo guardar el registro: '+String(error?.message||error);console.error('Error guardando presupuesto:',error);return false;
    }finally{if(submit){submit.disabled=false;submit.textContent=label}}
  }
  function initializeLaborAssist(prefix) {
    const search=root.querySelector('#'+prefix+'-time-search'), results=root.querySelector('#'+prefix+'-time-results'), selectedBox=root.querySelector('#'+prefix+'-time-selected'), calcBox=root.querySelector('#'+prefix+'-time-calc');
    if(!search||!results||!selectedBox||!calcBox)return;
    let selected=null;
    if(pendingLaborId){selected=catalog.find(item=>String(item.id)===String(pendingLaborId))||null;if(selected)search.value=selected.title||''}
    const field=suffix=>root.querySelector('#'+prefix+'-'+suffix);
    const f={min:field('hours-min'),usual:field('hours'),max:field('hours-max'),rate:field('rate'),otherMin:field('other-min'),otherMax:field('other-max'),preview:field('time-preview'),apply:field('apply-time')};
    const wordsFor=value=>String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().split(/[^a-z0-9]+/).filter(w=>w.length>1&&!['de','del','la','el','con','para','por','un','una','y','al','en','cambio'].includes(w));
    const searchable=item=>[item.title,item.family,item.application,item.variants,item.vehicleGroup,item.keywords,item.sourceName].filter(Boolean).join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
    const paintCalc=()=>{
      const min=Number(f.min.value), usual=Number(f.usual.value), max=Number(f.max.value), rate=parseMoney(f.rate.value), lowExtra=parseMoney(f.otherMin.value), highExtra=parseMoney(f.otherMax.value);
      const valid=!!selected&&selected.suggested!==null&&Number.isFinite(min)&&Number.isFinite(usual)&&Number.isFinite(max)&&min>0&&usual>=min&&max>=usual&&rate>0&&lowExtra>=0&&highExtra>=lowExtra;
      if(!selected)f.preview.textContent='Elegí un trabajo para consultar las horas.';
      else if(selected.suggested===null)f.preview.textContent='Esta operación no tiene horas sugeridas confirmadas; no se calculará un precio automático.';
      else if(!valid)f.preview.textContent='Revisá el rango de horas, la tarifa y los otros costos.';
      else f.preview.textContent='Estimación: '+amount(min*rate+lowExtra)+' a '+amount(max*rate+highExtra)+' · punto habitual '+amount(usual*rate+(lowExtra+highExtra)/2)+'. Solo incluye los conceptos ingresados.';
      f.apply.disabled=!valid;
    };
    const selectItem=item=>{
      selected=item||null;selectedBox.hidden=!selected;calcBox.hidden=!(selected&&selected.suggested!==null);
      selectedBox.innerHTML=selected?'<h4>'+esc(selected.title)+'</h4><p>'+esc(selected.application||'')+'</p><p class="muted">'+esc(selected.scope||'')+'</p><p class="muted">Referencia: '+esc(selected.status||'Orientativa')+'. '+esc(selected.sourceNote||'')+'</p>':'';
      if(selected&&selected.suggested!==null){f.min.value=String(Number.isFinite(selected.min)?selected.min:selected.suggested);f.usual.value=String(selected.suggested);f.max.value=String(Number.isFinite(selected.max)?selected.max:selected.suggested)}
      else{f.min.value='';f.usual.value='';f.max.value=''}
      paintCalc();
    };
    const drawResults=()=>{
      const words=wordsFor(search.value);
      const matches=catalog.filter(item=>words.length?words.some(word=>searchable(item).includes(word)):item.suggested!==null)
        .sort((a,b)=>{const score=item=>words.reduce((sum,w)=>sum+(searchable(item).includes(w)?1:0),0);return score(b)-score(a)||String(a.title).localeCompare(String(b.title),'es')}).slice(0,8);
      results.innerHTML=matches.length?matches.map(item=>'<button type="button" class="sme-budget-v2-time-row" data-budget-time-select="'+esc(item.id)+'"><span><strong>'+esc(item.title)+'</strong><small>'+esc(item.family||'')+' · '+esc(item.application||'')+'</small></span><span>'+(item.suggested===null?'Sin horas':esc(String(item.min??item.suggested))+'–'+esc(String(item.max??item.suggested))+' h')+'</span></button>').join(''):'<div class="sme-budget-v2-empty">No encontré coincidencias. Probá con “distribución”, “8v”, “K4M”, “tapa” o “embrague”.</div>';
      results.querySelectorAll('[data-budget-time-select]').forEach(button=>button.addEventListener('click',()=>{selectItem(catalog.find(item=>String(item.id)===String(button.dataset.budgetTimeSelect))||null);drawResults()}));
    };
    search.addEventListener('input',()=>{if(selected&&!searchable(selected).includes(wordsFor(search.value).join(' ')))selected=null;drawResults();selectItem(selected)});
    [f.min,f.usual,f.max,f.rate,f.otherMin,f.otherMax].forEach(input=>input.addEventListener('input',paintCalc));
    f.apply.addEventListener('click',()=>{
      if(!selected||f.apply.disabled)return;
      const min=Number(f.min.value), usual=Number(f.usual.value), max=Number(f.max.value), rate=parseMoney(f.rate.value), low=min*rate+parseMoney(f.otherMin.value), high=max*rate+parseMoney(f.otherMax.value);
      const form=root.querySelector(prefix==='quick'?'#sme-budget-quick-form':'#sme-budget-formal-form');if(!form)return;
      form.elements.laborTimeId.value=selected.id;form.elements.hoursEstimatedMin.value=String(min);form.elements.hoursEstimatedUsual.value=String(usual);form.elements.hoursEstimatedMax.value=String(max);
      form.elements.rateEstimated.value=String(rate);form.elements.otherCostMin.value=String(parseMoney(f.otherMin.value));form.elements.otherCostMax.value=String(parseMoney(f.otherMax.value));
      if(prefix==='quick'){
        form.elements.quickPrice.value=moneyInput(low);form.elements.usePriceRange.checked=Math.abs(high-low)>.005;form.elements.quickPriceMax.value=moneyInput(high);
        form.elements.usePriceRange.dispatchEvent(new Event('change',{bubbles:true}));form.elements.quickPrice.dispatchEvent(new Event('input',{bubbles:true}));
        if(!String(form.elements.quickScope.value||'').trim()&&selected.scope)form.elements.quickScope.value=selected.scope;
      }else{
        form.elements.laborAmount.value=moneyInput(usual*rate);form.elements.laborAmount.dispatchEvent(new Event('input',{bubbles:true}));
        if(!String(form.elements.detalle.value||'').trim())form.elements.detalle.value=selected.title;
      }
      f.preview.textContent='Cálculo aplicado al formulario. Revisá el alcance y guardá el presupuesto manualmente.';
    });
    drawResults();if(selected)selectItem(selected);
  }
  function bindCostForm() {
    if(!canReadCosts)return;
    const selector=root.querySelector('#sme-budget-cost-quote'),form=root.querySelector('#smeInternalCostForm');if(!selector||!form)return;
    const summary=root.querySelector('#sme-budget-cost-summary'), names=['hours','hourlyCost','partsCost','externalCost','consumablesCost','shippingCost','overheadCost','paymentFeePct','paymentFeeFixed','taxRatePct','targetMarginPct'];
    const chosen=()=>formalQuotes().find(q=>String(q.id)===String(selector.value))||null;
    const setFromQuote=()=>{
      const q=chosen();selectedCostId=q?q.id:'';
      names.forEach(name=>{if(form.elements[name])form.elements[name].value=q?.analisisInterno?.[name]??(name==='targetMarginPct'?'25':(name==='hours'?(q?.horasEstimadasHabituales||'0'):'0'))});
      paintSummary();
    };
    const calc=()=>{
      const q=chosen(),v=Object.fromEntries(names.map(name=>[name,Number(String(form.elements[name]?.value||'0').replace(',','.'))||0]));
      const sale=q?parseMoney(q.importe):0, laborCost=v.hours*v.hourlyCost, base=laborCost+v.partsCost+v.externalCost+v.consumablesCost+v.shippingCost+v.overheadCost;
      const fee=sale*v.paymentFeePct/100+v.paymentFeeFixed, taxes=sale*v.taxRatePct/100, profit=sale-base-fee-taxes, margin=sale>0?profit/sale*100:0;
      const denominator=1-(v.targetMarginPct+v.paymentFeePct+v.taxRatePct)/100, suggested=denominator>0?(base+v.paymentFeeFixed)/denominator:NaN;
      return {q,v,sale,laborCost,base,fee,taxes,profit,margin,suggested};
    };
    function paintSummary(){
      const r=calc();if(!r.q){summary.innerHTML='<p class="muted">Elegí un presupuesto formal para revisar su rentabilidad.</p>';return}
      const valid=Number.isFinite(r.suggested)&&r.suggested>0;
      summary.innerHTML='<div class="sme-budget-v2-metrics"><div><small>Precio al cliente</small><strong>'+amount(r.sale)+'</strong></div><div><small>Costo previsto</small><strong>'+amount(r.base)+'</strong></div><div><small>Comisión estimada de cobro</small><strong>'+amount(r.fee)+'</strong></div><div><small>Impuestos estimados</small><strong>'+amount(r.taxes)+'</strong></div><div><small>Ganancia estimada</small><strong>'+amount(r.profit)+'</strong></div><div><small>Margen neto estimado</small><strong>'+money(r.margin)+' %</strong></div></div><p class="'+(r.profit<0?'sme-budget-v2-warning':'muted')+'">'+(r.profit<0?'Con estos supuestos, el precio no cubre los costos estimados.':'Revisá que los costos y porcentajes correspondan a este trabajo.')+'</p><p><strong>Precio orientativo para lograr el margen objetivo:</strong> '+(valid?amount(r.suggested):'No se puede calcular con esos porcentajes.')+'</p>'+(String(r.q.estado||'Borrador')!=='Borrador'?'<p class="muted">El precio sugerido solo puede aplicarse a un presupuesto en estado Borrador.</p>':'');
    }
    form.addEventListener('input',paintSummary);selector.addEventListener('change',setFromQuote);
    form.onsubmit=async event=>{
      event.preventDefault();if(!canEditCosts)return;
      const q=chosen();if(!q){summary.innerHTML='<p class="sme-budget-v2-warning">Seleccioná un presupuesto formal válido.</p>';return}
      const old=[...db.presupuestos];q.analisisInterno=Object.fromEntries(names.map(name=>[name,String(form.elements[name]?.value??'0')]));
      q.analisisInterno.updatedAt=new Date().toISOString();q.analisisInterno.updatedByUser=String(ctx.currentUser?.id||ctx.currentUser?.username||'');
      if(!(await ctx.save())){db.presupuestos.splice(0,db.presupuestos.length,...old);summary.insertAdjacentHTML('beforeend','<p class="sme-budget-v2-warning">No se confirmó el guardado del análisis. Revisá el mensaje de almacenamiento.</p>');return}
      paintSummary();summary.insertAdjacentHTML('beforeend','<p class="sme-budget-v2-success">Análisis interno guardado. No se incluyó en el documento para el cliente.</p>');
    };
    root.querySelector('#sme-budget-apply-price')?.addEventListener('click',async()=>{
      if(!canEditCosts)return;const r=calc();
      if(!r.q||String(r.q.estado||'Borrador')!=='Borrador'){summary.insertAdjacentHTML('beforeend','<p class="sme-budget-v2-warning">Solo se puede aplicar el precio sugerido a un presupuesto en estado Borrador.</p>');return}
      if(!Number.isFinite(r.suggested)||r.suggested<=0){summary.insertAdjacentHTML('beforeend','<p class="sme-budget-v2-warning">No se pudo obtener un precio sugerido válido.</p>');return}
      const old=[...db.presupuestos], previousPrice=parseMoney(r.q.importe), newPrice=Math.ceil(Math.max(previousPrice,r.suggested));
      r.q.importe=String(newPrice);r.q.analisisInterno=Object.assign({},r.q.analisisInterno||{},{lastAppliedAt:new Date().toISOString(),lastAppliedPrice:String(newPrice),analysisPriceBeforeApply:String(previousPrice)});
      if(!(await ctx.save())){db.presupuestos.splice(0,db.presupuestos.length,...old);summary.insertAdjacentHTML('beforeend','<p class="sme-budget-v2-warning">No se confirmó el cambio de precio; se restauraron los datos anteriores.</p>');return}
      paintSummary();summary.insertAdjacentHTML('beforeend','<p class="sme-budget-v2-success">Precio actualizado al mínimo sugerido, sin reducir un precio que ya era mayor. Revisá el presupuesto antes de compartirlo.</p>');
    });
    setFromQuote();
  }
  function bindHistory(){
    const search=root.querySelector('#sme-budget-history-search'),list=root.querySelector('#sme-budget-history-list');if(!list)return;
    const paint=()=>{
      const needle=String(search?.value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().trim();
      const quotes=filteredQuotes().filter(q=>!needle||[quoteTitle(q),customerName(q.clienteId),vehicleName(q.vehiculoId),workName(q.trabajoId),q.estado,q.detalle,q.trabajoOrientativo,q.vehiculoReferencia,q.importe,q.estimacionMinima,q.estimacionMaxima].join(' ').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().includes(needle));
      list.innerHTML=historyItemsMarkup(quotes);
      list.querySelectorAll('[data-budget-edit]').forEach(button=>button.addEventListener('click',()=>{
        const q=db.presupuestos.find(item=>String(item.id)===String(button.dataset.budgetEdit));if(!q||!canEdit)return;
        editingQuote=q;draw(q.tipo==='Orientativo'?'quick':'formal');
      }));
      list.querySelectorAll('[data-budget-delete]').forEach(button=>button.addEventListener('click',async()=>{
        const q=db.presupuestos.find(item=>String(item.id)===String(button.dataset.budgetDelete));if(!q||!canEdit)return;
        const accepted=await (ctx.confirm?ctx.confirm('Eliminar presupuesto','¿Eliminar este registro de prueba?'):Promise.resolve(window.confirm('¿Eliminar este presupuesto?')));
        if(!accepted)return;const old=[...db.presupuestos],index=db.presupuestos.findIndex(item=>String(item.id)===String(q.id));if(index<0)return;
        db.presupuestos.splice(index,1);if(!(await ctx.save())){db.presupuestos.splice(0,db.presupuestos.length,...old);return}draw(activeTab);
      }));
      list.querySelectorAll('[data-budget-print]').forEach(button=>button.addEventListener('click',async()=>{
        const q=db.presupuestos.find(item=>String(item.id)===String(button.dataset.budgetPrint));if(!q)return;
        try{await ctx.print(buildDocumentHtml(q),quoteTitle(q))}catch(error){console.error('Error al imprimir presupuesto:',error);window.alert('No se pudo abrir el documento para imprimir. '+String(error?.message||error))}
      }));
      list.querySelectorAll('[data-budget-share]').forEach(button=>button.addEventListener('click',async()=>{
        const q=db.presupuestos.find(item=>String(item.id)===String(button.dataset.budgetShare));if(!q)return;
        try{await ctx.share(quoteTitle(q),quoteText(q))}catch(error){console.error('Error al compartir presupuesto:',error);window.alert('No se pudo abrir el menú para compartir. '+String(error?.message||error))}
      }));
      list.querySelectorAll('[data-budget-related]').forEach(button=>button.addEventListener('click',()=>{
        if(button.dataset.budgetRelated==='clientes')ctx.openRelated?.('clientes',{clientId:button.dataset.budgetClient});
        if(button.dataset.budgetRelated==='vehiculos')ctx.openRelated?.('vehiculos',{vehicleId:button.dataset.budgetVehicle});
        if(button.dataset.budgetRelated==='trabajos')ctx.openRelated?.('trabajos',{workId:button.dataset.budgetWork});
      }));
    };
    search?.addEventListener('input',paint);paint();
  }
  draw(activeTab);
}
