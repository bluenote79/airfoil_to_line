import adsk.core, adsk.fusion, adsk.cam, traceback
import math as math
import os
from math import e
from math import pi
import sys


script_path = os.path.dirname(os.path.abspath(__file__))
directory = "lib"
parent_dir = script_path
path_l = os.path.join(parent_dir, directory)

sys.path.append(path_l)

import euklid
import pyfoil



# Global set of event handlers to keep them referenced for the duration of the command
handlers = []
ui = None
app = adsk.core.Application.get()
if app:
    ui  = app.userInterface

product = app.activeProduct
design = adsk.fusion.Design.cast(product)
root = design.rootComponent
sketches = root.sketches
planes = root.constructionPlanes

class FoilCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            command = args.firingEvent.sender
            inputs = command.commandInputs
          
            input1 = inputs[0]
            sel0 = input1.selection(0)
            input2 = inputs[1]
            sel1 = input2.selection(0)
            input3 = inputs[2]
            input4 = inputs[3]
            input5 = inputs [4]
            input6 = inputs [5]
            input7 = inputs [6]

            foil = Foil()
            foil.Execute(sel0, sel1, input3.value, input4.value, 1, input5.value, input6.value, input7.value);
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

# Event handler that reacts to when the command is destroyed. This terminates the script.
class FoilCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # When the command is done, terminate the script
            # This will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


class AirfoilF(pyfoil.Airfoil):
    
    """
    AirfoilF inheritance from pyfoil Airfoil which is licensed under GNU v3
    https://github.com/airgproducts/pyfoil.git
    https://pypi.org/project/pyfoil/
    """

 
    def read_angle(self):
        
        diff = (self.curve.nodes[0] + self.curve.nodes[-1]) * 0.5
        alpha = -diff.angle()
        
        return alpha

    def set_end_one(self):

        self.curve.nodes[0][0] = 1
        self.curve.nodes[-1][0] = 1

    def open_tail(self):
        if self.curve.nodes[0][0] > self.curve.nodes[-1][0]:
            self.curve.nodes[-1][0] == self.curve.nodes[0][0]
        else:
            print("normal length")
        
        if self.curve.nodes[0][1] == self.curve.nodes[-1][1]:
            self.curve.nodes[0][1] = 0.000001
            self.curve.nodes[-1][1] = 0.000001
        else:
            print("gap at the end")

    def close_tail(self):
        self.curve.nodes[-1][0] = 1
        self.curve.nodes[0][0] = 1
        self.curve.nodes[0][1] = 0
        self.curve.nodes[-1][1] = 0


    def export_to_list(self):
        """
        Export airfoil to list of tupel (x, y)
        """
        normal = []
        for node in self.curve.nodes:
            normal.append((float(node[0]), float(node[1])))

        return normal
    
    def export_info(self, tail_gap, root_length, y_scale, faktor_exp):

        tail_gap_is = self.curve.nodes[0][1] - self.curve.nodes[-1][1]

        thickening_max = 0.5 * abs((tail_gap - tail_gap_is * 10)) / root_length

        back = thickening_max * root_length

        export = f'tail_gap {tail_gap}, root_length {root_length}, y_scale {y_scale}, faktor_exp {faktor_exp}, gapis {tail_gap_is}, thick max {thickening_max}, back {back}'

        return export


    def tailing_edge_thickening(self, tail_gap, root_length, y_scale, faktor_exp):

        tail_gap_is = root_length * (self.curve.nodes[0][1] - self.curve.nodes[-1][1])

        root_length = root_length

        thickening_max = 0.5 * abs((tail_gap - tail_gap_is)) / root_length   #   /2     ##  root_length * y scale# durch die Faktoren wieder in den raum bis x = 1   # vorn abs

        for i in range(len(self.curve.nodes)):
            if self.curve.nodes[i][0] == 0 and self.curve.nodes[i][1] == 0:
                nose_index = i

        x_norm = [self.curve.nodes[i][0] for i in range(len(self.curve.nodes))]
        y_norm = [self.curve.nodes[i][1] for i in range(len(self.curve.nodes))]

        if x_norm[-1] != 0:
            self.curve.nodes[-1] = (self.curve.nodes[-1][0], self.curve.nodes[0][1])

        for i in range(len(x_norm)):
            thickening = (abs(thickening_max) * (e**((float(x_norm[i])) - 1) * (faktor_exp)))

            if i < nose_index and y_norm[4] < y_norm[-5]:     
                y_norm[i] = y_norm[i] -abs(thickening*0.1)
            elif i < nose_index and y_norm[4] > y_norm[-5]:
                y_norm[i] = y_norm[i] + abs(thickening*0.1)
            elif i == nose_index:
                y_norm[i] = 0                   
            elif i > nose_index and y_norm[4] < y_norm[-5]:
                y_norm[i] = y_norm[i] + abs(thickening*0.1)
            elif i > nose_index and y_norm[4] > y_norm[-5]:
                y_norm[i] = y_norm[i] - abs(thickening*0.1)

        for i in range(len(self.curve.nodes)):
            self.curve.nodes[i][1] = y_norm[i]

        half_gap = round(tail_gap / (2 * root_length), 7)

        self.curve.nodes[0][1] = half_gap
        self.curve.nodes[-1][1] = -half_gap

        return AirfoilF


