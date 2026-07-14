from .state import DPP14State


CONTACTS = ("candidate", "source", "provider", "runtime", "platform", "command", "target", "harness", "expectation", "normal", "incident", "ast", "rollback", "proof")


def decompose_contacts(state: DPP14State) -> DPP14State:
    state.frozen_frame["contacts"] = {name: state.frozen_frame.get(name) for name in CONTACTS}
    state.trace.append({"transition": "DecomposeContacts", "status": "PASS", "contact_count": 14})
    return state
