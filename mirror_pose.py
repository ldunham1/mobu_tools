import pyfbsdk
import pyfbsdk_additions

# Python 2/3 compat
try:
    from contextlib import ContextDecorator
except ImportError:
    from functools import wraps

    class ContextDecorator(object):
        """contextlib.ContextDecorator backport."""
        def __call__(self, func):
            @wraps(func)
            def decorated(*args, **kwargs):
                with self:
                    return func(*args, **kwargs)
            return decorated


# ------------------------------------------------------------------------------
lapp = pyfbsdk.FBApplication()
lsys = pyfbsdk.FBSystem()
lplayer = pyfbsdk.FBPlayerControl()
lundo = pyfbsdk.FBUndoManager()


# ------------------------------------------------------------------------------
class SuspendRefresh(ContextDecorator):

    def __enter__(self):
        pyfbsdk.FBBeginChangeAllModels()

    def __exit__(self, exc_type, exc_val, exc_tb):
        pyfbsdk.FBEndChangeAllModels()
        return False


# ------------------------------------------------------------------------------
def get_mirror_name(name):
    if 'Left' in name:
        return name.replace('Left', 'Right')
    elif 'Right' in name:
        return name.replace('Right', 'Left')
    else:
        return name


@SuspendRefresh()
def select(name_list, add=False):
    if not isinstance(name_list, (list, tuple, set)):
        name_list = [name_list]

    for comp in lsys.Scene.Components:
        comp_name = getattr(comp, 'LongName', comp.Name)
        if comp_name in name_list:
            comp.Selected = True
            name_list.remove(comp_name)
        elif not add:
            comp.Selected = False


def selected():
    ordered_selected_models = pyfbsdk.FBModelList()
    pyfbsdk.FBGetSelectedModels(
        ordered_selected_models,
        None,  # Search all models, not just a particular branch
        True,  # Get selected (not deselected)
        True,  # Keep selection order
    )
    return ordered_selected_models


# ------------------------------------------------------------------------------
@SuspendRefresh()
def mirror_current_character(character):
    lundo.TransactionBegin('mirror_current_character({})'.format(character))

    try:
        current_pose = pyfbsdk.FBCharacterPose('_TMP_mirror_pose')
        current_pose.CopyPose(character)

        pose_options = pyfbsdk.FBCharacterPoseOptions()
        pose_options.mCharacterPoseKeyingMode = pyfbsdk.FBCharacterPoseKeyingMode.kFBCharacterPoseKeyingModeBodyPart
        pose_options.SetFlag(pyfbsdk.FBCharacterPoseFlag.kFBCharacterPoseMirror, True)
        character.SelectModels(True, False, True, False)

        for model in selected():
            lundo.TransactionAddModelTRS(model)

        current_pose.PastePose(character, pose_options)
        lsys.Scene.Evaluate()

        lplayer.Key()

        current_pose.FBDelete()
        lsys.Scene.Evaluate()

    finally:
        lundo.TransactionEnd()


@SuspendRefresh()
def mirror_current_selection(character):
    lundo.TransactionBegin('mirror_current_selection({})'.format(character))

    current_pose = pyfbsdk.FBCharacterPose('_TMP_mirror_pose')
    current_pose.CopyPose(character)

    pose_options = pyfbsdk.FBCharacterPoseOptions()
    pose_options.mCharacterPoseKeyingMode = pyfbsdk.FBCharacterPoseKeyingMode.kFBCharacterPoseKeyingModeBodyPart
    pose_options.SetFlag(pyfbsdk.FBCharacterPoseFlag.kFBCharacterPoseMirror, True)

    # Select mirror
    mirror_names = [
        get_mirror_name(model.LongName)
        for model in selected()
    ]
    select(mirror_names)
    for model in selected():
        lundo.TransactionAddModelTRS(model)

    current_pose.PastePose(character, pose_options)
    lsys.Scene.Evaluate()

    lplayer.Key()

    current_pose.FBDelete()
    lsys.Scene.Evaluate()

    lundo.TransactionEnd()


# ------------------------------------------------------------------------------
def create_tool(tool_name):

    def action_mirror_character(control, event):
        mirror_current_character(lapp.CurrentCharacter)

    def action_mirror_selection(control, event):
        mirror_current_selection(lapp.CurrentCharacter)

    tool = pyfbsdk_additions.FBCreateUniqueTool(tool_name)

    # initial settings
    tool.StartSizeX = 80
    tool.StartSizeY = 160

    # value label
    x = pyfbsdk.FBAddRegionParam(0, pyfbsdk.FBAttachType.kFBAttachLeft, "")
    y = pyfbsdk.FBAddRegionParam(5, pyfbsdk.FBAttachType.kFBAttachTop, "")
    w = pyfbsdk.FBAddRegionParam(0, pyfbsdk.FBAttachType.kFBAttachRight, "")
    h = pyfbsdk.FBAddRegionParam(20, pyfbsdk.FBAttachType.kFBAttachBottom, "")
    tool.AddRegion("button_layout", "button_layout", x, y, w, h)

    button_layout = pyfbsdk_additions.FBVBoxLayout()
    tool.SetControl("button_layout", button_layout)

    tool.mirrorCharacterBtn = pyfbsdk.FBButton()
    tool.mirrorCharacterBtn.Caption = 'Character'
    tool.mirrorCharacterBtn.Hint = "Character: Mirror the current Character's pose."
    tool.mirrorCharacterBtn.OnClick.Add(action_mirror_character)
    button_layout.Add(tool.mirrorCharacterBtn, 50, space=5, height=20)

    tool.mirrorSelectionBtn = pyfbsdk.FBButton()
    tool.mirrorSelectionBtn.Caption = 'Selection'
    tool.mirrorSelectionBtn.Hint = "Selection: Mirror the current Character's selected controls."
    tool.mirrorSelectionBtn.OnClick.Add(action_mirror_selection)
    button_layout.Add(tool.mirrorSelectionBtn, 50, space=5, height=20)

    return tool


# ------------------------------------------------------------------------------
if __name__ in ['__main__', '__builtin__']:
    tool_name = 'Mirror Current Pose'
    tool = create_tool(tool_name)


# MIT License
#
# Copyright (c) 2021 Lee Dunham
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
