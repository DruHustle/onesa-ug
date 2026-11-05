import {test} from 'node:test';
import assert from 'node:assert/strict';
import {circlePatrol,inspectionSweep,reviewMission,segmentMeters,simulationPosition,physicalFlightCommandsEnabled,realA77TelemetryConnected,type MissionDraft} from '../src/mission';

const point=(latitude:number,longitude:number,label='Checkpoint')=>({latitude,longitude,label});
const draft=(kind:MissionDraft['kind']='security_patrol'):MissionDraft=>({
 id:'11111111-1111-4111-8111-111111111111',
 title:'Prototype observation mission',kind,altitudeMeters:30,notes:'Operator review only',
 waypoints:[point(-17.8,31.0,'Start'),point(-17.8005,31.0004,'Inspect')]
});
test('all routes and telemetry remain preview-only and never carry a live command',()=>{
 assert.equal(physicalFlightCommandsEnabled,false);
 assert.equal(realA77TelemetryConnected,false);
 const plan=draft();
 const review=reviewMission(plan);
 assert.equal(review.blocking.length,0);
 assert.equal(review.mode,'simulation-only');
 assert.ok(review.warnings.some(x=>x.includes('No aircraft connection')));
 const observedAt='2026-11-05T11:00:00Z';
 const position=simulationPosition(plan,1,observedAt);
 assert.equal(position.source,'simulated');
 assert.equal(position.observedAt,observedAt);
 assert.deepEqual(position.point,plan.waypoints[1]);
});
test('invalid GPS, altitude, duplicate points, excessive routes and medical cargo remain blocked',()=>{
 const p=draft();
 assert.ok(reviewMission({...p,waypoints:[point(95,31),point(-17,30)]}).blocking.length);
 assert.ok(reviewMission({...p,altitudeMeters:900}).blocking.length);
 assert.ok(reviewMission({...p,waypoints:[point(-17.8,31),point(-17.8,31)]}).blocking.length);
 assert.ok(reviewMission({...p,waypoints:[point(-17.8,31),point(0,0)]}).blocking.length);
 assert.ok(reviewMission({...p,waypoints:Array.from({length:26},(_,i)=>point(-17.8+i*.0001,31))}).blocking.length);
 assert.ok(reviewMission(draft('hospital_delivery')).blocking.some(s=>s.includes('cargo')));
 assert.ok(reviewMission({...draft('hospital_delivery'),cargoDescription:'Sealed non-temperature-controlled supplies'}).warnings.some(x=>x.includes('medical')));
 assert.throws(()=>simulationPosition(p,9,'now'));
});
test('patrol and crop inspection routes have reproducible geometry and explicit return',()=>{
 const route=circlePatrol(-17.8,31.0,80,8);
 assert.equal(route.length,9);
 assert.equal(route.at(-1)?.latitude,route[0].latitude);
 assert.equal(route.at(-1)?.longitude,route[0].longitude);
 const a=reviewMission({...draft(),waypoints:route});
 assert.equal(a.blocking.length,0);
 assert.ok(a.distanceMeters>300&&a.distanceMeters<700);
 assert.equal(inspectionSweep(-17.8,31,120,120,4).length,8);
 assert.ok(segmentMeters(point(-17.8,31),point(-17.801,31))>100);
 assert.throws(()=>circlePatrol(-17.8,31,50000));
 assert.throws(()=>inspectionSweep(90,31,10,10));
});
