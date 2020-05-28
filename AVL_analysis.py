from kbeutils import avl
from parapy.gui import display
from full_aircraft import Aircraft
from parapy.core import *
from parapy.core.validate import *
from parapy.core.decorators import action
import matplotlib.pyplot as plt
import numpy as np
import warnings


class Avl_analysis(avl.Interface):

    aircraft = Input(in_tree=True)
    case_settings = Input()
    plot_which = Input('altitude')

    # TYPE_winglet and altitude will be passed to interface for warning evaluation
    @Input
    def TYPE_winglet(self):
        return self.aircraft.TYPE_winglet

    @Input
    # 1: 1000m,  2: 5000m, 3:9000m
    def altitude(self):
        return 3

    # TYPE_wing_airfoil will be passed to interface for plotting purposes
    # supercritical: 1, NACA-6: 2, Conventional: 3.
    @Input
    def TYPE_wing_airfoil(self):
        return self.aircraft.TYPE_wing_airfoil

    @Attribute
    def configuration(self):
        return self.aircraft.avl_configuration

    @Attribute
    # dynamic pressure
    def q(self):
        rho = [1.112, 0.736, 0.467]
        a = [336.4, 320.5, 303.8]
        if self.altitude == 1:
            q = 0.5 * rho[0] * (a[0] * float(self.configuration.mach))**2
        elif self.altitude == 2:
            q = 0.5 * rho[1] * (a[1] * float(self.configuration.mach))**2
        else:
            q = 0.5 * rho[2] * (a[2] * float(self.configuration.mach))**2

        right_wing = self.aircraft.right_wing

        with open("output.txt", "a") as file:
            file.write('Airfoil type\tWinglet type\tMach\tAltitude\tSweep 0.25c\t\tq\t'
                       'M_root(fix AoA)\t\tM_root(fix Cl)\n\t\t')
            file.write(str(self.TYPE_wing_airfoil))
            file.write('\t\t\t\t')
            file.write(str(self.TYPE_winglet))
            file.write("\t\t")
            file.write(str(self.configuration.mach))
            file.write("\t\t")
            file.write(str(4000*self.altitude-3000))
            file.write("\t\t")
            file.write(str(round(right_wing.wing_sweep_025c, 2)))
            file.write("\t")
            file.write(str(round(q, 2)))
            file.write("\t")

        return q

    @Part
    def cases(self):
        return avl.Case(quantify=len(self.case_settings),
                        name=self.case_settings[child.index][0],
                        settings=self.case_settings[child.index][1])

    @Attribute
    def l_over_d(self):
        return {case_name: result['Totals']['CLtot'] / result['Totals']['CDtot']
                for case_name, result in self.results.items()}

    @Attribute
    def CL(self):
        return {case_name: result['Totals']['CLtot']
                for case_name, result in self.results.items()}

    @Attribute
    def rootBendingMoment(self):
        wlt_names = ['Canted Winglet', 'Wingtip Fence', 'Raked Wingtip']
        wing_ccl = []
        wing_yle = []
        winglet_ccl = []
        winglet_yle = []
        for case_name, result in self.results.items():
            ccl = result['StripForces']['wing']['c cl']
            wing_ccl.append(ccl)
            yle = result['StripForces']['wing']['Yle']
            wing_yle.append(yle)
            for idx_name in range(len(wlt_names)):
                try:
                    name = wlt_names[idx_name]
                    ccl = result['StripForces'][name]['c cl']
                    winglet_ccl.append(ccl)
                    yle = result['StripForces'][name]['Yle']
                    winglet_yle.append(yle)
                    break
                except KeyError:
                    continue
        nu_wing_strips = int(len(wing_ccl[1]) / 2)
        nu_winglet_strips = int(len(winglet_ccl[1]) / 2)

        wing_ccl = np.array(wing_ccl)
        wing_ccl = wing_ccl[:, 0:nu_wing_strips]
        wing_yle = np.array(wing_yle)
        wing_yle = wing_yle[:, 0:nu_wing_strips]
        winglet_ccl = np.array(winglet_ccl)
        winglet_ccl = winglet_ccl[:, 0:nu_winglet_strips]
        winglet_yle = np.array(winglet_yle)
        winglet_yle = winglet_yle[:, 0:nu_winglet_strips]

        M_root_wing = np.zeros(len(self.results.items()))
        M_root_winglet = np.zeros(len(self.results.items()))
        for i in range(0, len(self.results.items())):
            if self.TYPE_winglet == 0:
                # canted winglet
                cant = self.aircraft.right_winglet.cant
            elif self.TYPE_winglet == 1:
                # wingtip fence
                cant = 0
            else:
                # raked wingtip, ignore dihedral
                cant = 90

            dy_wing = wing_yle[0, 3] - wing_yle[0, 2]
            dy_winglet = winglet_yle[0, 3] - winglet_yle[0, 2]
            Sf_wing = np.array(wing_ccl[i, :] * self.q * dy_wing)
            Sf_winglet = np.array(winglet_ccl[i, :] * self.q * dy_winglet)

            M_root_wing[i] = sum(np.multiply(Sf_wing, wing_yle[i, :]))
            M_root_winglet[i] = sum(np.multiply(Sf_winglet, winglet_yle[i, :]))

        M_root = M_root_wing + M_root_winglet

        file = open("output.txt", "a")
        for m in list(M_root):
            file.write(str(int(m)))
            file.write("\t\t\t")
        file.write("\n")
        file.close()

        return list(M_root)

    @Attribute
    def plot_M_root_bending(self):
        with open("output.txt", 'r+') as f:
            data = []
            count = 0
            for line in f:
                if count % 2 == 1:
                    temp = line.split('\t')
                    temp = [x for x in temp if x != '' and x != '\n']
                    data.append(temp)
                count = count + 1
            data = np.array(data)
            if self.plot_which == 'altitude':
                x_val = data[:, 3]
                plt.xlabel('altitude (m)')
            if self.plot_which == 'sweep':
                x_val = data[:, 4]
                plt.xlabel('sweep')
            y_val = data[:, 7]
            plt.plot(x_val, y_val)
            plt.ylabel('Root bending moment (Nm) at Cl=0.5')
            plt.show()
        return 'Plot done'


if __name__ == '__main__':
    obj = Aircraft(label="A320")
    # display(obj)

    cases = [('fixed_aoa', {'alpha': 3}),
             ('fixed_cl', {'alpha': avl.Parameter(name='alpha', value=0.5, setting='CL')})]

    analysis = Avl_analysis(aircraft=obj,
                            case_settings=cases)
    display(analysis)