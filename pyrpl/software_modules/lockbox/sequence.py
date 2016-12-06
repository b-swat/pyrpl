from pyrpl.attributes import SelectProperty, FloatProperty, BoolProperty, DynamicSelectProperty, StringProperty, \
                            ListStageOuputProperty
from pyrpl.modules import SoftwareModule
from pyrpl.widgets.module_widgets import LockboxSequenceWidget, LockboxStageWidget


from collections import OrderedDict

class Sequence(SoftwareModule):
    widget_class = LockboxSequenceWidget
    section_name = 'sequence'

    def init_module(self):
        self.stages = []

    def add_stage(self):
        """
        Stages can be added at will.
        """
        print('adding stage')
        stage = Stage(self)
        stage.update_inputs()
        stage.update_outputs()
        stage.name = "stage" + str(len(self.stages) + 1)
        self.stages.append(stage)
        setattr(self, stage.name, stage)
        # self.__class__.default_sweep_output.change_options([output.name for output in self.outputs])
        if self.widget is not None:
            self.widget.add_stage(stage)
        return stage

    def rename_stage(self, stage, new_name):
        if hasattr(self, stage.name):
            delattr(self, stage.name)
        setattr(self, new_name, stage)
        if stage._autosave_active:
            stage.c._rename(new_name)
        stage._name = new_name
        self.update_stage_names()

    def update_stage_names(self):
        if self.widget is not None:
            self.widget.update_stage_names()

    def remove_stage(self, stage):
        self.stages.remove(stage)
        if "stages" in self.c._keys():
            if stage.name in self.c.stages._keys():
                self.c.stages._pop(stage.name)
        if stage.widget is not None:
            self.widget.remove_stage(stage)

    def remove_all_stages(self):
        to_remove = [] # never iterate on a list that s being deleted
        for stage in self.stages:
            to_remove.append(stage)
        for stage in to_remove:
            self.remove_stage(stage)

    def load_setup_attributes(self):
        if self.c is not None:
            if 'stages' in self.c._dict.keys():
                for name, output in self.c.stages._dict.items():
                    if name!='states':
                        stage = self.add_stage()
                        stage._autosave_active = False
                        self.rename_stage(stage, name)
                        stage.load_setup_attributes()
                        stage._autosave_active = True

    def save_state(self, name, state_section=None):
        if state_section is None:
            state_section = self.c_states
        state_section[name] = OrderedDict()

        for stage in self.stages:
            stage.save_state(stage.name, getattr(state_section, name))

    def load_state(self, name, state_section=None):
        if state_section is None:
            state_section = self.c_states
        self.remove_all_stages()
        for stage_section in state_section[name].values():
            stage = self.add_stage()
            stage._autosave_active = False
            stage.set_setup_attributes(**stage_section)
            stage._autosave_active = True

    def update_outputs(self):
        for stage in self.stages:
            stage.update_outputs()

    def update_inputs(self):
        for stage in self.stages:
            stage.update_inputs()

class StageNameProperty(StringProperty):
    def set_value(self, obj, val):
        if obj.parent is not None:
            obj.parent.rename_stage(obj, val)
        else:
            super(StageNameProperty, self).set_value(obj, val)





class Stage(SoftwareModule):
    """
    A stage is a single step in the lock acquisition process
    """
    gui_attributes = ['name',
                      'input',
                      'variable_value',
                      'output_on',
                      'duration',
                      'function_call']
    setup_attributes = gui_attributes
    section_name = 'stage'
    name = StageNameProperty(default='my_stage')
    widget_class = LockboxStageWidget
    input = DynamicSelectProperty()
    output_on = ListStageOuputProperty()
    variable_value = FloatProperty()
    duration = FloatProperty()
    function_call = StringProperty()

    def init_module(self):
        self.lockbox = self.parent.parent
        self.update_inputs()
        self.update_outputs()

    def update_inputs(self):
        """
        Updates the list of possible inputs to be in sync with the existing inputs in the model
        """
        input_names = [input.name for input in self.lockbox.inputs]
        self.__class__.input.change_options(self, input_names)

    def update_outputs(self):
        """
        Updates the list of outputs to be in sync with the existing outputs in the lockbox
        """

        output_names = [output.name for output in self.lockbox.outputs]
        print('updating', output_names)
        new_output_on = dict()
        for name in output_names:
            if not name in self.output_on:
                new_output_on[name] = (True, False, 0)
            else:
                new_output_on[name] = self.output_on[name]
        print(new_output_on)
        self.output_on = new_output_on

    def set_setup_attributes(self, **kwds):
        try:
            super(Stage, self).set_setup_attributes(**kwds)
        finally:
            self.update_outputs()
            self.update_inputs()

    def _setup(self):
        """
        Setup the lockbox parameters according to this stage
        """
        pass