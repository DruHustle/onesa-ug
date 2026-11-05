import React,{useEffect,useMemo,useState} from 'react';
import {Alert,Linking,Platform,Pressable,ScrollView,Share,StatusBar,StyleSheet,Text,TextInput,View} from 'react-native';
import {SafeAreaProvider,SafeAreaView} from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';
import {circlePatrol,inspectionSweep,reviewMission,simulationPosition,validPoint,type MissionKind,type MissionDraft,type Point} from './src/mission';

const kinds:{id:MissionKind;title:string;caption:string}[]=[
 {id:'security_patrol',title:'Security round',caption:'Inspect a perimeter, gate or fence'},
 {id:'farm_inspection',title:'Farm inspection',caption:'Observe pivots, crops and livestock areas'},
 {id:'conservancy_check',title:'Conservancy',caption:'Document conservancy observations; no automated pursuit'},
 {id:'hospital_delivery',title:'Medical delivery',caption:'Plan only; medical flight is not certified'},
 {id:'ecommerce_delivery',title:'E-commerce delivery',caption:'Plan only; payload delivery unverified'}
];
type Tab='overview'|'route'|'locate'|'video'|'records';
type Observation={id:string;missionId:string;at:string;note:string;point:Point|null;source:'simulated'};
const planKey='onesa.drone.prototype.route.v1',observationsKey='onesa.drone.prototype.notes.v1';
const now=()=>new Date().toISOString();
const emptyPlan=():MissionDraft=>({id:'preview-'+Date.now().toString(36),title:'A77 prototype round',kind:'security_patrol',waypoints:[],altitudeMeters:25,notes:''});
const normalizeCoordinate=(s:string,min:number,max:number):number|null=>{
 if(!s.trim())return null;const v=Number(s);return Number.isFinite(v)&&v>=min&&v<=max?v:null;
};
const numberString=(n:number)=>n.toFixed(6);
function Action({title,onPress,secondary=false,disabled=false}:{title:string;onPress:()=>void;secondary?:boolean;disabled?:boolean}) {
 return <Pressable accessibilityRole="button" accessibilityState={{disabled}} disabled={disabled} onPress={onPress} style={({pressed})=>[styles.button,secondary?styles.secondary:styles.primary,pressed&&styles.pressed,disabled&&styles.disabled]}><Text style={[styles.buttonText,secondary&&styles.secondaryText]}>{title}</Text></Pressable>;
}
function Input({title,value,onChange,keyboardType,multiline=false,placeholder}:{title:string;value:string;onChange:(s:string)=>void;keyboardType?:'numeric'|'decimal-pad';multiline?:boolean;placeholder?:string}){
 return <View style={styles.field}><Text style={styles.label}>{title}</Text><TextInput accessibilityLabel={title} placeholder={placeholder} placeholderTextColor="#6D8494" value={value} onChangeText={onChange} keyboardType={keyboardType} multiline={multiline} style={[styles.input,multiline&&{height:90,textAlignVertical:'top'}]}/></View>;
}
function KeyValue({title,value}:{title:string;value:string}){return <View style={styles.keyValue}><Text style={styles.muted}>{title}</Text><Text style={styles.value}>{value}</Text></View>;}
function App(){
 const [tab,setTab]=useState<Tab>('overview');
 const [plan,setPlan]=useState<MissionDraft>(emptyPlan);
 const [latitude,setLatitude]=useState(''),[longitude,setLongitude]=useState('');
 const [marker,setMarker]=useState(''),[radius,setRadius]=useState('80');
 const [cargo,setCargo]=useState(''),[altitude,setAltitude]=useState('25');
 const [step,setStep]=useState<number|null>(null);
 const [observations,setObservations]=useState<Observation[]>([]);
 const [note,setNote]=useState(''),[loading,setLoading]=useState(true);
 const [feedback,setFeedback]=useState('');
 const kind=kinds.find(k=>k.id===plan.kind)??kinds[0];
 const preview=useMemo(()=>reviewMission(plan),[plan]);
 const simulation=useMemo(()=>step===null?null:simulationPosition(plan,step,now()),[plan,step]);
 useEffect(()=>{let live=true;(async()=>{
    try {
      const saved=await SecureStore.getItemAsync(planKey);
      const notes=await SecureStore.getItemAsync(observationsKey);
      if(!live)return;
      if(saved){const parsed=JSON.parse(saved) as MissionDraft;
        if(parsed&&Array.isArray(parsed.waypoints)&&parsed.waypoints.every(validPoint)&&!reviewMission(parsed).blocking.length)
          setPlan(parsed);
      }
      if(notes){const rows=JSON.parse(notes);if(Array.isArray(rows))setObservations(rows.slice(0,100));}
    }catch{if(live)setFeedback('Saved route could not be read. Create a new preview.');}
    finally{if(live)setLoading(false);}
 })();return()=>{live=false;};},[]);
 const update=(patch:Partial<MissionDraft>)=>{setStep(null);setPlan(p=>({...p,...patch}));setFeedback('');};
 const centre=()=>{
   const lat=normalizeCoordinate(latitude,-89,89),lon=normalizeCoordinate(longitude,-180,180);
   if(lat===null||lon===null){setFeedback('Enter valid latitude (-89 to 89) and longitude (-180 to 180).');return null;}
   return {lat,lon};
 };
 const addPoint=()=>{
   const c=centre();if(!c)return;
   if(plan.waypoints.length>=25){setFeedback('Maximum 25 preview checkpoints.');return;}
   update({waypoints:[...plan.waypoints,{latitude:c.lat,longitude:c.lon,label:marker.trim().slice(0,100)||'Waypoint '+(plan.waypoints.length+1)}]});
   setMarker('');
 };
 const template=(type:'patrol'|'inspection')=>{
   const c=centre();if(!c)return;
   try {
     const size=Number(radius);
     const route=type==='patrol'?circlePatrol(c.lat,c.lon,size):inspectionSweep(c.lat,c.lon,size,size,4);
     update({kind:type==='patrol'?'security_patrol':'farm_inspection',waypoints:route});
     setFeedback('Route geometry created for simulation review only.');
   }catch{setFeedback('Use a preview size between 10 and 1,000 metres.');}
 };
 const reset=()=>{setPlan(emptyPlan());setStep(null);setFeedback('New route draft.');};
 const save=async()=>{
   if(preview.blocking.length){setFeedback('Resolve route errors before saving.');return;}
   try{await SecureStore.setItemAsync(planKey,JSON.stringify(plan));setFeedback('Saved as a private local draft. Not sent to any drone or server.');}
   catch{setFeedback('Secure local storage failed. The route remains in this session only.');}
 };
 const exportPlan=()=>{
   if(preview.blocking.length){setFeedback('Review the route before exporting.');return;}
   Alert.alert('Share this private flight plan?','The export contains exact farm/conservancy coordinates. Share only with a trusted operator. It is not a drone command.',[
     {text:'Cancel',style:'cancel'},
     {text:'Share',onPress:()=>{void Share.share({message:JSON.stringify({...plan,mode:'simulation-only',physicalExecution:false},null,2)}).catch(()=>setFeedback('Sharing was cancelled or failed.'));}}
   ]);
 };
 const addObservation=async()=>{
   if(step===null||!simulation||!note.trim()){setFeedback('Start a simulation and enter an observation note.');return;}
   const entry:Observation={id:'obs-'+Date.now().toString(36),missionId:plan.id,at:now(),note:note.trim().slice(0,1000),point:simulation.point,source:'simulated'};
   const next=[entry,...observations].slice(0,100);
   try{await SecureStore.setItemAsync(observationsKey,JSON.stringify(next));setObservations(next);setNote('');setFeedback('Simulation observation saved securely on this device.');}
   catch{setFeedback('Could not save observation locally.');}
 };
 const map=async()=>{
   if(!simulation)return;
   const p=simulation.point;
   const link='https://www.openstreetmap.org/?mlat='+encodeURIComponent(p.latitude)+'&mlon='+encodeURIComponent(p.longitude)+'#map=15/'+encodeURIComponent(p.latitude)+'/'+encodeURIComponent(p.longitude);
   try{await Linking.openURL(link);}catch{setFeedback('Unable to open external map.');}
 };
 const vendor=async()=>{
   try{await Linking.openURL('https://apps.apple.com/app/id6467178101');}
   catch{setFeedback('Open CHUBORY FLY manually in the Apple App Store.');}
 };
 const tabs:[Tab,string][]=[['overview','Overview'],['route','Route'],['locate','Locate'],['video','Video'],['records','Notes']];
 return <SafeAreaProvider><SafeAreaView style={styles.outer}>
   <StatusBar barStyle="light-content"/>
   <ScrollView style={styles.scroll} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
    <View style={styles.hero}><View style={styles.dot}/><Text style={styles.eyebrow}>ONESA DRONE · A77 PROTOTYPE</Text><Text style={styles.headline}>Aerial missions</Text><Text style={styles.heroSub}>Route planning, inspection rounds and observation — simulation only.</Text><Text accessibilityRole="alert" style={styles.warning}>NO LIVE AIRCRAFT CONNECTION · NO AUTOMATED FLIGHT</Text></View>
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{flexGrow:0}} contentContainerStyle={styles.tabs}>
     {tabs.map(([value,label])=><Pressable key={value} accessibilityRole="tab" accessibilityState={{selected:tab===value}} style={[styles.tab,tab===value&&styles.selected]} onPress={()=>setTab(value)}><Text style={[styles.tabLabel,tab===value&&styles.tabSelected]}>{label}</Text></Pressable>)}
    </ScrollView>
    {loading&&<Text style={styles.muted}>Opening private drafts…</Text>}
    {tab==='overview'&&<View style={styles.stack}>
      <Text style={styles.sectionTitle}>Hardware status</Text>
      <View style={styles.card}><KeyValue title="Prototype" value="CHUBORY A77 brushless quadcopter"/><KeyValue title="Current manufacturer app" value="CHUBORY FLY"/><KeyValue title="Physical GPS" value="Unknown / not connected"/><KeyValue title="Live video source" value="Not connected"/><KeyValue title="Flight commands" value="Disabled by construction"/><Action title="Open manufacturer app information" secondary onPress={()=>void vendor()}/></View>
      <View style={styles.card}><Text style={styles.sectionTitle}>Mission options</Text>{kinds.map(k=><Pressable key={k.id} style={styles.item} accessibilityRole="button" onPress={()=>{update({kind:k.id});setTab('route');}}><Text style={styles.itemTitle}>{k.title}</Text><Text style={styles.muted}>{k.caption}</Text></Pressable>)}</View>
      <Text style={styles.hint}>Route plans and simulated check-ins do not give permission to fly or imply airspace approval, delivery certification, anti-poaching intervention, or real-time drone tracking.</Text>
    </View>}
    {tab==='route'&&<View style={styles.stack}>
      <Text style={styles.sectionTitle}>Design a route</Text>
      <View style={styles.card}><Input title="Mission name" value={plan.title} onChange={title=>update({title:title.slice(0,100)})}/>
        <Text style={styles.label}>Mission type</Text><View style={styles.wrap}>{kinds.map(k=><Pressable key={k.id} accessibilityRole="button" style={[styles.chip,plan.kind===k.id&&styles.chipSelected]} onPress={()=>update({kind:k.id})}><Text style={styles.chipText}>{k.title}</Text></Pressable>)}</View>
        <Text style={styles.muted}>{kind.caption}</Text>
        <Input title="Simulation altitude (metres)" keyboardType="numeric" value={altitude} onChange={v=>{setAltitude(v);update({altitudeMeters:Number(v)})}}/>
        <Input title="Operator notes" value={plan.notes} onChange={v=>update({notes:v.slice(0,1000)})} multiline/>
        {plan.kind.includes('delivery')&&<Input title="Cargo description" value={cargo} onChange={v=>{setCargo(v);update({cargoDescription:v.slice(0,250)})}}/>}
      </View>
      <View style={styles.card}><Text style={styles.sectionTitle}>Checkpoints</Text>
        <Input title="Latitude" value={latitude} onChange={setLatitude} keyboardType="decimal-pad" placeholder="-17.800000"/>
        <Input title="Longitude" value={longitude} onChange={setLongitude} keyboardType="decimal-pad" placeholder="31.050000"/>
        <Input title="Waypoint label" value={marker} onChange={setMarker} placeholder="Farm gate, kraal, borehole"/>
        <Action title="Add checkpoint" onPress={addPoint} disabled={plan.waypoints.length>=25}/>
        <Input title="Template radius / width (metres)" value={radius} onChange={setRadius} keyboardType="numeric"/>
        <Action secondary title="Create round patrol preview" onPress={()=>template('patrol')}/>
        <Action secondary title="Create crop inspection sweep" onPress={()=>template('inspection')}/>
        {plan.waypoints.map((p,i)=><View key={i} style={styles.item}>
          <Text style={styles.itemTitle}>{i+1}. {p.label}</Text>
          <Text style={styles.muted}>{numberString(p.latitude)}, {numberString(p.longitude)}</Text>
          <Action secondary title="Remove checkpoint" onPress={()=>update({waypoints:plan.waypoints.filter((_,j)=>j!==i)})}/>
        </View>)}
      </View>
      <View style={styles.card}><Text style={styles.sectionTitle}>Route review</Text><KeyValue title="Waypoints" value={String(preview.waypointCount)}/><KeyValue title="Estimated straight-leg distance" value={preview.distanceMeters+' m · illustrative'}/>
      {preview.blocking.map((x,i)=><Text key={i} style={styles.error}>• {x}</Text>)}{preview.warnings.map((x,i)=><Text key={i} style={styles.hint}>• {x}</Text>)}
      <Action title="Save private route draft" disabled={!!preview.blocking.length} onPress={()=>void save()}/>
      <Action secondary title="Share plan for human review" disabled={!!preview.blocking.length} onPress={exportPlan}/>
      <Action secondary title="Start manual simulation (no flight)" disabled={!!preview.blocking.length} onPress={()=>{setStep(0);setTab('locate');setFeedback('Simulation started. The real aircraft is not connected.');}}/>
      <Action secondary title="New empty plan" onPress={reset}/></View>
    </View>}
    {tab==='locate'&&<View style={styles.stack}>
      <Text style={styles.sectionTitle}>Drone location</Text>
      <View style={styles.card}><Text style={styles.warning}>REAL AIRCRAFT: NO LOCATION AVAILABLE</Text><Text style={styles.hint}>CHUBORY FLY may show local flight status when connected directly to the A77 Wi‑Fi hotspot. Onesa has no verified GPS/API adapter or remote position feed.</Text><Action secondary title="Open CHUBORY FLY information" onPress={()=>void vendor()}/></View>
      {simulation?<View style={styles.card}><Text style={styles.sectionTitle}>Simulated position · point {step!+1}/{plan.waypoints.length}</Text>
        <Text style={styles.coord}>{simulation.point.latitude.toFixed(6)}</Text><Text style={styles.coord}>{simulation.point.longitude.toFixed(6)}</Text><Text style={styles.muted}>Source: SIMULATED — not GPS telemetry</Text>
        <Action secondary title="Open simulated point on map (shares coordinates)" onPress={()=>void map()}/>
        <Action title="Next simulated checkpoint" disabled={step===null||step>=plan.waypoints.length-1} onPress={()=>setStep(x=>x===null?null:Math.min(x+1,plan.waypoints.length-1))}/>
        <Action secondary title="Restart simulation" onPress={()=>setStep(0)}/>
        <Action secondary title="End simulation" onPress={()=>setStep(null)}/>
      </View>:<View style={styles.card}><Text style={styles.muted}>No active simulation. Build and review a route first.</Text><Action title="Open route planner" onPress={()=>setTab('route')}/></View>}
    </View>}
    {tab==='video'&&<View style={styles.stack}><Text style={styles.sectionTitle}>Camera & inspections</Text>
      <View style={[styles.card,styles.video]}><Text style={styles.warning}>VIDEO DISCONNECTED</Text><Text style={styles.muted}>No camera SDK, stream endpoint or consented relay is configured.</Text></View>
      <View style={styles.card}><Text style={styles.hint}>Use CHUBORY FLY over the A77 local Wi‑Fi for the manufacturer's video features. Remote livestreaming, encrypted recording, access control, georeferenced clips and mobile uplink need separate hardware/software integration and field testing.</Text>
        <Action title="Open CHUBORY FLY information" secondary onPress={()=>void vendor()}/></View>
    </View>}
    {tab==='records'&&<View style={styles.stack}><Text style={styles.sectionTitle}>Inspection notes</Text>
      <View style={styles.card}><Text style={styles.hint}>These are local simulation notes, not a live security finding or evidence of illegal activity. Keep any real security footage private and subject to lawful handling.</Text><Input title="Observation" value={note} onChange={setNote} multiline placeholder="Fence damage, animal count concern, gate status…"/>
        <Action title="Record simulated observation" disabled={!simulation||!note.trim()} onPress={()=>void addObservation()}/></View>
      {observations.map(x=><View key={x.id} style={styles.card}><Text style={styles.itemTitle}>{x.at} · SIMULATED</Text><Text style={styles.value}>{x.note}</Text><Text style={styles.muted}>Source: {x.source} · {x.point?numberString(x.point.latitude)+', '+numberString(x.point.longitude):'No coordinate'}</Text></View>)}
      {!observations.length&&<Text style={styles.muted}>No inspection observations recorded.</Text>}
    </View>}
    {!!feedback&&<Text accessibilityRole="alert" style={styles.feedback}>{feedback}</Text>}
    <Text style={styles.footer}>Onesa Drone prototype · No physical controls, live coordinates, real video or autonomous patrol. Refer to an authorized operator and applicable aviation/privacy rules before any field use.</Text>
   </ScrollView>
 </SafeAreaView></SafeAreaProvider>;
}
const styles=StyleSheet.create({
 outer:{flex:1,backgroundColor:'#071923'},scroll:{flex:1},content:{padding:16,paddingBottom:60,gap:16,maxWidth:740,alignSelf:'center',width:'100%'},
 hero:{backgroundColor:'#0D2B35',borderRadius:24,padding:22,gap:9,borderColor:'#295365',borderWidth:1},
 dot:{backgroundColor:'#11CAA7',height:8,width:8,borderRadius:10},eyebrow:{color:'#6DE3D0',fontSize:11,fontWeight:'700',letterSpacing:2},
 headline:{color:'#F7FAFB',fontSize:29,fontWeight:'800'},heroSub:{color:'#C6DFE5',fontSize:14,lineHeight:20},
 warning:{color:'#FFCA84',fontSize:12,fontWeight:'700',letterSpacing:.4},
 tabs:{gap:8,paddingVertical:4},tab:{paddingHorizontal:16,paddingVertical:11,borderRadius:99,backgroundColor:'#173341'},selected:{backgroundColor:'#D6FCF2'},tabLabel:{color:'#C2D9DF',fontWeight:'700'},tabSelected:{color:'#08302A'},
 stack:{gap:14},sectionTitle:{color:'#EAF8F9',fontSize:19,fontWeight:'800',marginBottom:7},
 card:{backgroundColor:'#11303E',borderColor:'#26505B',borderWidth:1,borderRadius:18,padding:17,gap:12},
 field:{gap:6},label:{color:'#DCECF0',fontSize:13,fontWeight:'700'},input:{color:'#F5FFFF',backgroundColor:'#08242E',borderColor:'#39737D',borderWidth:1,borderRadius:12,paddingVertical:11,paddingHorizontal:14,fontSize:16,minHeight:44},
 button:{minHeight:45,borderRadius:12,alignItems:'center',justifyContent:'center',padding:10},primary:{backgroundColor:'#12CEA8'},secondary:{backgroundColor:'#1D4C56',borderColor:'#52828B',borderWidth:1},pressed:{opacity:.8},disabled:{opacity:.45},buttonText:{color:'#073A30',fontSize:14,fontWeight:'800',textAlign:'center'},secondaryText:{color:'#E1F5F2'},
 keyValue:{flexDirection:'row',justifyContent:'space-between',flexWrap:'wrap',gap:6},muted:{color:'#A9C2CB',lineHeight:20,fontSize:13},value:{color:'#F4FAFB',fontWeight:'600',fontSize:14},
 hint:{color:'#C3CED8',lineHeight:19,fontSize:13},error:{color:'#FFA59E',lineHeight:20},item:{borderTopWidth:1,borderTopColor:'#2A5360',paddingTop:12,gap:6},itemTitle:{color:'#E7F6F7',fontSize:15,fontWeight:'700'},coord:{color:'#E9FFF9',fontSize:28,fontVariant:['tabular-nums'],fontWeight:'800'},
 wrap:{flexDirection:'row',flexWrap:'wrap',gap:8},chip:{backgroundColor:'#254856',paddingHorizontal:12,paddingVertical:8,borderRadius:15},chipSelected:{backgroundColor:'#14665B'},chipText:{color:'#E3FFFA',fontSize:13,fontWeight:'600'},
 video:{minHeight:220,justifyContent:'center',alignItems:'center',backgroundColor:'#030D12'},feedback:{padding:12,color:'#CFF9EE',backgroundColor:'#165D59',borderRadius:12},footer:{color:'#92AAB7',fontSize:11,lineHeight:17,paddingVertical:18}
});
export default App;
