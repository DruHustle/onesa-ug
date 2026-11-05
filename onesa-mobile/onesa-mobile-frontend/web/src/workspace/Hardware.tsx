import { useState } from 'react';
import type { Field } from './components';
import { Details, Empty, Info, matches, MutationButton, options, Panel, Pill, RecordForm, RecordMeta, Search, DateText } from './components';
import type { Item, StaffData, WorkspaceContext } from './types';
import { humanize } from './helpers.mjs';

const assetTypes = ['android_phone', 'iphone', 'router', 'switch', 'ups', 'satellite_terminal', 'test_sim', 'workstation', 'other'];
const checkKeys = ['asset_label', 'power', 'firmware', 'management_security', 'equipment_approval', 'connectivity', 'recovery'];
const pathOptions = [{value:'terrestrial',label:'Terrestrial mobile'}, {value:'direct_to_cell',label:'Handset direct to cell'}, {value:'dish_wifi',label:'Dish and Wi-Fi'}];
const optional = (value: string | undefined) => value?.trim() ? value.trim() : undefined;
function siteOptions(sites: Item[]) { return sites.map(site => ({ value: site.id, label: String(site.name) })); }

export function Hardware({ data, context }: { data: StaffData; context: WorkspaceContext }) {
  const [search, setSearch] = useState('');
  const writable = data.permissions.includes('hardware.write');
  const visible = data.assets.filter(asset => matches(asset, search, ['tag', 'manufacturer', 'model', 'assetType', 'state']));
  return <div className="mw-stack">
    <Info>Inventory records describe your equipment. Commissioning is evidence of completed checks; network status stays unobserved until an authenticated measurement is available.</Info>
    <div className="mw-columns">
      <Panel title="Pilot sites" hint={`${data.sites.length} shown`}>
        {data.sites.length ? <ul className="mw-plain-list">{data.sites.map(site => <li key={site.id}><div><strong>{String(site.name)}</strong><small>{String(site.area)} · {humanize(site.purpose)}</small></div><Pill value={site.state}/></li>)}</ul> : <Empty>Add your device bench or field-trial location to begin.</Empty>}
        {writable && <Details label="Add a site"><RecordForm title="Add a site" busy={context.pending} submitLabel="Save site" fields={[
          {name:'name',label:'Site name',maxLength:80}, {name:'area',label:'Area or district',maxLength:100},
          {name:'purpose',label:'Purpose',type:'select',options:options(['device_bench','wifi_backhaul','field_trial']),wide:true},
        ]} onSubmit={v => context.mutate('/v1/ops/sites',{name:v.name,area:v.area,purpose:v.purpose},'POST','Site saved. Add its equipment next.')}/></Details>}
      </Panel>
      <Panel title="Add equipment" hint="Plan before procurement">
        {writable && data.sites.length > 0 ? <Details label="Register a planned asset"><RecordForm title="Register a planned asset" busy={context.pending} submitLabel="Save planned asset" fields={[
          {name:'siteId',label:'Site',type:'select',options:siteOptions(data.sites)},
          {name:'tag',label:'Asset tag',pattern:'[A-Z0-9][A-Z0-9_\\-]{2,31}',maxLength:32,hint:'Your internal label, for example OM-PHONE-01.'},
          {name:'assetType',label:'Equipment type',type:'select',options:options(assetTypes)},
          {name:'manufacturer',label:'Manufacturer',maxLength:60}, {name:'model',label:'Model',maxLength:100},
          {name:'firmware',label:'Firmware / software',required:false,maxLength:80},
          {name:'powerWatts',label:'Rated power (W)',type:'number',min:0,max:10000,step:'0.1',required:false},
          {name:'custodian',label:'Custodian / responsible team',required:false,maxLength:80},
          {name:'serialReference',label:'Internal serial record reference',required:false,maxLength:160,hint:'Reference your controlled inventory. No SIM keys or handset identifiers are needed here.'},
          {name:'supplierReference',label:'Supplier / procurement reference',required:false,maxLength:160},
          {name:'typeApprovalRef',label:'Equipment approval reference',required:false,maxLength:160,hint:'A non-secret reference, without credentials or subscriber identifiers.'},
        ]} onSubmit={v => context.mutate('/v1/ops/assets',{siteId:v.siteId,tag:v.tag,assetType:v.assetType,manufacturer:v.manufacturer,model:v.model,...(optional(v.firmware)?{firmware:v.firmware}:{}),...(v.powerWatts?{powerWatts:Number(v.powerWatts)}:{}),...(optional(v.custodian)?{custodian:v.custodian}:{}),...(optional(v.serialReference)?{serialReference:v.serialReference}:{}),...(optional(v.supplierReference)?{supplierReference:v.supplierReference}:{}),...(optional(v.typeApprovalRef)?{typeApprovalRef:v.typeApprovalRef}:{})},'POST','Planned asset saved. Record receipt when it arrives.')}/></Details>
          : <Empty>{writable ? 'Create a site first. No equipment has been purchased by adding a record.' : 'Your role can review inventory. Operations staff can add and commission equipment.'}</Empty>}
        <p className="mw-secondary">Use internal asset labels. Do not enter SIM authentication keys, passwords, national ID numbers or customer phone numbers.</p>
      </Panel>
    </div>
    <Panel title="Equipment inventory" hint={`${visible.length} of ${data.assets.length} shown`}>
      <Search label="Find equipment by tag, model or state" value={search} setValue={setSearch}/>
      {visible.length ? <div className="mw-record-list">{visible.map(asset => <Asset key={asset.id} asset={asset} siteName={String(data.sites.find(s=>s.id===asset.siteId)?.name??'Site record unavailable')} writable={writable} context={context}/>)}</div> : <Empty>{search ? 'No equipment matches this search.' : 'No equipment records yet. Start with a planned asset.'}</Empty>}
    </Panel>
  </div>;
}
function Asset({ asset, siteName, writable, context }: { asset: Item; siteName: string; writable: boolean; context: WorkspaceContext }) {
  const checks = (asset.checks ?? {}) as Record<string, {result:string;evidenceRef?:string;checkedAt?:string;checkedBy?:string;note?:string}>;
  const complete = Object.values(checks).filter(check => ['pass','not_applicable'].includes(check.result)).length;
  return <article className="mw-record">
    <div className="mw-record-line"><div><h3>{String(asset.tag)} <span>{String(asset.manufacturer)} {String(asset.model)}</span></h3><p>{siteName} · {humanize(asset.assetType)} · {complete}/{checkKeys.length} checks complete</p></div><Pill value={asset.state}/></div>
    <div className="mw-inline-facts"><span>Network: <strong>Unobserved</strong></span><span>Firmware: {String(asset.firmware)}</span><span>Rated power: {Number(asset.powerWatts)} W</span></div>
    <Details label={`View ${String(asset.tag)} checks and actions`}>
      <RecordMeta item={asset}/>
      <dl className="mw-definition-list"><div><dt>Custodian</dt><dd>{String(asset.custodian??'Not recorded')}</dd></div><div><dt>Serial record reference</dt><dd className="mw-reference">{String(asset.serialReference??'Not recorded')}</dd></div><div><dt>Supplier / procurement reference</dt><dd className="mw-reference">{String(asset.supplierReference??'Not recorded')}</dd></div></dl>
      <dl className="mw-check-grid">{checkKeys.map(key => <div key={key}><dt>{humanize(key)}</dt><dd><Pill value={checks[key]?.result??'not_run'}/>{checks[key]?.evidenceRef && <small>{checks[key].evidenceRef} · <DateText value={checks[key].checkedAt}/></small>}{checks[key]?.note&&<small className="mw-observation">{checks[key].note}</small>}{checks[key]?.checkedBy&&<small>Checked by <span className="mw-reference">{checks[key].checkedBy}</span></small>}</dd></div>)}</dl>
      <MutationButton context={context} action={()=>context.download(`/v1/ops/records/assets/${asset.id}`,`onesa-mobile-asset-${String(asset.tag)}.json`)}>Download asset record and check history</MutationButton>
      {writable && asset.state !== 'retired' && <div className="mw-stack">
        {asset.state === 'planned' && <MutationButton context={context} action={() => context.mutate(`/v1/ops/assets/${asset.id}`,{revision:asset.revision,state:'received'},'PATCH','Asset receipt recorded. Complete the commissioning checks next.')}>Record asset received</MutationButton>}
        {asset.state !== 'planned' && <Details label={`Record a commissioning check for ${String(asset.tag)}`}><RecordForm title={`Commission ${String(asset.tag)}`} busy={context.pending} submitLabel="Save check evidence" fields={[
          {name:'check',label:'Commissioning check',type:'select',options:options(checkKeys)},
          {name:'result',label:'Observed result',type:'select',options:options(['pass','fail','not_applicable'])},
          {name:'evidenceRef',label:'Evidence reference',maxLength:160,wide:true},
          {name:'note',label:'Observation / reason',type:'textarea',required:false},
        ]} onSubmit={v => context.mutate(`/v1/ops/assets/${asset.id}/checks`,{revision:asset.revision,check:v.check,result:v.result,evidenceRef:v.evidenceRef,...(optional(v.note)?{note:v.note}:{})},'POST','Commissioning check saved. Network connectivity remains a separate observation.')}><p className="mw-secondary">Asset label, power, management security and equipment approval require a passing check. The other checks may be marked not applicable with supporting evidence.</p></RecordForm></Details>}
        <Details label={`Update ${String(asset.tag)} inventory`}><RecordForm title={`Update ${String(asset.tag)} inventory`} busy={context.pending} reset={false} submitLabel="Save inventory update" fields={[
          {name:'state',label:'Inventory state',type:'select',options:options(asset.state==='planned'?['planned','received','faulty','retired']:['received','faulty','retired']),required:false,hint:'Leave unchanged when updating metadata only.'},
          {name:'custodian',label:'Custodian / responsible team',required:false,maxLength:80,value:String(asset.custodian??'')},
          {name:'serialReference',label:'Internal serial record reference',required:false,maxLength:160,value:String(asset.serialReference??'')},
          {name:'supplierReference',label:'Supplier / procurement reference',required:false,maxLength:160,value:String(asset.supplierReference??'')},
          {name:'firmware',label:'Firmware / software',required:false,maxLength:80,value:String(asset.firmware)},
          {name:'typeApprovalRef',label:'Equipment approval reference',required:false,maxLength:160,value:String(asset.typeApprovalRef??''),wide:true},
        ]} onSubmit={v => {
          if(!v.state&&![v.firmware,v.typeApprovalRef,v.custodian,v.serialReference,v.supplierReference].some(value=>value.trim()))throw new Error('Enter a change to save.');
          return context.mutate(`/v1/ops/assets/${asset.id}`,{revision:asset.revision,...(v.state?{state:v.state}:{}),...(optional(v.firmware)?{firmware:v.firmware}:{}),...(optional(v.typeApprovalRef)?{typeApprovalRef:v.typeApprovalRef}:{}),...(optional(v.custodian)?{custodian:v.custodian}:{}),...(optional(v.serialReference)?{serialReference:v.serialReference}:{}),...(optional(v.supplierReference)?{supplierReference:v.supplierReference}:{})},'PATCH','Inventory update saved.');
        }}><p className="mw-secondary">A serial reference, firmware or approval change resets the affected commissioning checks. Review and repeat them before recording a passing trial. Leaving an optional field blank keeps its current value.</p></RecordForm></Details>
      </div>}
    </Details>
  </article>;
}