class Foil:
    def Execute(self, sel0, sel1, endleiste_soll, faktor_exponent, y_scale, resample_it, number_pt_crv, break_it):

       
        def scale_sketch(profil_neu):
        
            sketchAirfoil = sketches.add(root.xYConstructionPlane)
            sketchAirfoil.name=f"sketchAirfoil"

            points_new = adsk.core.ObjectCollection.create()

            for p in range(len(profil_neu)):
                point = adsk.core.Point3D.create(float(profil_neu[p][0]), float(profil_neu[p][1]), 0.0)    # points in mm normfaktor raus
                points_new.add(point)
                  
            #lines = sketchAirfoil.sketchCurves.sketchLines                                         # cleanup
            #curveAirfoil = sketchAirfoil.sketchCurves.sketchFittedSplines.add(points_new)          # cleanup

            sketchCount = 0
            for sketch in sketches:
                if sketch == sketchAirfoil:
                    sketchIndexAirfoil = sketchCount
                    break
                else:
                    sketchCount += 1

            contour2 = root.sketches.item(sketchIndexAirfoil)

            scales = root.features.scaleFeatures

            scaleFactor = adsk.core.ValueInput.createByReal(wurzeltiefe * y_scale)              #  * y_scale
            inputEntity = adsk.core.ObjectCollection.create()
            inputEntity.add(contour2)

            pointsCount = 0
            for point in contour2.sketchPoints:
                point = contour2.sketchPoints.item(pointsCount)
                if point.geometry.x == 0 and point.geometry.y == 0:
                    basePt2 = contour2.sketchPoints.item(pointsCount) # here is the noseindex
                    break
                else:
                    sketchCount += 1

            
            bx2 = basePt2.geometry.x
            by2 = basePt2.geometry.y                         

            scaleInput = scales.createInput(inputEntity, basePt2, scaleFactor)
            scale = scales.add(scaleInput)

            list_point2 = []
            for p in range(len(y_norm)):      # y values ursprg
                point = adsk.core.Point3D.cast(points_new.item(p))
                coords2 = point.getData()
                list_point2.append(coords2)

            list3 = [(float(list_point2[p][1]), float(list_point2[p][2]), 0.0) for p in range(len(list_point2))]

            sketchAirfoil.deleteMe()

            return list3

        def mirror_h(profil):
        
            profil_m = [(profil[p][0], profil[p][1], -profil[p][2], profil[p][3]) for p in range(len(profil))]

            return profil_m
        
        def mirror_v(profil):

            profil_m = [(profil[p][0], 1 -profil[p][1], profil[p][2], profil[p][3]) for p in range(len(profil))]

            return profil_m
        
        

        ############### MAIN ###################
        
        # Open first file for reading original DAT file
        dlg = ui.createFileDialog()
        dlg.title = 'Open DAT File'
        dlg.filter = 'Airfoil DAT files (*.dat);;All Files (*.*)'
        if dlg.showOpen() != adsk.core.DialogResults.DialogOK :
            return
        
        filename = dlg.filename
                   
        # analyse input
        line_sehne = sel0.entity
        line_oben = sel1.entity

        if line_sehne.startSketchPoint == line_oben.startSketchPoint:
                start = line_sehne.startSketchPoint
                ende = line_sehne.endSketchPoint
                start2 = line_oben.startSketchPoint
                ende2 = line_oben.endSketchPoint
        elif line_sehne.startSketchPoint == line_oben.endSketchPoint:
                start = line_sehne.startSketchPoint
                ende = line_sehne.endSketchPoint
                start2 = line_oben.endSketchPoint
                ende2 = line_oben.startSketchPoint
        elif line_sehne.endSketchPoint == line_oben.endSketchPoint:
                start = line_sehne.endSketchPoint
                ende = line_sehne.startSketchPoint
                start2 = line_oben.endSketchPoint
                ende2 = line_oben.startSketchPoint
        elif line_sehne.endSketchPoint == line_oben.startSketchPoint:
                start = line_sehne.endSketchPoint
                ende = line_sehne.startSketchPoint
                start2 = line_oben.startSketchPoint
                ende2 = line_oben.endSketchPoint
        
        wurzeltiefe = line_sehne.length
             
        # use xpoil class methodes
        foilAngle = AirfoilF.import_from_dat(filename)
        alpha = round(AirfoilF.read_angle(foilAngle) + math.pi / 2, 2)
        foilf = AirfoilF.import_from_dat(filename).normalized(False)

        
        AirfoilF.open_tail(foilf)

        # AirfoilF.set_end_one(foilf)
        if resample_it is True:
            foil_new = AirfoilF.resample(foilf, int(number_pt_crv))
        else:
            foil_new = foilf

        # maybe integrate more xfoil features later ###################
        #chamber_val = 0.5
        #y_scale = 0.1 * y_scale
        #set_chamber_dialogue = False
        #thickness_val = 6
        #set_thickness_dialogue = False

        #if set_chamber_dialogue is True:
        #    AirfoilF.set_camber(foilf, chamber_val)

        #if set_thickness_dialogue is True:
        #    AirfoilF.set_thickness(foilf, thickness_val)
        ################################################################


        listedat = AirfoilF.export_to_list(foil_new)
        xv, yv = list(zip(*listedat))
        no = xv.index(min(xv))
        
        werte = AirfoilF.export_info(foilf, endleiste_soll, wurzeltiefe, y_scale, faktor_exponent)

        # decide if tailing edge should be thickened
        if endleiste_soll != 0:
            AirfoilF.tailing_edge_thickening(foil_new, endleiste_soll, wurzeltiefe, y_scale, faktor_exponent)
        else:
            AirfoilF.close_tail(foil_new)

        #AirfoilF.set_thickness(foilf, (y_scale - 1))

        profil_neu = AirfoilF.export_to_list(foil_new)

        x_norm, y_norm = list(zip(*profil_neu))

        # xfoil scales to length of 1, therfore scaling with fusion 360
        list3 = scale_sketch(profil_neu)

        # get filename for naming the sketch in fusion 360        
        datei = os.path.basename(filename)

        ################## TO DO name differend scetch not temp sketch ##################
        sketchAirfoil2 = sketches.add(root.xYConstructionPlane)
    
        scaleMatrix = adsk.core.Matrix3D.create()
        scaleMatrix.setCell(0, 0, wurzeltiefe)
        scaleMatrix.setCell(1, 1, wurzeltiefe)

               
        countersk = 0
        for sketch in root.sketches:
            if sketch == sketchAirfoil2:
                nr = countersk
            else:
                countersk += 1

        if list3[0][0] < 1:
            temp = ((1.0, -1.0 * float(list3[-1][1])))
            list3.insert(0, temp)              # Punkt am Ende ergänzen
                
        if list3[-1][0] < 1:
            temp = ((1.0 , -1.0 * float(list3[0][1])))
            list3.append(temp)

        points_airfoil2 = adsk.core.ObjectCollection.create()
        point_nose = adsk.core.ObjectCollection.create()

        vector = adsk.core.Vector3D.create(start.geometry.x, start.geometry.y)


        transform = adsk.core.Matrix3D.create()
        transform.translation = vector

        point_mid_el = adsk.core.Point3D.create(wurzeltiefe, 0.5 * (float(list3[0][1]) + float(list3[-1][1])), 0.0)
        point_mid_el.transformBy(transform)


        axes = root.constructionAxes
        axisInput = axes.createInput()
        axisInput.setByTwoPoints(start, ende)
        axes.add(axisInput)
        axisInput.setByTwoPoints(start2, ende2)
        axes.add(axisInput)

        x_axe = axes[0]
        x_dir = x_axe.geometry.direction
        y_axe = axes[1]
        y_dir = y_axe.geometry.direction
        z_axe = x_dir.crossProduct(y_dir)

        midline = start.geometry.vectorTo(point_mid_el)
        midlineto = start.geometry.vectorTo(ende.geometry) 
        midlinerotationMatrix = adsk.core.Matrix3D.create()
        midlinerotationMatrix.setToRotateTo(midline, midlineto, z_axe)

        sketchTest = line_sehne.parentSketch
        sketchTest.name=f'{datei}_{round(y_scale * 100 * 10, 0)}% {round(alpha, 2)}° {round(endleiste_soll * 10, 2)}_mm tail'

        pointplus  = adsk.core.Point3D.create(1, 1, 0)
        pointminus  = adsk.core.Point3D.create(1, -1, 0)
        pointplus.transformBy(midlinerotationMatrix)
        pointplus.transformBy(transform)
        pointminus.transformBy(midlinerotationMatrix)
        pointminus.transformBy(transform)

        pointminusdist = app.measureManager.measureMinimumDistance(pointminus, ende2.geometry).value
        pointplusdist = app.measureManager.measureMinimumDistance(pointplus, ende2.geometry).value

        # make sure upper side is oriented towards the side of the vertical line
        if  pointminusdist < pointplusdist:
            try:
                xtemp, ytemp = list(zip(*list3))
            except:
                xtemp = [list3[i][0] for i in range(len(list3))]
                ytemp = [list3[j][1] for j in range(len(list3))]

            list4 = [(xtemp[i], -ytemp[i]) for i in range(len(xtemp))]
            list3 = list4
        else:
            list3 =  list3


        # sketch points at the sketch origin, scale according root, move to line, rotate
        for p in range(len(list3)):
            point = adsk.core.Point3D.create(float(list3[p][0]), float(list3[p][1]), 0.0)    # points in mm normfaktor raus
            point.transformBy(scaleMatrix)
            point.transformBy(midlinerotationMatrix)
            point.transformBy(transform)
            points_airfoil2.add(point)
            if list3[p][0] == 0 and list3[p][1] == 0:
                point_nose.add(point)

        lines = sketchTest.sketchCurves.sketchLines
        curveAirfoil = sketchTest.sketchCurves.sketchFittedSplines.add(points_airfoil2)

        
        #if el_line == True:
        lines.addByTwoPoints(curveAirfoil.endSketchPoint, curveAirfoil.startSketchPoint)

        sketchAirfoil2.deleteMe()

        if break_it is True:
            try:
                curveAirfoil.breakCurve(point_nose.item(0), createConstraints=True)
            except:
                ui.messageBox(f"Curve must be broken manually")
    
       

