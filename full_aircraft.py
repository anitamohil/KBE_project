import os
from scripts.ref_frame import Frame
from scripts.fuselage import Fuselage
from scripts.wing import Wing
from scripts.HT import HorizontalTail
from scripts.VT import VerticalTail
from scripts.readGeometry import ReadGeometry
from scripts.winglet import *
from parapy.exchange.step import STEPWriter
from parapy.core import *
from parapy.geom import *
from AVL_analysis import AvlAnalysis
from parapy.gui import image
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Table
from reportlab.platypus import TableStyle
from reportlab.lib import colors

from scripts.xfoilAnalysis import XfoilAnalysis

DIR = os.path.dirname(__file__)


class Aircraft(GeomBase):
    input = ReadGeometry("A320")

    winglet_ON = Input(True)
    TYPE_wing_airfoil = Input(1)
    TYPE_winglet = Input(0)
    M_cruise = Input(input.M_cruise)  # cruise mach number

    ##### FUSELAGE #####
    ln_d = Input(input.ln_d)  # nose slenderness ratio
    lt_d = Input(input.lt_d)  # tail slenderness ratio

    ###### WING ######
    name = Input("wing")
    airfoil_root = Input(input.w_af_root)
    airfoil_kink = Input(input.w_af_kink)
    airfoil_tip = Input(input.w_af_tip)
    wing_span = Input(input.wing_span)
    incidence = Input(input.incidence)
    twist = Input(input.twist)
    wing_c_root = Input(input.wing_c_root)
    wing_taper_ratio_inboard = Input(input.wing_taper_ratio_inboard)

    ####### Horizontal Tail ############
    htp_root_airfoil = Input(input.ht_root)
    htp_tip_airfoil = Input(input.ht_tip)
    htp_area = Input(input.htp_area)
    htp_taper = Input(input.htp_taper)
    htp_dihedral = Input(input.htp_dihedral)

    ######### VERTICAL TAIL ###############
    vtp_root_airfoil = Input(input.vt_root)
    vtp_tip_airfoil = Input(input.vt_tip)
    vtp_aspect_ratio = Input(input.vtp_aspect_ratio)
    vtp_sweep = Input(input.vtp_sweep)
    vtp_area = Input(input.vtp_area)

    ########### Winglet ####################
    # --------TYPE 0 Canted Winglet-------------
    ct_name = "Canted Winglet"
    ct_airfoil_root = Input(input.ct_airfoil_root)
    ct_airfoil_tip = Input(input.ct_airfoil_tip)

    ct_chord_root_ratio = Input(input.ct_chord_root_ratio)
    ct_taper_ratio = Input(input.ct_taper_ratio)
    ct_height_ratio = Input(input.ct_height_ratio)
    ct_sweep = Input(input.ct_sweep)
    ct_cant = Input(input.ct_cant, validator=Range(0, 90))
    ct_twist_tip = Input(input.ct_twist_tip)

    # --------TYPE 1 Wingtip Fence-------------
    wtf_name = Input("Wingtip Fence")
    wtf_airfoil_up = Input(input.wtf_airfoil_up)
    wtf_airfoil_root = Input(input.wtf_airfoil_root)
    wtf_airfoil_down = Input(input.wtf_airfoil_down)
    wtf_chord_up = Input(input.wtf_chord_up)
    wtf_chord_root = Input(input.wtf_chord_root)
    wtf_chord_down = Input(input.wtf_chord_down)
    wtf_height_up = Input(input.wtf_height_up)
    wtf_height_down = Input(input.wtf_height_down)
    wtf_sweep_up = Input(input.wtf_sweep_up)
    wtf_sweep_down = Input(input.wtf_sweep_down)
    wtf_twist_up = Input(input.wtf_twist_up)
    wtf_twist_down = Input(input.wtf_twist_down)

    # --------TYPE 2 Raked Wingtip-------------
    rkt_name = Input("Raked Wingtip")
    rkt_airfoil_start = Input(input.rkt_airfoil_start)
    rkt_airfoil_tip = Input(input.rkt_airfoil_tip)
    rkt_chord_start = Input(input.rkt_chord_start)
    rkt_taper_ratio = Input(input.rkt_taper_ratio)
    rkt_span_ratio = Input(input.rkt_span_ratio)
    rkt_sweep_le = Input(input.rkt_sweep_le)

    # --------TYPE 3 Sharklet-------------------
    skt_airfoil_start = Input(input.skt_airfoil_start)
    skt_airfoil_mid = Input(input.skt_airfoil_mid)
    skt_airfoil_tip = Input(input.skt_airfoil_tip)

    skt_chord_mid = Input(input.skt_chord_mid)
    skt_K_lambda = Input(input.skt_K_lambda)
    skt_height_ratio = Input(input.skt_height_ratio)
    skt_KR = Input(input.skt_KR)
    skt_cant = Input(input.skt_cant)
    skt_sweep_le = Input(input.skt_sweep_le)
    skt_sweep_transition_te = Input(input.skt_sweep_transition_te)
    skt_twist = Input(input.skt_twist)
    skt_nu_blended_sections = Input(input.skt_nu_blended_sections)

    # XFOIL analysis input
    reynolds_number = Input(20000000)
    alpha = Input((-5, 25, 1))
    cutting_plane_span_fraction = Input(0.5)
    flydir = Input(True)


    @Part
    def aircraft_frame(self):
        return Frame(pos=self.position)  # this helps visualizing the wing local reference frame

    @Part
    def fuselage(self):
        return Fuselage(pass_down="ln_d, lt_d",
                        color="Blue")

    @Part
    def htp_right_wing(self):
        return HorizontalTail(htp_root_airfoil=self.htp_root_airfoil,
                              htp_tip_airfoil=self.htp_tip_airfoil,
                              htp_area=self.htp_area,
                              htp_taper=self.htp_taper,
                              htp_dihedral=self.htp_dihedral,
                              wing_area=self.right_wing.wing_area_total,
                              starting_point_mac=self.right_wing.starting_point_mac,
                              wing_sweep_025c=self.right_wing.wing_sweep_025c,
                              MAC_chord_length=self.right_wing.MAC_chord_length,
                              position=self.position.translate('z', 0.3 * self.fuselage.cabin_d))

    @Part
    def htp_left_wing(self):
        return MirroredShape(shape_in=self.htp_right_wing.solid,
                             reference_point=self.htp_right_wing.position,
                             transparency=0.4,
                             vector1=self.htp_right_wing.position.Vz,
                             vector2=self.htp_right_wing.position.Vx)

    @Part
    def right_wing(self):
        return Wing(name=self.name,
                    TYPE_airfoil=self.TYPE_wing_airfoil,
                    airfoil_root=self.airfoil_root,
                    airfoil_kink=self.airfoil_kink,
                    airfoil_tip=self.airfoil_tip,
                    wing_span=self.wing_span,
                    M_cruise=self.M_cruise,
                    incidence=self.incidence,
                    twist=self.twist,
                    wing_c_root=self.wing_c_root,
                    wing_taper_ratio_inboard=self.wing_taper_ratio_inboard,
                    cabin_l=self.fuselage.cabin_l,
                    position=self.position.translate('x', 0.48 * self.fuselage.cabin_l,
                                                     '-z', 0.40 * self.fuselage.cabin_d))

    @Part(parse=False)
    def right_winglet(self):
        if self.TYPE_winglet == 0:
            return CantedWinglet(name="Canted Winglet",
                                 airfoil_root=self.ct_airfoil_root,
                                 airfoil_tip=self.ct_airfoil_tip,
                                 chord_wingtip=self.right_wing.chords[2],
                                 chord_root_ratio=self.ct_chord_root_ratio,
                                 taper_ratio=self.ct_taper_ratio,
                                 wing_span=self.right_wing.wing_span / 2,
                                 height_ratio=self.ct_height_ratio,
                                 sweep=self.ct_sweep,
                                 cant=self.ct_cant,
                                 twist_tip=self.ct_twist_tip,
                                 position=self.right_wing.section_positions[2],
                                 avl_duplicate_pos=self.position,
                                 suppress=not self.winglet_ON)

        elif self.TYPE_winglet == 1:
            return WingtipFence(name="Wingtip Fence",
                                airfoil_up=self.wtf_airfoil_up,
                                airfoil_root=self.wtf_airfoil_root,
                                airfoil_down=self.wtf_airfoil_down,
                                chord_up=self.wtf_chord_up,
                                chord_root=self.wtf_chord_root,
                                chord_down=self.wtf_chord_down,
                                height_up=self.wtf_height_up,
                                height_down=self.wtf_height_down,
                                sweep_up=self.wtf_sweep_up,
                                sweep_down=self.wtf_sweep_down,
                                twist_up=self.wtf_twist_up,
                                twist_down=self.wtf_twist_down,
                                position=rotate(translate(self.right_wing.section_positions[2],
                                                          'x', self.right_wing.chords[2] - self.wtf_chord_root),
                                                'x', np.deg2rad(-90)),
                                avl_duplicate_pos=self.position,
                                suppress=not self.winglet_ON)

        elif self.TYPE_winglet == 2:
            return RakedWingtip(name="Raked Wingtip",
                                airfoil_start=self.rkt_airfoil_start,
                                airfoil_tip=self.rkt_airfoil_tip,
                                chord_start=self.right_wing.chords[2],
                                taper_ratio=self.rkt_taper_ratio,
                                wing_span=self.right_wing.wing_span / 2,
                                span_ratio=self.rkt_span_ratio,
                                sweep_le=self.rkt_sweep_le,
                                position=self.right_wing.section_positions[2],
                                avl_duplicate_pos=self.position,
                                suppress=not self.winglet_ON)

        elif self.TYPE_winglet == 3:
            return Sharklet(name="Sharklet",
                            airfoil_start=self.skt_airfoil_start,
                            airfoil_mid=self.skt_airfoil_mid,
                            airfoil_tip=self.skt_airfoil_tip,
                            # chord start = wing.chord_tip
                            chord_start=self.right_wing.chords[2],
                            chord_mid=self.skt_chord_mid,
                            K_lambda=self.skt_K_lambda,
                            wing_semi_span=self.right_wing.wing_span / 2,
                            height_ratio=self.skt_height_ratio,
                            KR=self.skt_KR,
                            cant=self.skt_cant,
                            sweep_le=self.skt_sweep_le,
                            sweep_transition_te=self.skt_sweep_transition_te,
                            twist=self.skt_twist,
                            dihedral=self.right_wing.wing_dihedral,
                            nu_blended_sections=self.skt_nu_blended_sections,
                            position=rotate(self.right_wing.section_positions[2],
                                            'x', np.deg2rad(self.right_wing.wing_dihedral)),
                            avl_duplicate_pos=self.position,
                            suppress=not self.winglet_ON)

    @Part
    def left_wing(self):
        return MirroredShape(shape_in=self.right_wing.solid,
                             reference_point=self.right_wing.position,
                             transparency=0,
                             vector1=self.right_wing.position.Vz,
                             vector2=self.right_wing.position.Vx,
                             mesh_deflection=0.0001)

    @Part
    def left_winglet(self):
        return MirroredShape(shape_in=self.right_winglet.surface,
                             reference_point=self.right_wing.position.point,
                             # Two vectors to define the mirror plane
                             vector1=self.right_wing.position.Vz,
                             vector2=self.right_wing.position.Vx,
                             suppress=not self.winglet_ON,
                             mesh_deflection=0.0001)

    @Part
    def vtp_wing(self):
        return VerticalTail(vtp_root_airfoil=self.vtp_root_airfoil,
                            vtp_tip_airfoil=self.vtp_tip_airfoil,
                            vtp_aspect_ratio=self.vtp_aspect_ratio,
                            vtp_sweep=self.vtp_sweep,
                            vtp_area=self.vtp_area,
                            htp_area=self.htp_right_wing.htp_area,
                            lh=self.htp_right_wing.lh,
                            Vh=self.htp_right_wing.Vh,
                            MAC_chord_length=self.right_wing.MAC_chord_length,
                            starting_point_mac=self.right_wing.starting_point_mac,
                            cabin_d=self.fuselage.cabin_d,
                            wing_span=self.right_wing.wing_span,
                            position=rotate90(self.position.translate('z', (0.48 * self.fuselage.cabin_d)),
                                              'x'),
                            color="blue")

    @Attribute
    def avl_surfaces(self):  # this scans the product tree and collect all instances of the avl.Surface class
        return self.find_children(lambda o: isinstance(o, avl.Surface))

    @Part
    def avl_configuration(self):
        return avl.Configuration(name='A320',
                                 reference_area=self.right_wing.wing_area_total,
                                 reference_span=self.right_wing.wing_span,
                                 reference_chord=self.right_wing.MAC_chord_length,
                                 reference_point=self.position.point,
                                 surfaces=self.avl_surfaces,
                                 mach=self.M_cruise)

    @Part
    def step_writer_components(self):
        return STEPWriter(default_directory=DIR,
                          trees=[self.fuselage,
                                 self.right_wing,
                                 self.right_winglet,
                                 self.left_wing,
                                 self.left_winglet,
                                 self.vtp_wing,
                                 self.htp_right_wing,
                                 self.htp_left_wing]
                          )

    @Part
    def avl_analysis(self):
        return AvlAnalysis(aircraft=[self.right_wing,
                                     self.right_winglet,
                                     self.left_wing,
                                     self.left_winglet],
                           altitude=9000,
                           TYPE_winglet=self.TYPE_winglet,
                           TYPE_wing_airfoil=self.TYPE_wing_airfoil,
                           configuration=self.avl_configuration,
                           case_settings=[('fixed_aoa', {'alpha': 3}),
                                          ('fixed_cl', {'alpha': avl.Parameter(name='alpha', value=0.5, setting='CL')})]
                           )

    @Part
    def xfoil_analysis(self):
        return XfoilAnalysis(lifting_surface=self.right_wing,
                             cutting_plane_span_fraction=self.cutting_plane_span_fraction,
                             flydir=self.flydir,
                             reynolds_number=self.reynolds_number,
                             alpha=self.alpha)


