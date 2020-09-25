import stormpy
from unfolder import unfold
from locelim.datastructures import PCFP


# There seems to be a problem when modifying a jani model in stormpy and then building it.
# Exporting to json and parsing again may help.
def export_and_parse_jani(jani_model):
    with open("model.jani", "w") as f:
        f.write(str(jani_model))
    jani_model, _ = stormpy.parse_jani_model("model.jani")
    return jani_model

def main():
    path = "locelim/examples/coin_game_with_ints.prism"

    prism_program: stormpy.PrismProgram = stormpy.parse_prism_program(path)
    prism_props: stormpy.core.Property = stormpy.parse_properties_for_prism_program("P=? [F x>=20]", prism_program)

    jani_model: stormpy.JaniModel
    jani_props: stormpy.core.Property
    jani_model, jani_props = prism_program.to_jani(prism_props)

    pcfp = PCFP.PCFP.from_jani(jani_model)

    unfolded_pcfp = unfold(pcfp, jani_model, ["f", "x"])

    new_jani = unfolded_pcfp.to_jani()
    new_model = stormpy.build_model(new_jani)
    print(new_model)


def build_test_automaton(expression_manager: stormpy.ExpressionManager, initial_state: int) -> stormpy.JaniAutomaton:
    location_var: stormpy.Variable = expression_manager.create_integer_variable("locvar_" + str(initial_state))
    automaton: stormpy.JaniAutomaton = stormpy.JaniAutomaton("Test", location_var)

    for i in range(3):
        location = stormpy.JaniLocation("loc_" + str(i), stormpy.JaniOrderedAssignments([]))
        automaton.add_location(location)

    # This seems to be ignored. The final markov chain is evaluated starting at location loc_0
    # Because loc_0 has no outgoing transitions, the result is a markov chain with a single state
    automaton.add_initial_location(initial_state)

    template_edge: stormpy.JaniTemplateEdge = stormpy.JaniTemplateEdge(expression_manager.create_boolean(True))
    destination_indices_and_probabilities: [(int, stormpy.Expression)] = [
        (0, expression_manager.create_rational(stormpy.pycarl.gmp.Rational(0.5))),
        (1, expression_manager.create_rational(stormpy.pycarl.gmp.Rational(0.25))),
        (2, expression_manager.create_rational(stormpy.pycarl.gmp.Rational(0.25)))
    ]

    template_edge_destination: stormpy.JaniTemplateEdgeDestination = stormpy.JaniTemplateEdgeDestination(stormpy.JaniOrderedAssignments([]))
    template_edge.add_destination(template_edge_destination)
    template_edge.add_destination(template_edge_destination)  # Reusing the same object doesn't seem to cause issues
    template_edge.add_destination(template_edge_destination)

    edge: stormpy.JaniEdge = stormpy.JaniEdge(initial_state, 0, None, template_edge, destination_indices_and_probabilities)

    automaton.add_edge(edge)

    return automaton


def print_dtmc(model: stormpy.SparseDtmc):
    print(model)

    for state in model.states:
        for action in state.actions:
            for transition in action.transitions:
                print("From state {}, with probability {}, go to state {}".format(state, transition.value(), transition.column))
    print("")

if __name__ == '__main__':
    main()