export function Trials({ data, context }: { data: StaffData; context: WorkspaceContext }) {
  const [search,setSearch]=useState(''), writable=data.permissions.includes('hardware.write');
  const visible=data.trials.filter(item=>matches(item,search,['scenario','operator','path','service','result']));
  return <div className="mw-stack"><Info>Record an authorized test that you performed or a labelled lab simulation. Saving a trial never configures a radio, connects a SIM, or enables satellite service.</Info>
    <Panel title="Field-trial plan" hint="Evidence before claims">
      {writable && data.sites.length > 0 && data.assets.length > 0 ? <Details label="Plan a field trial"><RecordForm title="Plan a field trial" busy={context.pending} submitLabel="Save trial plan" fields={[
        {name:'siteId',label:'Site',type:'select',options:siteOptions(data.sites)},
        {name:'assetId',label:'Test asset',type:'select',options:data.assets.filter(a=>a.state!=='retired').map(a=>({value:a.id,label:`${String(a.tag)} · ${String(data.sites.find(s=>s.id===a.siteId)?.name??'Unknown site')}`})),hint:'Choose an asset belonging to the selected site.'},
        {name:'path',label:'Connectivity path',type:'select',options:pathOptions},
        {name:'service',label:'Function under test',type:'select',options:options(['sms','app_data','app_voice','native_voice','internet'])},
        {name:'operator',label:'Operator / contracted provider',maxLength:80}, {name:'plannedFor',label:'Planned date',type:'date',required:false},
        {name:'scenario',label:'Test scenario',maxLength:160,wide:true},
      ]} onSubmit={v=>context.mutate('/v1/ops/trials',{siteId:v.siteId,assetId:v.assetId,path:v.path,service:v.service,operator:v.operator,scenario:v.scenario,...(v.plannedFor?{plannedFor:v.plannedFor}:{})},'POST','Field-trial plan saved. No network action was executed.')}/></Details>
        : <Empty>{writable ? 'Add a site and its test equipment before planning a field trial.' : 'Your role can review recorded field trials.'}</Empty>}
    </Panel>
    <Panel title="Trial records" hint={`${visible.length} shown`}><Search label="Find a trial by scenario, operator or result" value={search} setValue={setSearch}/>
      {visible.length ? <div className="mw-record-list">{visible.map(trial=><article className="mw-record" key={trial.id}>
        <div className="mw-record-line"><div><h3>{String(trial.scenario)}</h3><p>{String(trial.operator)} · {humanize(trial.path)} · {humanize(trial.service)}</p></div><Pill value={trial.result??trial.state}/></div>
        <p className="mw-secondary">{String(data.assets.find(a=>a.id===trial.assetId)?.tag??trial.assetId)} · {String(data.sites.find(s=>s.id===trial.siteId)?.name??'Site unavailable')}</p>
        {trial.state==='completed' ? <div className="mw-stack"><p>{String(trial.observation)}</p><div className="mw-inline-facts"><span>Source: <strong>{humanize(trial.source)}</strong></span><span>Observed: <DateText value={trial.observedAt}/></span>{trial.latencyMs!==undefined&&<span>Latency: {Number(trial.latencyMs)} ms</span>}{trial.downloadMbps!==undefined&&<span>Download: {Number(trial.downloadMbps)} Mbps</span>}</div><p className="mw-secondary">Evidence: {String(trial.evidenceRef)}. Recorded observations do not independently establish service availability.</p></div>
          : writable && <Details label={`Record result for ${String(trial.scenario)}`}><TrialResult trial={trial} context={context}/></Details>}
        <Details label="Record reference and time"><RecordMeta item={trial}/></Details>
      </article>)}</div> : <Empty>{search?'No trials match this search.':'No field trials have been recorded.'}</Empty>}
    </Panel>
  </div>;
}
function TrialResult({trial,context}:{trial:Item;context:WorkspaceContext}) {
  const fields:Field[]=[
    {name:'result',label:'Result',type:'select',options:options(['pass','fail','blocked'])},
    {name:'source',label:'Evidence source',type:'select',options:[{value:'manual_field_record',label:'Manual field observation'},{value:'lab_simulator',label:'Lab simulation'}]},
    {name:'observedAt',label:'Observation date and time',type:'datetime-local',hint:'Your device’s local time; saved with a time-zone-independent timestamp.'},
    {name:'evidenceRef',label:'Evidence reference',maxLength:160},
    {name:'latencyMs',label:'Measured latency (ms)',type:'number',min:0,max:60000,step:'0.1',required:false},
    {name:'downloadMbps',label:'Measured download (Mbps)',type:'number',min:0,max:10000,step:'0.01',required:false},
    {name:'observation',label:'What happened?',type:'textarea'},
  ];
  return <RecordForm title={`Record result ${trial.id}`} fields={fields} busy={context.pending} submitLabel="Save immutable result" onSubmit={v=>context.mutate(`/v1/ops/trials/${trial.id}/results`,{revision:trial.revision,result:v.result,source:v.source,observedAt:new Date(v.observedAt).toISOString(),evidenceRef:v.evidenceRef,observation:v.observation,...(v.latencyMs!==''?{latencyMs:Number(v.latencyMs)}:{}),...(v.downloadMbps!==''?{downloadMbps:Number(v.downloadMbps)}:{})},'POST','Trial result saved. Repeat the trial to record another observation.')}><p className="mw-secondary">A passing result requires commissioned equipment. Completed observations cannot be overwritten.</p></RecordForm>;
}