if __name__ == '__main__':
    from parapy.gui import display

    obj = Aircraft(label="Aircraft assembly")

    pdf = canvas.Canvas('myNewPdf.pdf')
    data = [['Aircraft Parameters', 'Initial Values', 'Final Values'], ['Fuselage Length (m)'], ['Cabin Diameter (m)'],
            ['Nose Slenderness Ratio'],
            ['Tail Slenderness Ratio'], ['Wing Quarter Chord Sweep (deg)'], ['Wing Dihedral (deg)'],
            ['Total Wing Area (sq. m)'],
            ['Cruise mach Number'], ['Wing Twist (deg)'], ['Wing Span (m)'], ['Wing Root Chord (m)'],
            ['Horizontal Tail Aspect Ratio'],
            ['Horizontal Tail Span (m)'], ['Horizontal Tail Sweep (deg)'], ['Horizontal Tail Arm (m)'],
            ['Horizontal Tail Root Chord (m)'],
            ['Horizontal Tail Taper Ratio'], ['Horizontal Tail Area (sq. m)'], ['Horizontal Tail Dihedral (deg)'],
            ['Vertical Tail Taper Ratio'], ['Vertical Tail Span (m)'], ['Vertical Tail Arm (m)'],
            ['Vertical Tail Sweep (deg)'],
            ['Vertical Tail Aspect Ratio'], ['Vertical Tail Area (sq. m)']]

    entireFuselage = obj.fuselage
    rightWing = obj.right_wing
    leftWing = obj.left_wing
    rightWinglet = obj.right_winglet
    leftWinglet = obj.left_winglet
    horizTailRight = obj.htp_right_wing
    horizTailLeft = obj.htp_left_wing
    verticalTail = obj.vtp_wing

    # fuselage
    entireAirplane = [entireFuselage.Cabin, entireFuselage.Nose, entireFuselage.fuselage_tail,
                      rightWing.solid, leftWing, rightWinglet.surface, leftWinglet, horizTailRight.solid,
                      horizTailLeft, verticalTail.solid]

    img = image.Image(shapes=entireAirplane, width=1920, height=1080)
    img.write('A320_isometric.jpg')

    camera_top = image.MinimalCamera(viewing_center=Point(0, 0, 0),
                                     eye_location=Point(0, 0, 10),
                                     up_direction=Vector(0, 1, 0),
                                     scale=10, aspect_ratio=1.5)

    img1 = image.Image(shapes=entireAirplane, camera=camera_top, height=1080)
    img1.write('A320_top.jpg')

    camera_left = image.MinimalCamera(viewing_center=Point(0, 90, 0),
                                      eye_location=Point(0, 0, 10),
                                      up_direction=Vector(0, 1, 0),
                                      scale=40, aspect_ratio=2)

    img2 = image.Image(shapes=entireAirplane, camera=camera_left, height=1080)
    img2.write('A320_side.jpg')

    camera_back = image.MinimalCamera(viewing_center=Point(-90, 0, 0),
                                      eye_location=Point(0, 0, 10),
                                      up_direction=Vector(0, 0, 1),
                                      scale=30, aspect_ratio=2)

    img3 = image.Image(shapes=entireAirplane, camera=camera_back, height=1080)
    img3.write('A320_back.jpg')

    pointOfFocus = [rightWing.solid, leftWing, rightWinglet.surface, leftWinglet]

    img4 = image.Image(shapes=pointOfFocus, width=1920, height=1080)
    img4.write('full_wing_isometric_initial.jpg')

    image_4 = image.Image(shapes=pointOfFocus, view='top', width=400, height=400)
    image_4.write('new_file.jpg')

    camera_top1 = image.MinimalCamera(viewing_center=Point(0, 0, 0),
                                      eye_location=Point(0, 0, 10),
                                      up_direction=Vector(0, 1, 0),
                                      scale=40, aspect_ratio=2)

    img5 = image.Image(shapes=pointOfFocus, camera=camera_top1, height=1080)
    img5.write('full_wing_top.jpg')

    camera_back1 = image.MinimalCamera(viewing_center=Point(-90, 0, 0),
                                       eye_location=Point(0, 0, 10),
                                       up_direction=Vector(0, 0, 1),
                                       scale=30, aspect_ratio=2)

    img6 = image.Image(shapes=pointOfFocus, camera=camera_back1, height=1080)
    img6.write('full_wing_back.jpg')

    data[1].append(str(entireFuselage.fuselage_length))
    data[2].append(str(entireFuselage.cabin_d))
    data[3].append(str(entireFuselage.ln_d))
    data[4].append(str(entireFuselage.lt_d))
    data[5].append(str(rightWing.wing_sweep_025c))
    data[6].append(str(rightWing.wing_dihedral))
    data[7].append(str(rightWing.wing_area_total))
    data[8].append(str(rightWing.M_cruise))
    data[9].append(str(rightWing.twist))
    data[10].append(str(rightWing.wing_span))
    data[11].append(str(rightWing.wing_c_root))
    data[12].append(str(horizTailRight.htp_aspect))
    data[13].append(str(horizTailRight.htp_span))
    data[14].append(str(horizTailRight.htp_sweep))
    data[15].append(str(horizTailRight.lh))
    data[16].append(str(horizTailRight.htp_c_root))
    data[17].append(str(horizTailRight.htp_taper))
    data[18].append(str(horizTailRight.htp_area))
    data[19].append(str(horizTailRight.htp_dihedral))
    data[20].append(str(verticalTail.vtp_taper))
    data[21].append(str(verticalTail.vtp_span))
    data[22].append(str(verticalTail.vtp_tailarm))
    data[23].append(str(verticalTail.vtp_sweep))
    data[24].append(str(verticalTail.vtp_aspect_ratio))
    data[25].append(str(verticalTail.vtp_area))

    display(obj)

    entireFuselageNew = obj.fuselage
    rightWingNew = obj.right_wing
    leftWingNew = obj.left_wing
    rightWingletNew = obj.right_winglet
    leftWingletNew = obj.left_winglet
    horizTailRightNew = obj.htp_right_wing
    horizTailLeftNew = obj.htp_left_wing
    verticalTailNew = obj.vtp_wing

    # fuselage
    entireAirplaneNew = [entireFuselageNew.Cabin, entireFuselageNew.Nose, entireFuselageNew.fuselage_tail,
                         rightWingNew.solid, leftWingNew, rightWingletNew.surface, leftWingletNew,
                         horizTailRightNew.solid, horizTailLeftNew, verticalTailNew.solid]

    camera = image.MinimalCamera(viewing_center=Point(0, 0, 0),
                                 eye_location=Point(0, 0, 10),
                                 up_direction=Vector(0, 1, 0),
                                 scale=40, aspect_ratio=1)

    img1 = image.Image(shapes=entireAirplane, camera=camera, height=1080)
    img1.write('full_aircraft.jpg')

    data[1].append(str(entireFuselageNew.fuselage_length))
    data[2].append(str(entireFuselageNew.cabin_d))
    data[3].append(str(entireFuselageNew.ln_d))
    data[4].append(str(entireFuselageNew.lt_d))
    data[5].append(str(rightWingNew.wing_sweep_025c))
    data[6].append(str(rightWingNew.wing_dihedral))
    data[7].append(str(rightWingNew.wing_area_total))
    data[8].append(str(rightWingNew.M_cruise))
    data[9].append(str(rightWingNew.twist))
    data[10].append(str(rightWingNew.wing_span))
    data[11].append(str(rightWingNew.wing_c_root))
    data[12].append(str(horizTailRightNew.htp_aspect))
    data[13].append(str(horizTailRightNew.htp_span))
    data[14].append(str(horizTailRightNew.htp_sweep))
    data[15].append(str(horizTailRightNew.lh))
    data[16].append(str(horizTailRightNew.htp_c_root))
    data[17].append(str(horizTailRightNew.htp_taper))
    data[18].append(str(horizTailRightNew.htp_area))
    data[19].append(str(horizTailRightNew.htp_dihedral))
    data[20].append(str(verticalTailNew.vtp_taper))
    data[21].append(str(verticalTailNew.vtp_span))
    data[22].append(str(verticalTailNew.vtp_tailarm))
    data[23].append(str(verticalTailNew.vtp_sweep))
    data[24].append(str(verticalTailNew.vtp_aspect_ratio))
    data[25].append(str(verticalTailNew.vtp_area))

    pdf.setFont('Courier', 20)
    pdf.drawCentredString(100, 800, 'KBE Project Report (Team-13)')
    #pdf.drawString(200, 700, str(entireFuselage.cabin_d))

    pdf.setFont('Courier', 15)

    table = Table(data)
    style = TableStyle([
        ('background', (0, 0), (2, 0), colors.green),
        ('color', (0, 0), (-1, 0), colors.whitesmoke),
        ('alignment', (0, 0), (-1, -1), 'CENTER'),
    ])
    table.wrapOn(pdf, 20, 20)
    table.drawOn(pdf, 100, 100)

    pdf.showPage()
    pdf.drawInlineImage('new_file.jpg', 10, 10)

    pdf.save()
