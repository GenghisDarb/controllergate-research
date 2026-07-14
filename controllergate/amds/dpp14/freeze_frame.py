from copy import deepcopy
from controllergate.state.integrity import canonical_hash
from .state import DPP14State


def freeze_frame(state: DPP14State) -> DPP14State:
    state.frozen_frame = deepcopy(state.frozen_frame)
    state.frozen_frame["frame_hash"] = canonical_hash(state.frozen_frame)
    state.trace.append({"transition": "FreezeFrame", "status": "PASS", "frame_hash": state.frozen_frame["frame_hash"]})
    return state
