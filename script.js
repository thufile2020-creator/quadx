/* QUADx four-member integrated hackathon demo. Emission factors remain illustrative. */
(() => {
  'use strict';
  const FACTORS = {
    electricity: { factor: 0.70, unit: 'kWh', label: 'Electricity', scope: 2, icon: 'ϟ' },
    diesel: { factor: 2.70, unit: 'L', label: 'Diesel', scope: 1, icon: '◈' },
    petrol: { factor: 2.31, unit: 'L', label: 'Petrol', scope: 1, icon: '◈' },
  }; // Illustrative kg CO2 / activity unit; replace with documented, period-specific factors in production.
  const DATA_KEY = 'quadx-records-v1';
  const COMPANY_KEY = 'quadx-company-v1';
  const $ = (id) => document.getElementById(id);
  const els = (selector) => document.querySelectorAll(selector);
  const format = (n, digits = 1) => Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: digits });
  const monthKey = (date) => String(date).slice(0, 7);
  const currentMonth = () => isoDay(new Date()).slice(0, 7); // Local calendar month.
  const safeGet = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
  const safeSet = (key, value) => { try { localStorage.setItem(key, value); } catch { toast('Browser storage unavailable. Changes may not persist.'); } };
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const dateForMonth = (offset) => { const today = new Date(); return new Date(today.getFullYear(), today.getMonth() + offset, 15, 12); };
  const isoDay = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;
  const displayMonth = (key) => new Date(`${key}-15T12:00:00`).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' });
  const displayDate = (date) => new Date(`${date}T12:00:00`).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  const generateDemo = () => {
    const result = [];
    const electricity = [690, 780, 730, 860, 810, 940];
    const diesel = [65, 78, 75, 82, 90, 74];
    for(let i = 0; i < 6; i++) {
      const date = isoDay(dateForMonth(i - 5));
      result.push({ id: `demo-e-${i}`, name: `Electricity bill · ${displayMonth(date.slice(0,7))}`, type: 'electricity', amount: electricity[i], date, demo: true });
      result.push({ id: `demo-d-${i}`, name: `Diesel record · ${displayMonth(date.slice(0,7))}`, type: 'diesel', amount: diesel[i], date, demo: true });
    }
    return result;
  };
  const loadRecords = () => {
    try { const saved = JSON.parse(safeGet(DATA_KEY)); if (Array.isArray(saved)) return saved.filter(validRecord); } catch {}
    return generateDemo();
  };
  const validRecord = (r) => r && FACTORS[r.type] && typeof r.name === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(r.date) && Number.isFinite(Number(r.amount)) && Number(r.amount) > 0;
  let records = loadRecords();
  let company = safeGet(COMPANY_KEY) || 'Northstar Components';
  let selectedFileName = '';
  let authToken = null;
  let businessId = null;
  // Logged-in records use the factor snapshot returned by the Flask database.
  // Browser demonstration records use the original illustrative frontend factors.
  const recordFactor = (r) => Number.isFinite(Number(r.factor)) ? Number(r.factor) : FACTORS[r.type].factor;
  const emission = (r) => Number(r.amount) * recordFactor(r);
  const sum = (collection) => collection.reduce((total, item) => total + emission(item), 0);
  const byType = (type, collection = records) => collection.filter(r => r.type === type);
  const forMonth = (key) => records.filter(r => monthKey(r.date) === key);
  let toastTimer;
  function toast(message) { const t = $('toast'); t.textContent = message; t.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => t.classList.remove('show'), 3000); }
  function navTo(view) {
    if (!['overview','documents','analytics','simulator','reports','settings'].includes(view)) view = 'overview';
    els('.page').forEach(page => page.classList.toggle('active', page.dataset.page === view));
    els('.nav-link').forEach(button => { const active = button.dataset.view === view; button.classList.toggle('active',active); if(active) button.setAttribute('aria-current','page'); else button.removeAttribute('aria-current'); });
    const labels = {overview:'Overview',documents:'Documents',analytics:'Carbon analytics',simulator:'Reduction simulator',reports:'Reports',settings:'Settings'};
    $('currentPageLabel').textContent = labels[view];
    history.replaceState(null,'',`#${view}`);
    $('sidebar').classList.remove('open'); $('mobileShade').classList.remove('show'); $('menuToggle').setAttribute('aria-expanded','false');
    window.scrollTo({ top: 0, behavior: 'instant' });
  }
  els('[data-view]').forEach(el => el.addEventListener('click', () => navTo(el.dataset.view)));
  els('[data-navigate]').forEach(el => el.addEventListener('click', () => navTo(el.dataset.navigate)));
  window.addEventListener('hashchange', () => navTo(location.hash.slice(1)));
  $('menuToggle').addEventListener('click', () => { const open = $('sidebar').classList.toggle('open'); $('mobileShade').classList.toggle('show',open); $('menuToggle').setAttribute('aria-expanded',String(open)); });
  $('mobileShade').addEventListener('click', () => { $('sidebar').classList.remove('open'); $('mobileShade').classList.remove('show'); $('menuToggle').setAttribute('aria-expanded','false'); });

  const rows = (data, deletable=false) => data.length ? data.map(r => {
    const t=FACTORS[r.type];
    const badge=t.scope===2?'':' fuel';
    return `<tr><td><div class="td-title"><span class="td-icon">${t.icon}</span>${escapeHtml(r.name)}${r.demo?' <small style="font-size:9px;color:#a1aba5">(demo)</small>':''}</div></td><td><span class="type-badge${badge}">${t.label}</span></td><td>${format(r.amount)} ${t.unit}</td><td>${displayDate(r.date)}</td><td><strong>${format(emission(r))} kg</strong></td>${deletable?`<td><button type="button" class="delete-button" data-delete="${escapeHtml(r.id)}" aria-label="Delete record">Delete</button></td>`:''}</tr>`;
  }).join('') : `<tr><td colspan="${deletable?6:5}" class="empty-state">No records yet. Add a bill or an activity record to begin.</td></tr>`;
  function renderChart() {
    const keys = Array.from({ length: 6 }, (_,i) => {const d = dateForMonth(i-5);return isoDay(d).slice(0,7);});
    const values = keys.map(k => sum(forMonth(k)));
    const svg = $('trendChart');
    const max = Math.max(...values, 1) * 1.2;
    const x = i => 14 + i * 118;
    const y = value => 208 - (value/max)*177;
    const points = values.map((v,i) => `${x(i)},${y(v)}`).join(' ');
    const area = `${x(0)},208 ${points} ${x(5)},208`;
    const grid = Array.from({length:4},(_,i) => {const ly=31+i*59;return `<line x1="0" y1="${ly}" x2="610" y2="${ly}" stroke="#ebf1eb" stroke-dasharray="4 5"/>`}).join('');
    const dots = values.map((v,i)=>`<circle cx="${x(i)}" cy="${y(v)}" r="5" fill="#2c8f69" stroke="white" stroke-width="3"><title>${displayMonth(keys[i])}: ${format(v)} kg CO₂</title></circle>`).join('');
    svg.innerHTML = `<defs><linearGradient id="chartFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#59af85" stop-opacity=".24"/><stop offset="100%" stop-color="#59af85" stop-opacity=".01"/></linearGradient></defs>${grid}<polygon points="${area}" fill="url(#chartFill)"/><polyline points="${points}" fill="none" stroke="#2c8f69" stroke-linecap="round" stroke-linejoin="round" stroke-width="3"/>${dots}`;
    $('chartMonths').innerHTML = keys.map(k=>`<span>${displayMonth(k).split(' ')[0]}</span>`).join('');
  }
  function renderOverview() {
    const curr=forMonth(currentMonth()); const electric=sum(byType('electricity',curr)); const fuel=sum(curr.filter(r=>r.type!=='electricity')); const total=electric+fuel;
    $('currentMonthLabel').textContent=displayMonth(currentMonth());
    $('statTotal').textContent=format(total); $('statElectricity').textContent=format(electric); $('statFuel').textContent=format(fuel); $('statDocs').textContent=String(records.length);
    $('electricityUsage').textContent=`${format(byType('electricity',curr).reduce((s,r)=>s+Number(r.amount),0))} kWh recorded`;
    $('fuelUsage').textContent=`${format(curr.filter(r=>r.type!=='electricity').reduce((s,r)=>s+Number(r.amount),0))} litres of owned fuel`;
    $('donutTotal').textContent=format(total,0); $('sourceElectricity').textContent=`${format(electric)} kg`; $('sourceFuel').textContent=`${format(fuel)} kg`;
    const pct=total?100*electric/total:50;
    $('sourceDonut').style.background=`conic-gradient(#459f78 0 ${pct}%, #cdb16c ${pct}% 100%)`;
    $('recentRows').innerHTML=rows([...records].sort((a,b)=>b.date.localeCompare(a.date)).slice(0,5));
    renderChart();
  }
  function renderDocuments() {
    const sorted=[...records].sort((a,b)=>b.date.localeCompare(a.date));
    $('recordCount').textContent=String(records.length);
    $('allRecordsRows').innerHTML=rows(sorted,true);
    els('[data-delete]').forEach(btn => btn.addEventListener('click', async () => {
      const target=records.find(r=>String(r.id)===btn.dataset.delete);
      if(!target || !confirm(`Delete “${target.name}”?`)) return;
      try {
        if(authToken) {
          await api(`/api/businesses/${businessId}/activities/${target.id}`, {method:'DELETE'});
          await reloadDatabaseRecords();
        } else {
          records=records.filter(r=>r.id!==target.id); persist();
        }
        toast('Record deleted');
      } catch(error){ toast(`Delete failed: ${error.message}`); }
    }));
  }
  function renderAnalytics() {
    const electric=sum(byType('electricity')); const fuel=sum(records.filter(r=>r.type!=='electricity')); const total=electric+fuel;
    $('analyticsTotal').textContent=format(total); $('scope1Value').textContent=`${format(fuel)} kg`;$('scope2Value').textContent=`${format(electric)} kg`;
    $('scope1Bar').style.width=`${total?100*fuel/total:0}%`; $('scope2Bar').style.width=`${total?100*electric/total:0}%`;
    const keys=[...new Set(records.map(r=>monthKey(r.date)))].sort().reverse();
    $('monthlyRows').innerHTML=keys.length?keys.map(k=> {const month=forMonth(k);const e=sum(byType('electricity',month));const f=sum(month.filter(r=>r.type!=='electricity'));return `<tr><td><strong>${displayMonth(k)}</strong></td><td>${format(e)} kg</td><td>${format(f)} kg</td><td><strong>${format(e+f)} kg</strong></td></tr>`;}).join(''):'<tr><td colspan="4" class="empty-state">No monthly data yet.</td></tr>';
  }
  function renderSimulator() {
    const pct=Number($('savingSlider').value);
    const curr=byType('electricity',forMonth(currentMonth()));
    const kwh=curr.reduce((s,r)=>s+Number(r.amount),0);
    const before=kwh*FACTORS.electricity.factor; const after=before*(1-pct/100);
    $('sliderPct').textContent=`${pct}%`; $('simKwh').textContent=`${format(kwh)} kWh`; $('simNewKwh').textContent=`${format(kwh*(1-pct/100))} kWh`; $('simSavings').textContent=format(before-after);
    $('simBefore').textContent=`${format(before)} kg`; $('simAfter').textContent=`${format(after)} kg`; $('simAfterBar').style.width=`${100-pct}%`;
  }
  $('savingSlider').addEventListener('input',renderSimulator);
  function renderReport() {
    const electric=sum(byType('electricity')); const fuel=sum(records.filter(r=>r.type!=='electricity')); const total=electric+fuel;
    $('reportCompany').textContent=company; $('reportPeriod').textContent=`All recorded periods · Generated ${new Date().toLocaleDateString('en-IN',{day:'numeric',month:'long',year:'numeric'})}`;
    $('reportTotal').textContent=format(total); $('reportScope1').textContent=format(fuel); $('reportScope2').textContent=format(electric);
    const printRows=[...records].sort((a,b)=>b.date.localeCompare(a.date)).map(r=>`<tr><td>${escapeHtml(r.name)}</td><td>${escapeHtml(FACTORS[r.type].label)}</td><td>${format(r.amount)} ${FACTORS[r.type].unit}</td><td>${escapeHtml(r.date)}</td><td>${format(emission(r))}</td></tr>`).join('');
    $('printableReport').innerHTML=`<h1>QUADx · Preliminary CO₂ Emissions Summary</h1><p class="print-meta"><strong>Company:</strong> ${escapeHtml(company)}<br><strong>Generated:</strong> ${new Date().toLocaleDateString('en-IN')}<br><strong>Reporting coverage:</strong> All saved record dates<br><strong>Status:</strong> Illustrative demo, unverified</p><div class="print-summary"><strong>Total estimated emissions:</strong> ${format(total)} kg CO₂<br><strong>Scope 1 (owned fuel):</strong> ${format(fuel)} kg CO₂<br><strong>Scope 2 (electricity):</strong> ${format(electric)} kg CO₂</div><h2>Activity records</h2><div class="print-table"><table><thead><tr><th>Record</th><th>Type</th><th>Consumption</th><th>Date</th><th>kg CO₂</th></tr></thead><tbody>${printRows||'<tr><td colspan="5">No records</td></tr>'}</tbody></table></div><h2>Methodology and limitations</h2><p>Activity × illustrative factor: purchased electricity, diesel and petrol activity multiplied by per-record demonstration emission factors. Factors are unverified and may differ between records. Scope 3, non-CO₂ gases, source-document retention, and independent verification are excluded. Some entries may be seeded demo records. Do not use for regulatory or supplier disclosure.</p><p class="print-disclaimer">QUADx frontend prototype · This document is not a certified carbon footprint report.</p>`;
  }
  function renderCompany() { $('sidebarCompany').textContent=company; $('companyInput').value=company; }
  function renderAll() { renderOverview();renderDocuments();renderAnalytics();renderSimulator();renderReport();renderCompany(); }
  function persist(){if(!authToken)safeSet(DATA_KEY,JSON.stringify(records));renderAll();}
  function showRecordForm(fileName='') {
    selectedFileName=fileName;
    $('recordForm').classList.remove('hidden');
    $('recordDate').value=isoDay(new Date());
    $('recordName').value=fileName || '';
    $('recordAmount').value=''; $('recordType').value='electricity'; updateRecordEstimate();
    $('recordForm').scrollIntoView({behavior:'smooth',block:'center'});
  }
  function hideRecordForm(){ $('recordForm').classList.add('hidden'); $('fileInput').value=''; selectedFileName=''; }
  async function acceptFile(file) {
    if(!file)return;
    const valid= /\.(txt|pdf|png|jpe?g|webp)$/i.test(file.name) &&
      (file.type==='' || ['text/plain','application/pdf','image/png','image/jpeg','image/webp'].includes(file.type));
    if(!valid){toast('Choose a TXT, PDF, JPG, PNG or WEBP bill.');return;}
    if(file.size>11*1024*1024){toast('Choose a file smaller than 11 MB.');return;}
    showRecordForm(file.name);
    $('ocrStatus').textContent='Scanning bill using Member 3 Python engine...';
    try {
      const form=new FormData(); form.append('bill',file);
      const result=await api('/api/ai/scan',{method:'POST',body:form});
      const extracted=result.extracted || {};
      const elec=Number(extracted.electricity_kwh);
      const diesel=Number(extracted.diesel_litres);
      if(extracted.electricity_kwh !== null && Number.isFinite(elec) && elec>0){
        $('recordType').value='electricity'; $('recordAmount').value=elec;
      } else if(extracted.diesel_litres !== null && Number.isFinite(diesel) && diesel>0){
        $('recordType').value='diesel'; $('recordAmount').value=diesel;
      }
      if(result.billing_period && /^\d{4}-\d{2}$/.test(result.billing_period)) {
        $('recordDate').value=result.billing_period+'-01';
      }
      updateRecordEstimate();
      $('ocrStatus').textContent='OCR scan finished. Check the extracted numbers against the original bill before clicking Save.';
      toast('Review the extracted consumption before saving.');
    } catch(error) {
      $('ocrStatus').textContent='Scanner unavailable: '+error.message+' — enter values manually.';
      toast('Manual entry is still available.');
    }
  }
  $('uploadZone').addEventListener('click',()=> $('fileInput').click());
  $('uploadZone').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();$('fileInput').click();}});
  $('fileInput').addEventListener('change',e=>acceptFile(e.target.files[0]));
  for(const event of ['dragenter','dragover']) $('uploadZone').addEventListener(event,e=>{e.preventDefault();$('uploadZone').classList.add('drag-over');});
  for(const event of ['dragleave','drop']) $('uploadZone').addEventListener(event,e=>{e.preventDefault();$('uploadZone').classList.remove('drag-over');if(event==='drop')acceptFile(e.dataTransfer.files[0]);});
  $('manualEntryBtn').addEventListener('click',()=>showRecordForm());
  $('closeRecordForm').addEventListener('click',hideRecordForm);
  $('cancelRecord').addEventListener('click',hideRecordForm);
  function updateRecordEstimate(){ const t=FACTORS[$('recordType').value];const a=Math.max(0,Number($('recordAmount').value)||0);$('unitLabel').textContent=`(${t.unit})`;$('recordEstimate').textContent=`${format(a*t.factor)} kg CO₂`;$('factorDescription').textContent=`${t.factor.toFixed(2)} kg CO₂ / ${t.unit} (demo only)`;}
  $('recordType').addEventListener('change',updateRecordEstimate);
  $('recordAmount').addEventListener('input',updateRecordEstimate);
  $('recordForm').addEventListener('submit',async e=>{
    e.preventDefault(); const amount=Number($('recordAmount').value);const date=$('recordDate').value;const name=$('recordName').value.trim();const type=$('recordType').value;
    if(!Number.isFinite(amount)||amount<=0||amount>1e9||!date||!name||!FACTORS[type]) {toast('Enter a valid name, date, type, and positive consumption amount.');return;}
    try {
      if(authToken) {
        await api(`/api/businesses/${businessId}/activities`,{method:'POST',body:{
          activity_type:type,quantity:amount,period:date.slice(0,7),
          note:JSON.stringify({name,date,sourceName:selectedFileName}).slice(0,250)
        }});
        await reloadDatabaseRecords();
      } else {
        records.push({id:`entry-${Date.now()}-${Math.random().toString(36).slice(2,8)}`,name,type,date,amount,demo:false,sourceName:selectedFileName});
        persist();
      }
      hideRecordForm();toast(authToken?'Activity saved to Flask database.':'Activity saved to browser demo.');
    } catch(error) {toast('Could not save activity: '+error.message);}
  });
  $('downloadCsv').addEventListener('click',()=>{
    const headers=['Record','Type','Amount','Unit','Date','Factor kg CO2/unit','Emissions kg CO2','Demo'];
    const data=records.map(r=>[r.name,r.type,r.amount,FACTORS[r.type].unit,r.date,recordFactor(r),emission(r).toFixed(3),r.demo?'yes':'no']);
    const csv=[headers,...data].map(row=>row.map(v=>{const raw=String(v);const safe=/^[=+@\-]/.test(raw)?`'${raw}`:raw;return `"${safe.replace(/"/g,'""')}"`;}).join(',')).join('\r\n');
    const blob=new Blob([csv],{type:'text/csv;charset=utf-8'});const link=document.createElement('a');link.href=URL.createObjectURL(blob);link.download='QUADx-emissions-demo.csv';document.body.appendChild(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
    toast('Demo CSV exported');
  });
  $('printReportBtn').addEventListener('click',()=> {renderReport();window.print();});
  $('settingsForm').addEventListener('submit',async e=>{
    e.preventDefault(); const name=$('companyInput').value.trim();
    if(!name){toast('Enter a business name.');return;}
    try {
      if(authToken) await api(`/api/businesses/${businessId}`,{method:'PATCH',body:{name}});
      else safeSet(COMPANY_KEY,name);
      company=name;renderAll();toast('Company name saved');
    } catch(error){toast(error.message);}
  });
  $('resetDemo').addEventListener('click',()=>{
    if(authToken){toast('Sign out first. This button only resets local demo records.');return;}
    if(!confirm('Reset local sample records and company name?'))return;
    records=generateDemo();company='Northstar Components';safeSet(COMPANY_KEY,company);
    persist();toast('Browser demo data restored');
  });
  // === Connected Member 2 Flask backend + Member 3 AI + Member 4 PDF ===
  async function api(path,{method='GET',body}={}) {
    const headers={};
    if(authToken) headers.Authorization=`Bearer ${authToken}`;
    if(body !== undefined && !(body instanceof FormData)) headers['Content-Type']='application/json';
    const response=await fetch(path,{method,headers,
      body:body instanceof FormData?body:(body===undefined?undefined:JSON.stringify(body))});
    const payload=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(payload.error||`API ${response.status}`);
    return payload;
  }
  function statusUpdate() {
    $('accountButton').textContent=authToken?'Sign out (DB connected)':'Connect backend';
    $('recordsStorageLabel').textContent=authToken?
      'Database records (SQLite) — changes are saved by your Flask backend.':
      'Browser demo records — click Connect backend to register/sign in and save to SQLite.';
  }
  async function reloadDatabaseRecords() {
    const result=await api(`/api/businesses/${businessId}/activities`);
    records=result.records.filter(r=>FACTORS[r.activity_type]).map(r=>{
      let details={};
      try{details=JSON.parse(r.note||'{}');if(!details||typeof details!=='object')details={};}catch{}
      return {id:String(r.id),name:details.name||`${r.activity_type} record`,
        type:r.activity_type,amount:r.quantity,date:details.date||`${r.period}-01`,
        factor:r.factor_kg_co2e_per_unit, factorSource:r.factor_source,
        demo:!!r.factor_is_demo,sourceName:details.sourceName||''};
    }).filter(validRecord);
    renderAll();
  }
  async function connectAccount(data,register){
    const result=await api(register?'/api/auth/register':'/api/auth/login',
      {method:'POST',body:data});
    const token=result.access_token;
    authToken=token;
    try {
      let businesses=await api('/api/businesses');
      let business=businesses.businesses[0];
      if(!business){
        const created=await api('/api/businesses',{method:'POST',body:{
          name:company,industry:'Manufacturing',city:'Chennai'
        }});
        business=created.business;
      }
      businessId=business.id;company=business.name;
      await reloadDatabaseRecords();
      statusUpdate();
      $('accountDialog').close();
      $('authPassword').value='';
      toast('Connected. Activity records now save to the Flask database.');
    } catch(error){ authToken=null;businessId=null;statusUpdate();throw error; }
  }
  $('accountButton').addEventListener('click',()=>{
    if(authToken){
      if(!confirm('Sign out and return to local demo records?'))return;
      authToken=null;businessId=null;records=loadRecords();company=safeGet(COMPANY_KEY)||'Northstar Components';
      renderAll();statusUpdate();toast('Signed out. Browser demo restored.');
    }else $('accountDialog').showModal();
  });
  $('authClose').addEventListener('click',()=>$('accountDialog').close());
  $('registerMode').addEventListener('change',()=>{
    const register=$('registerMode').checked;
    $('authNameRow').classList.toggle('hidden',!register);
    $('authName').required=register;
    $('authSubmit').textContent=register?'Create account':'Sign in';
    $('authPassword').autocomplete=register?'new-password':'current-password';
  });
  $('accountForm').addEventListener('submit',async event=>{
    event.preventDefault();
    const register=$('registerMode').checked;
    const data={email:$('authEmail').value.trim(),password:$('authPassword').value};
    if(register)data.name=$('authName').value.trim();
    $('authSubmit').disabled=true;
    try{await connectAccount(data,register);}
    catch(error){toast('Account error: '+error.message);}
    finally{$('authSubmit').disabled=false;}
  });
  $('runDetective').addEventListener('click',async()=>{
    try {
      const recordsInput=JSON.parse($('detectiveInput').value);
      const result=await api('/api/ai/detect',{method:'POST',body:{records:recordsInput}});
      $('aiResults').textContent=JSON.stringify(result,null,2);
    }catch(error){$('aiResults').textContent='Error: '+error.message;}
  });
  $('getRecommendations').addEventListener('click',async()=>{
    try{
      const curr=forMonth(currentMonth());
      const electricity=byType('electricity',curr).reduce((n,r)=>n+Number(r.amount),0);
      const diesel=byType('diesel',curr).reduce((n,r)=>n+Number(r.amount),0);
      const result=await api('/api/ai/recommend',{method:'POST',body:{
        activity:{electricity_kwh:electricity,diesel_litres:diesel}
      }});
      $('aiResults').textContent=JSON.stringify({
        total_kg_co2e:result.emissions.total_kg_co2e,
        warning:result.emissions.reporting_warning,
        note:'Suggestions cover electricity and diesel only (petrol excluded from this AI module).',
        suggestions:result.suggestions
      },null,2);
    }catch(error){$('aiResults').textContent='Error: '+error.message;}
  });
  function demoPassportPayload() {
    if(!records.length)throw new Error('Add at least one activity record first.');
    const dates=records.map(r=>r.date).sort();
    return {
      report_id:`DEMO-${Date.now()}`,
      business:{name:company,industry:'Manufacturing demo',location:'Chennai',supplier_id:'QUADX-DEMO'},
      period:{start:dates[0],end:dates[dates.length-1]},
      activities:records.map((r,i)=>({
        id:`ROW-${i+1}`,source:r.type==='electricity'?'Purchased grid electricity':
          `Company-owned ${r.type}`,
        scope:r.type==='electricity'?'Scope 2':'Scope 1',
        quantity:Number(r.amount),unit:FACTORS[r.type].unit,
        emission_factor:FACTORS[r.type].factor,
        factor_unit:`kg CO2e/${FACTORS[r.type].unit}`,
        factor_source:'DEMO ONLY - illustrative factor',
        factor_year:new Date().getFullYear(),
        evidence_file:r.sourceName||''
      })),
      quality_notes:['Browser data is not verified; uploaded source files are not retained.',
        'Emission factors are illustrative placeholders, not valid for official reporting.']
    };
  }
  $('downloadPassportButton').addEventListener('click',async()=>{
    const button=$('downloadPassportButton');button.disabled=true;
    try{
      const url=authToken?`/api/reports/businesses/${businessId}/pdf`:'/api/reports/pdf';
      const headers={};let body;
      if(authToken){headers.Authorization=`Bearer ${authToken}`;}
      else{headers['Content-Type']='application/json';body=JSON.stringify(demoPassportPayload());}
      const response=await fetch(url,{method:authToken?'GET':'POST',headers,body});
      if(!response.ok){const error=await response.json().catch(()=>({}));throw new Error(error.error||'PDF generation failed');}
      const blob=await response.blob();
      const href=URL.createObjectURL(blob);
      const link=document.createElement('a');link.href=href;link.download='QUADx_Carbon_Passport_DEMO.pdf';
      document.body.appendChild(link);link.click();link.remove();
      setTimeout(()=>URL.revokeObjectURL(href),5000);
      toast('Member 4 passport PDF generated.');
    }catch(error){toast('Report error: '+error.message);}
    finally{button.disabled=false;}
  });
  statusUpdate();
  // If backend is unavailable the original local dashboard still works.
  api('/api/health').catch(()=>toast('Flask backend unavailable. Run python app.py.'));

  renderAll();navTo(location.hash.slice(1)||'overview');
})();
