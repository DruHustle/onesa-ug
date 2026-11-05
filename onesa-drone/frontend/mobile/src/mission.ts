export type MissionKind = 'security_patrol' | 'farm_inspection' | 'conservancy_check' | 'hospital_delivery' | 'ecommerce_delivery';
export type Point = Readonly<{latitude:number;longitude:number;label:string}>;
export type MissionDraft = Readonly<{
 id:string;title:string;kind:MissionKind;waypoints:readonly Point[];
 altitudeMeters:number; notes:string; cargoDescription?:string;
}>;
export type MissionPreview = {distanceMeters:number; waypointCount:number; warnings:string[]; blocking:string[]; mode:'simulation-only'};
const radians = (x:number)=>x*Math.PI/180;
const degrees = (x:number)=>x*180/Math.PI;
const R=6371000;
export function validPoint(x:Point):boolean{
 return Number.isFinite(x.latitude)&&Math.abs(x.latitude)<=90&&
        Number.isFinite(x.longitude)&&Math.abs(x.longitude)<=180&&
        typeof x.label==='string'&&x.label.trim().length<=100;
}
export function segmentMeters(a:Point,b:Point):number {
 if(!validPoint(a)||!validPoint(b))throw new Error('invalid_point');
 const dLat=radians(b.latitude-a.latitude),dLon=radians(b.longitude-a.longitude);
 const q=Math.sin(dLat/2)**2+Math.cos(radians(a.latitude))*Math.cos(radians(b.latitude))*Math.sin(dLon/2)**2;
 return 2*R*Math.atan2(Math.sqrt(q),Math.sqrt(Math.max(0,1-q)));
}
export function reviewMission(draft:MissionDraft):MissionPreview {
 const blocking:string[]=[];
 const warnings:string[]=['No aircraft connection or supported A77 flight-control SDK. Plan can be simulated or exported for human review only.',
 'No authoritative airspace, weather, obstacle, risk or pilot authorization has been checked.'];
 if(!draft.title.trim()||draft.title.length>100)blocking.push('Mission name must be 1–100 characters.');
 if(draft.notes.length>1000)blocking.push('Notes exceed 1000 characters.');
 if(!Number.isFinite(draft.altitudeMeters)||draft.altitudeMeters<5||draft.altitudeMeters>120)
    blocking.push('Simulation altitude must be between 5 and 120 metres (not an operational clearance).');
 if(!draft.waypoints.length||draft.waypoints.length>25)blocking.push('Choose 2 to 25 waypoints.');
 else if(draft.waypoints.length<2)blocking.push('At least two waypoints are required.');
 if(draft.waypoints.some(p=>!validPoint(p)))blocking.push('One or more coordinates are invalid.');
 let distanceMeters=0;
 if(draft.waypoints.every(validPoint)){
   for(let i=1;i<draft.waypoints.length;i++){
     const leg=segmentMeters(draft.waypoints[i-1],draft.waypoints[i]);
     if(leg<0.5)blocking.push('Consecutive waypoints must be different.');
     distanceMeters+=leg;
   }
 }
 if(distanceMeters>15000)blocking.push('Preview route exceeds 15 km. Split it into separate review plans.');
 if(['hospital_delivery','ecommerce_delivery'].includes(draft.kind)&&!(draft.cargoDescription??'').trim())
   blocking.push('Delivery plans require a cargo description.');
 if(draft.kind==='hospital_delivery')warnings.push('No medical transport, cold-chain or clinical certification is claimed.');
 if(draft.kind==='conservancy_check')warnings.push('Field observation is not automated poacher identification, pursuit or intervention.');
 return {distanceMeters:Math.round(distanceMeters),waypointCount:draft.waypoints.length,warnings,blocking,mode:'simulation-only'};
}
function wrapLon(lon:number):number{return ((lon+540)%360)-180;}
/** Local approximate route geometry for visualization only; never uploaded to aircraft. */
export function circlePatrol(latitude:number,longitude:number,radiusMeters:number,points=8):Point[] {
 if(!Number.isFinite(latitude)||Math.abs(latitude)>89||!Number.isFinite(longitude)||Math.abs(longitude)>180||
    !Number.isFinite(radiusMeters)||radiusMeters<10||radiusMeters>1000||
    !Number.isInteger(points)||points<4||points>16)throw new Error('invalid_patrol');
 const out:Point[]=[];
 for(let i=0;i<=points;i++){
   const angle=2*Math.PI*(i%points)/points;
   const lat=latitude+degrees(radiusMeters*Math.cos(angle)/R);
   const lon=wrapLon(longitude+degrees(radiusMeters*Math.sin(angle)/(R*Math.cos(radians(latitude)))));
   out.push({latitude:+lat.toFixed(7),longitude:+lon.toFixed(7),label:i===0?'Patrol start':i===points?'Return to start':`Check ${i}`});
 }
 return out;
}
/** Serpentine crop inspection pattern, bounded for conservative preview geometry. */
export function inspectionSweep(latitude:number,longitude:number,widthMeters:number,heightMeters:number,rows=4):Point[] {
 if(!Number.isFinite(latitude)||Math.abs(latitude)>89||!Number.isFinite(longitude)||Math.abs(longitude)>180||
    !Number.isFinite(widthMeters)||widthMeters<10||widthMeters>1000||
    !Number.isFinite(heightMeters)||heightMeters<10||heightMeters>1000||
    !Number.isInteger(rows)||rows<2||rows>10)throw new Error('invalid_inspection');
 const metresToLat=degrees(1/R),metresToLon=degrees(1/(R*Math.cos(radians(latitude))));
 const out:Point[]=[];
 for(let i=0;i<rows;i++){
    const lat=latitude+(i/(rows-1)-0.5)*heightMeters*metresToLat;
    const left=wrapLon(longitude-widthMeters/2*metresToLon);
    const right=wrapLon(longitude+widthMeters/2*metresToLon);
    const endpoints=i%2===0?[left,right]:[right,left];
    for(const lng of endpoints)out.push({latitude:+lat.toFixed(7),longitude:+lng.toFixed(7),label:`Inspection ${out.length+1}`});
 }
 return out;
}
/** GPS source is always explicit. A simulated point must never be displayed as actual drone position. */
export type AircraftPosition={source:'simulated';point:Point;observedAt:string;missionId:string} |
 {source:'unavailable';reason:'no_supported_adapter'};
export function simulationPosition(plan:MissionDraft,index:number,observedAt:string):AircraftPosition {
 if(reviewMission(plan).blocking.length)throw new Error('invalid_plan');
 if(!Number.isInteger(index)||index<0||index>=plan.waypoints.length)throw new Error('invalid_step');
 return {source:'simulated',point:plan.waypoints[index],observedAt,missionId:plan.id};
}
export const physicalFlightCommandsEnabled=false as const;
export const realA77TelemetryConnected=false as const;