class FoilValidateInputHandler(adsk.core.ValidateInputsEventHandler):
    def __init__(self):
        super().__init__()
      
    def notify(self, args):
        try:
            sels = ui.activeSelections
            if len(sels) == 1:
                args.areInputsValid = True
            else:
                args.areInputsValid = False
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


# Event handler that reacts when the command definitio is executed which
# results in the command being created and this event being fired.
class FoilCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:

            # Get the command that was created.
            cmd = adsk.core.Command.cast(args.command)

            onExecute = FoilCommandExecuteHandler()
            cmd.execute.add(onExecute)
            handlers.append(onExecute) 

            # Connect to the command destroyed event.
            onDestroy = FoilCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            onValidateInput = FoilValidateInputHandler()
            cmd.validateInputs.add(onValidateInput)


            handlers.append(onDestroy)

            # Get the CommandInputs collection associated with the command.
            inputs = cmd.commandInputs

            # Create the inputs       
            i1 = inputs.addSelectionInput("SketchLine", "Sehnenlinie", "Please select line")
            i1.addSelectionFilter(adsk.core.SelectionCommandInput.SketchLines)
            i2 = inputs.addSelectionInput("SketchLine", "ortogonale oben", "Please select line")
            i2.addSelectionFilter(adsk.core.SelectionCommandInput.SketchLines)
            i3 = inputs.addValueInput("Endleiste Dicke", "Endleiste Dicke", "mm", adsk.core.ValueInput.createByReal(0.1))
            i4 = inputs.addValueInput("Exponent", "Exponent", "", adsk.core.ValueInput.createByReal(10))
            i5 = inputs.addBoolValueInput("checkbox", "Punkte neu verteilen", True, "", False)
            i6 = inputs.addValueInput("ungerade Anzahl Punkte", "ungerade Anzahl Punkte", "", adsk.core.ValueInput.createByString("121"))
            i7 = inputs.addBoolValueInput("checkbox", "Kurve aufbrechen", True, "", False)
            

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


def run(context):
    try:
        title = 'Select Construction Plane'

        if not design:
            ui.messageBox('No active Fusion design', title)
            return

        
        commandDefinitions = ui.commandDefinitions

        # check the command exists or not
        cmdDef = commandDefinitions.itemById('AirfoilCMDDef')
        if not cmdDef:
            #resourceDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'Resources') # absolute resource file path is specified
            cmdDef = commandDefinitions.addButtonDefinition('AirfoilCMDDef',
                    'Foil Parameters',
                    'Creates Foil spline on selected construction plane')       #resourceDir


        onCommandCreated = FoilCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



