"""Map-constrained dry compartments; bank spots never become marsh levels."""
import numpy as np
import shapely
from shapely.geometry import Point, Polygon, box


def smooth(a,b,v):
    t=np.clip((v-a)/(b-a),0,1)
    return t*t*(3-2*t)


class MarshSurface:
    def __init__(self,config,review,datum,water,geoms,protected,structures,railways=None):
        self.config=config; self.datum=datum
        e0,n0,e1,n1=config['reviewBoundsBNG']
        self.outline=(Polygon([(e-538900,183209-n) for e,n in config['reviewOutlineBNG']])
                      if 'reviewOutlineBNG' in config else box(e0-538900,183209-n1,e1-538900,183209-n0))
        assert self.outline.is_valid,'Invalid reviewed ground outline'
        candidates=self.outline.difference(water)
        e,n=config['interiorPointBNG'];seed=Point(e-538900,183209-n)
        parts=[g for g in shapely.get_parts(candidates) if g.covers(seed)]
        assert len(parts)==1,'Marsh compartment is ambiguous'
        self.protected=protected
        self.bank=shapely.union_all([geoms[k] for k in config['bankReachIds']])
        # The far southern tip meets the older detailed mesh. Leave it in
        # place and taper into it; the selected measured dots remain outside it.
        self.area=parts[0].difference(protected.buffer(8))
        if config.get('surfaceMode')=='bank-margin':
            self.area=self.area.intersection(self.bank.buffer(config['bankTransitionMetres'][1]))
        self.support_area=self.area
        self.railways=[]
        self.structure_area=shapely.GeometryCollection()
        for identifier in config.get('integratedRailwayIds',[]):
            railway=next(r for r in railways or [] if r.get('id')==identifier)
            self.railways.append(railway)
            footprint=shapely.union_all([Polygon(p[0],p[1:]) for p in railway['footprint']])
            self.structure_area=self.structure_area.union(self.support_area.intersection(footprint))
            self.area=self.area.difference(footprint)
        assert self.area.intersection(protected).area<.001,'Patch reaches protected detailed terrain'
        assert self.area.intersection(structures.buffer(2)).area<.001,'Review structures before lifting this compartment'
        self.water=water
        rows={r['id']:r for r in review['observations']}
        self.controls=[]
        self.series={}
        for role,key in [('bank','bankControlIds'),('marsh','marshControlIds')]:
            stations=[]
            for identifier in config[key]:
                row=rows[identifier];e,n=row['positionBNG']
                assert row['sourceType']=='spot' and row['valueConfidence']=='high'
                assert not row.get('terrainUse','').startswith('Withheld'),identifier
                assert row['setting'] in (['marsh','open_ground','embankment_foot'] if role=='marsh' else ['embankment_top'])
                assert self.area.covers(Point(e-538900,183209-n)),identifier
                odn=(row['expectedValueFeet']+datum['liverpoolToNewlynFeet'])*.3048
                y=odn-datum['odnMinusSceneYMetres']
                stations.append((n,y))
                self.controls.append({'id':identifier,'role':role,'positionBNG':[e,n],
                    'positionScene':[e-538900,y,183209-n],'sourceFeet':row['expectedValueFeet'],
                    'heightODNMetres':odn,'sourceDatum':row['sourceDatum'],
                    'reviewCrop':row['detailCrop']})
            self.series[role]=np.array(sorted(stations))
        shapely.prepare(self.area)
        # Clipped/triangulated boundary coordinates can fall a few ulps on
        # either side. Sample both sides of the same mathematical edge without
        # widening the actual terrain footprint.
        self.sample_area=self.area.buffer(1e-7)
        self.sample_support_area=self.support_area.buffer(1e-7)
        shapely.prepare(self.sample_area);shapely.prepare(self.sample_support_area)

    def apply(self,xz,base,support=False):
        result=np.array(base,copy=True)
        selected=shapely.covers(self.sample_support_area if support else self.sample_area,shapely.points(xz))
        if not selected.any():return result
        q=xz[selected];pts=shapely.points(q);north=183209-q[:,1]
        bank_weight=1-smooth(*self.config['bankTransitionMetres'],shapely.distance(pts,self.bank))
        bank_only=self.config.get('surfaceMode')=='bank-margin'
        if bank_only:
            target=np.interp(north,*self.series['bank'].T)
        else:
            if self.config.get('groundInterpolation')=='inverse-distance-squared':
                controls=[c for c in self.controls if c['role']=='marsh']
                positions=np.array([c['positionScene'] for c in controls])
                distance2=np.sum((q[:,None,:]-positions[None,:,[0,2]])**2,axis=2)
                weights=1/np.maximum(distance2,1e-10)
                marsh=(weights@positions[:,1])/weights.sum(axis=1)
            else:marsh=np.interp(north,*self.series['marsh'].T)
            bank=np.interp(north,*self.series['bank'].T) if len(self.series['bank']) else marsh
            target=marsh+(bank-marsh)*bank_weight
        # Keep the existing mapped waterline and bed; join the dry ground to it.
        shore=smooth(*self.config['shoreTransitionMetres'],shapely.distance(pts,self.water))
        target=.08+(target-.08)*shore
        fade=smooth(*self.config['southernBlendNorthings'],north)
        fade*=1-smooth(*self.config['northernBlendNorthings'],north)
        fade*=smooth(*self.config['westernBlendEastings'],q[:,0]+538900)
        fade*=smooth(8,18,shapely.distance(pts,self.protected))
        if 'outlineTransitionMetres' in self.config:
            fade*=smooth(*self.config['outlineTransitionMetres'],shapely.distance(pts,self.outline.boundary))
        if bank_only:fade*=bank_weight
        result[selected]=base[selected]+(target-base[selected])*fade
        return result

    def railway_adjustments(self):
        """Lift the supporting earth slope with its ground, keeping the crest."""
        changes=[]
        for railway in self.railways:
            vertices=np.asarray(railway['embankment'],dtype=float)
            flat=vertices.reshape(-1,3);base=-.09
            ground=self.apply(flat[:,[0,2]],np.full(len(flat),base),support=True)
            crest=railway['formationHeight']
            weight=np.clip((crest-flat[:,1])/(crest-base),0,1)
            updated=flat[:,1]+(ground-base)*weight
            assert updated.max()<=max(crest,float(flat[:,1].max()))+1e-6
            for i in np.flatnonzero(np.abs(updated-flat[:,1])>1e-8):
                changes.append({'railwayId':railway['id'],'triangle':int(i//3),'vertex':int(i%3),
                    'beforeY':float(flat[i,1]),'afterY':float(updated[i]),'surfaceId':self.config['id']})
        return changes

    def metadata(self):
        return {'id':self.config['id'],'name':self.config['name'],'areaM2':self.area.area,
            'controls':self.controls,'config':self.config,'verticalReference':self.datum,
            'appliedToDisplayTerrain':True,'appliedToFloodSolver':False}


class TerrainSurfaces:
    """Apply separate reviewed compartments without averaging across rivers."""
    def __init__(self,surfaces):
        self.surfaces=surfaces
        for i,a in enumerate(surfaces):
            for b in surfaces[i+1:]:
                assert a.area.intersection(b.area).area<.001,'Reviewed compartments overlap'
        self.area=shapely.union_all([s.area for s in surfaces])
        self.structure_area=shapely.union_all([s.structure_area for s in surfaces])
        self.config={'meshCellMetres':min(s.config['meshCellMetres'] for s in surfaces)}

    def apply(self,xz,base):
        result=base
        for surface in self.surfaces:result=surface.apply(xz,result)
        return result

    def metadata(self):
        from build_lower_lea_region import rings
        return [dict(s.metadata(),polygons=rings(s.area)) for s in self.surfaces]
