from core.constants import *
from core import Container
from core.widgets import Pump, Tank, PumpFlow, Simpletext, Frame
from plugins.abstract import AbstractPlugin


class Resman(AbstractPlugin):
    def __init__(self, taskplacement='bottommid', taskupdatetime=2000):
        super().__init__(taskplacement, taskupdatetime)

        new_par = dict(automaticsolver=False, displayautomationstate=True, pumpcoloroff=C['WHITE'],
                       pumpcoloron=C['GREEN'], pumpcolorfailure=C['RED'], toleranceradius=250,
                       statuslocation='bottomright', displaystatus=True,
                       tolerancecolor=C['BLACK'], tolerancecoloroutside=C['BLACK'],

                        tank=dict(a=dict(level=2500, max=4000, target=2500, depletable=True,
                                         lossperminute=800, _infoside='left'),
                                  b=dict(level=2500, max=4000, target=2500, depletable=True,
                                         lossperminute=800, _infoside='right'),
                                  c=dict(level=1000, max=2000, target=None, depletable=True,
                                         lossperminute=0, _infoside='left'),
                                  d=dict(level=1000, max=2000, target=None, depletable=False,
                                         lossperminute=0, _infoside='left'),
                                  e=dict(level=3000, max=4000, target=None, depletable=False,
                                         lossperminute=0, _infoside='right'),
                                  f=dict(level=3000, max=4000, target=None, depletable=True,
                                         lossperminute=0, _infoside='right')),

                        pump=dict([
                           ('1', dict(flow=800, state='off', key='NUM_1', _fromtank='c', _totank='a')),
                           ('2', dict(flow=600, state='off', key='NUM_2', _fromtank='e', _totank='a')),
                           ('3', dict(flow=800, state='off', key='NUM_3', _fromtank='d', _totank='b')),
                           ('4', dict(flow=600, state='off', key='NUM_4', _fromtank='f', _totank='b')),
                           ('5', dict(flow=600, state='off', key='NUM_5', _fromtank='e', _totank='c')),
                           ('6', dict(flow=600, state='off', key='NUM_6', _fromtank='d', _totank='f')),
                           ('7', dict(flow=400, state='off', key='NUM_7', _fromtank='a', _totank='b')),
                           ('8', dict(flow=400, state='off', key='NUM_8', _fromtank='b', _totank='a'))
                           ]
                        )
                   )


        self.parameters.update(new_par)
        self.automode_position = (0.48, 0.55)
        self.wait_before_leak = 1  # How many updates to wait before the leak begins

        # Add response timers to target tanks, and an is_in_tolerance information
        for tank_letter, this_tank in self.parameters['tank'].items():
            if this_tank['target'] is not None:
                tank = self.parameters['tank'][tank_letter]
                tank['_response_time'] = 0
                tank['_is_in_tolerance'] = None
                tank['_tolerance_color'] = self.parameters['tolerancecolor']


    def show(self):
        super().show()
        if self.parameters['displaystatus']:
            if self.get_widget('status_foreground') is not None:
                self.get_widget('status_foreground').set_visibility(False)


    def hide(self):
        super().hide()
        if self.parameters['displaystatus']:
            if self.get_widget('status_foreground') is not None:
                self.get_widget('status_foreground').set_visibility(True)


    def get_response_timers(self):
        return [t['_response_time'] for l, t in self.parameters['tank'].items() if t['target'] is not None]


    def create_widgets(self):
        super().create_widgets()

        # Compute tank widgets container
        h = 0.35 * self.task_container.h      # Tank height
        small, medium, large = (x*self.task_container.w for x in [0.1, 0.12, 0.15]) # Tank widths
        lower_y = self.task_container.b + 0.15 * self.task_container.h   # Bottom tank anchors
        upper_y = self.task_container.b + 0.55 * self.task_container.h

        # Tank left coordinates proportion
        l_prop_dict = dict(a=0.14, b=0.64, c=0.05, d=0.55, e=0.3, f=0.8)
        l_coord_dict = {k:self.task_container.l + self.task_container.w * v for k, v in l_prop_dict.items()}

        tank_container_dict = dict(
                          a=Container(name='Sup-G', l=l_coord_dict['a'], b=upper_y, w=large,  h=h),
                          b=Container(name='Sup-D', l=l_coord_dict['b'], b=upper_y, w=large,  h=h),
                          c=Container(name='Ext-G', l=l_coord_dict['c'], b=lower_y, w=small,  h=h),
                          d=Container(name='Int-D', l=l_coord_dict['d'], b=lower_y, w=small,  h=h),
                          e=Container(name='Int-G', l=l_coord_dict['e'], b=lower_y, w=medium, h=h),
                          f=Container(name='Ext-D', l=l_coord_dict['f'], b=lower_y, w=medium, h=h)
                        )

        # The pump status are managed from Resman
        if self.parameters['displaystatus'] is True:
            # Get the pump status container
            pthp = PLUGIN_TITLE_HEIGHT_PROPORTION
            status_container = self.win.get_container(self.parameters['statuslocation'])
            status_title_container = status_container.reduce_and_translate(height=pthp,   y=1)
            status_task_container  = status_container.reduce_and_translate(height=1-pthp, y=0)

            # Add statuslocation foreground in case it is displayed
            self.add_widget('status_foreground', Frame, status_task_container,
                            fill_color=C['BACKGROUND'], draw_order=15)

            # Add the pump status title
            self.add_widget('status_title', Simpletext, container=status_title_container,
                           text=_('Pump status').upper(),
                           font_size=F['MEDIUM'], color=C['WHITE'])

            # Add pump flows
            for pump_number, this_pump in self.parameters['pump'].items():
                pos = int(pump_number) - 1
                flow_container = Container(f'pump_{pump_number}', status_container.l,
                                           status_container.b + status_container.h * (0.8 - 0.1 * pos),
                                           status_container.w, status_container.h * 0.1)

                this_pump['statuswidget'] = self.add_widget(f"pump_{pump_number}_flow", PumpFlow,
                                                           container=flow_container, label=pump_number,
                                                           flow=this_pump['flow'])

        tanks = self.parameters['tank']
        for tank_letter, this_tank in tanks.items():
            fluid_label = str(this_tank['level']) if this_tank['depletable'] else str()
            this_tank['widget'] = self.add_widget(f'tank_{tank_letter}', Tank,
                                                 container=tank_container_dict[tank_letter],
                                                 letter=tank_container_dict[tank_letter].name,
                                                 level=this_tank['level'],
                                                 fluid_label = fluid_label,
                                                 level_max=this_tank['max'],
                                                 target=this_tank['target'],
                                                 toleranceradius=self.parameters['toleranceradius'],
                                                 infoside=this_tank['_infoside'])


        for pump_number, this_pump in self.parameters['pump'].items():
            from_cont = tanks[this_pump['_fromtank']]['widget'].container
            to_cont = tanks[this_pump['_totank']]['widget'].container
            y_offset = 0.055*self.task_container.h if pump_number == '7' else 0  # Raise the 7th pump
            pump_width = 0.028 * self.task_container.w

            # Pump is not specified by a container (None), but by two containers (from-to)
            this_pump['widget'] = self.add_widget(f'pump_{pump_number}', Pump, container=None,
                                                 from_cont=from_cont,
                                                 to_cont=to_cont, pump_n=pump_number,
                                                 color=self.parameters['pumpcoloroff'],
                                                 pump_width=pump_width,
                                                 y_offset=y_offset)


    def compute_next_plugin_state(self):
        if super().compute_next_plugin_state() == 0:
            return
        
        tanks = self.parameters['tank']
        pumps = self.parameters['pump']
        time_resolution = (self.parameters['taskupdatetime'] / 1000) / 60.

        # 0. Compute automatic actions if heuristicsolver activated, three heuristics
        # Browse only woorking pumps (state != -1)

        if self.wait_before_leak > 0:
            self.wait_before_leak -= 1
        else:
            if self.parameters['automaticsolver'] is True:
                for pump_n, this_pump in {p: v for p, v in pumps.items() if v['state'] != 'failure'}.items():
                    from_tank, to_tank = tanks[this_pump['_fromtank']], tanks[this_pump['_totank']]

                    # 0.1. Systematically activate pumps draining non-depletable tanks
                    if not from_tank['depletable'] and this_pump['state'] == 'off':
                        this_pump['state'] = 'on'

                    # 0.2. Activate/deactivate pump whose target tank is too low/high
                    # "Too" means level is out of a tolerance zone around the target level (2500 +/- 150)
                    if to_tank['target'] is not None:
                        if to_tank['level'] <= to_tank['target'] - 50:
                            this_pump['state'] = 'on'
                        elif to_tank['level'] >= to_tank['target'] + 50:
                            this_pump['state'] = 'off'

                    # 0.3. Equilibrate between the two A/B tanks if sufficient level
                    if from_tank['target'] is not None and to_tank['target'] is not None:
                        if from_tank['level'] >= to_tank['target'] >= to_tank['level']:
                            this_pump['state'] = 'on'
                        else:
                            this_pump['state'] = 'off'

            for _, this_tank in tanks.items():           # 1. Deplete target tanks
                if this_tank['target'] is not None:
                    this_tank['level'] -= min(int(this_tank['lossperminute'] *  time_resolution), this_tank['level'])

            for pump_n, this_pump in pumps.items():      # 2. For each pump
                if this_pump['state'] == 'on':           # 2.a Transfer flow if pump is ON
                    fromtank, totank = tanks[this_pump['_fromtank']], tanks[this_pump['_totank']]

                                                    # Compute (available) volume
                    volume = min(int(this_pump['flow']) * time_resolution, fromtank['level'])

                    if fromtank['depletable']:      # Drain it from tank (if its capacity is limited)...
                        fromtank['level'] -= int(volume)

                                                    # ...to tank (if it's not full)
                    totank['level'] += min(int(volume), totank['max'] - totank['level'])

        # The following is always executed (independent on wait_before_leak)
        for tank_l, this_tank in tanks.items():      # 3. For each tank
            pumps_to_deactivate = []

            if this_tank['level'] >= this_tank['max']:    # If it is full, select incoming pumps for deactivation
                pumps_to_deactivate.extend([v for p, v in pumps.items() if v['_totank'] == tank_l])

            elif this_tank['level'] <= 0:            # Likewise, if it is empty, select outcome
                                                     # pumps for deactivation
                pumps_to_deactivate.extend([v for p, v in pumps.items() if v['_fromtank'] == tank_l])

            for this_pump in pumps_to_deactivate:    # Deactivate selected pumps if not on failure
                if not this_pump['state'] == 'failure':
                    this_pump['state'] = 'off'


            if this_tank['target'] is not None:      # Record performance for target tanks
                t, r = this_tank['target'], self.parameters['toleranceradius']
                this_tank['_is_in_tolerance'] = float('nan')
                if r > 0:  # If a tolerance level is defined
                    this_tank['_is_in_tolerance'] = t - r <= this_tank['level'] <= t + r
                    tolerance_color = self.parameters['tolerancecolor']
                    if not this_tank['_is_in_tolerance']:  # If a response is needed
                        tolerance_color = self.parameters['tolerancecoloroutside']
                        this_tank['_response_time'] += self.parameters['taskupdatetime']
                    elif this_tank['_response_time'] > 0:  # Back in the tolerance zone
                        self.log_performance(f'{tank_l}_response_time', this_tank['_response_time'])
                        this_tank['_response_time'] = 0
                    this_tank['_tolerance_color'] = tolerance_color

                deviation = this_tank['level'] - this_tank['target']
                self.log_performance(f'{tank_l}_in_tolerance', this_tank['_is_in_tolerance'])
                self.log_performance(f'{tank_l}_deviation', deviation)


    def refresh_widgets(self):
        if super().refresh_widgets() == 0:
            return
        tanks = self.parameters['tank']
        pumps = self.parameters['pump']

        for _, this_pump in pumps.items():           # 4. Refresh visual information
            this_pump['widget'].set_color(self.parameters[f"pumpcolor{this_pump['state']}"])

            if this_pump['state'] == 'on':
                this_pump['statuswidget'].set_flow(str(this_pump['flow']))
            else:  # failure || off
                this_pump['statuswidget'].set_flow(str(0))

        for tank_letter, this_tank in tanks.items():
            this_tank['widget'].set_fluid_level(this_tank['level'], this_tank['max'])
            fluid_label = str(this_tank['level']) if this_tank['depletable'] == True else ''
            this_tank['widget'].set_fluid_label(fluid_label)

            # Apply modification that are specific to target tanks
            # a.    Is there a need to refresh the tolerance radius ?
            if this_tank['target'] is not None: # Check only target tanks
                this_tank['widget'].set_tolerance_radius(self.parameters['toleranceradius'],
                                                         this_tank['target'], this_tank['max'])

            # b.    Is there a need to change the tolerance color ?
                this_tank['widget'].set_tolerance_color(this_tank['_tolerance_color'])


    def get_pump_by_key(self, key):
        pump = [p for _, p in self.parameters['pump'].items() if p['key'] == key]
        if len(pump) > 0:
            return pump[0]


    def do_on_key(self, key, state):
        super().do_on_key(key, state)
        if key is None:
            return

        if state == 'press':
            pump_key = self.get_pump_by_key(key)
            if pump_key['state'] != 'failure':
                pump_key['state'] = 'on' if pump_key['state'] == 'off' else 'off'
