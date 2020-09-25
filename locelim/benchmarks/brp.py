# manual analysis of brp benchmark


# // Probability that the sender does not report a successful transmission
# // (property 1 from [DJJL01])
# // RESULT (N=16,MAX=2): 4.2333344360436463E-4
# // RESULT (N=16,MAX=3): 1.2617766032502142E-5
# // RESULT (N=16,MAX=4): 3.760115852621381E-7
# // RESULT (N=16,MAX=5): 1.1205147161661327E-8
# // RESULT (N=32,MAX=2): 8.464876760601103E-4
# // RESULT (N=32,MAX=3): 2.523537283980547E-5
# // RESULT (N=32,MAX=4): 7.520230293559993E-7
# // RESULT (N=32,MAX=5): 2.2410294182907482E-8
# // RESULT (N=64,MAX=2): 0.0016922588104839984
# // RESULT (N=64,MAX=3): 5.047010884909582E-5
# // RESULT (N=64,MAX=4): 1.5040454930200707E-6
# // RESULT (N=64,MAX=5): 4.482058786183236E-8

# "p1": P=? [ F s=5 ];
# // Probability that the sender reports an uncertainty on the success of the transmission
# // (property 2 from [DJJL01])
# // RESULT (N=16,MAX=2): 2.6453089092093334E-5
# // RESULT (N=16,MAX=3): 7.886057122710931E-7
# // RESULT (N=16,MAX=4): 2.350071994489705E-8
# // RESULT (N=16,MAX=5): 7.003216933947301E-10
# // RESULT (N=32,MAX=2): 2.6441890629620753E-5
# // RESULT (N=32,MAX=3): 7.885957622036431E-7
# // RESULT (N=32,MAX=4): 2.35007110980951E-8
# // RESULT (N=32,MAX=5): 7.003216860351248E-10
# // RESULT (N=64,MAX=2): 2.641950789079939E-5
# // RESULT (N=64,MAX=3): 7.885758616123002E-7
# // RESULT (N=64,MAX=4): 2.3500693423534514E-8
# // RESULT (N=64,MAX=5): 7.003216702973405E-10
# "p2": P=? [ F s=5 & srep=2 ];

# // Probability that the receiver does not receive any chunk when the sender did try to send a chunk
# // (property 4 from [DJJL01])
# // RESULT (N=16,MAX=2): 8.000000000000001E-6
# // RESULT (N=16,MAX=3): 1.6000000000000003E-7
# // RESULT (N=16,MAX=4): 3.2000000000000005E-9
# // RESULT (N=16,MAX=5): 6.400000000000001E-11
# // RESULT (N=32,MAX=2): 8.000000000000001E-6
# // RESULT (N=32,MAX=3): 1.6000000000000003E-7
# // RESULT (N=32,MAX=4): 3.2000000000000005E-9
# // RESULT (N=32,MAX=5): 6.400000000000001E-11
# // RESULT (N=64,MAX=2): 8.000000000000001E-6
# // RESULT (N=64,MAX=3): 1.6000000000000003E-7
# // RESULT (N=64,MAX=4): 3.2000000000000005E-9
# // RESULT (N=64,MAX=5): 6.400000000000001E-11
# "p4": P=? [ F !(srep=0) & !recv ];

import stormpy as sp

from locelim.datastructures.PCFP import PCFP

# a small hack to print variables/expressions right
sp.storage.Variable.__repr__ = lambda self: self.name
sp.Expression.__repr__ = lambda self: str(self)


def transitions_count(model):
    res = 0
    for state in model.states:
        for action in state.actions:
            res += len(action.transitions)
    return res


def brp_manual_simplification():
    prism_program = sp.parse_prism_program("originals/brp.v1.prism")
    jani_model, jani_props = prism_program.to_jani([])
    jani_model = jani_model.flatten_composition()


    prism_program: sp.PrismProgram

    jani_model:sp.JaniModel
    mgr = jani_model.expression_manager
    N = jani_model.get_constant("N").expression_variable
    MAX = jani_model.get_constant("MAX").expression_variable

    constant_vals = [
        {N: mgr.create_integer(100), MAX: mgr.create_integer(100)}
    ]

    for constant_val in constant_vals:
        print(constant_val)
        property_str = "P=? [ F s=5 ]"
        property = sp.parse_properties_for_jani_model(property_str, jani_model)
        jani_model_const_def = jani_model.define_constants(constant_val)
        model = sp.build_model(jani_model_const_def, property)
        result = sp.model_checking(model, property[0])
        initial_state = model.initial_states[0]
        print("number of states: {}".format(len(model.states)))
        print("number of transitions: {}".format(transitions_count(model)))
        print(result.at(initial_state))

    # start simplifying the model, convert to pcfp first
    # here we leave undef constants undefined

    pcfp = PCFP.from_jani(jani_model)

    mgr: sp.ExpressionManager = pcfp.get_manager()
    s = mgr.get_variable("s")
    srep = mgr.get_variable("srep")
    r = mgr.get_variable("r")
    rrep = mgr.get_variable("rrep")
    r_ab = mgr.get_variable("r_ab")
    s_ab = mgr.get_variable("s_ab")
    bs = mgr.get_variable("bs")
    br = mgr.get_variable("br")
    k = mgr.get_variable("k")
    l = mgr.get_variable("l")
    pcfp.unfold(s)
    pcfp.unfold(r)
    # pcfp.unfold(br)
    # pcfp.unfold(r_ab)
    # pcfp.unfold(r)

    target_predicate = sp.Expression.Eq(s.get_expression(), mgr.create_integer(5))

    [print(cmd) for cmd in pcfp.commands]


    print("eliminable locs:")
    [print(loc) for loc in pcfp.get_eliminable_locs(target_predicate)]


    # loc_to_eliminate = [
    #     {s: mgr.create_integer(1), r: mgr.create_integer(1)},
    #     {s: mgr.create_integer(2), r: mgr.create_integer(1)}
    # ]
    loc_to_eliminate = pcfp.get_eliminable_locs(target_predicate)
    while loc_to_eliminate:
        loc = loc_to_eliminate.pop()
        print("eliminating location {} ...".format(loc))
        pcfp.eliminate_loc(loc)
        loc_to_eliminate = pcfp.get_eliminable_locs(target_predicate)
        # [print(cmd) for cmd in pcfp.commands]


    simplified_prism_str = pcfp.to_prism_string()
    print(simplified_prism_str)
    with open("tmp.prism", "w") as f:
        f.write(simplified_prism_str)

    simplified_prism = sp.parse_prism_program("tmp.prism")
    jani_model, _ = simplified_prism.to_jani([])

    # mgr = jani_model.expression_manager
    N = jani_model.get_constant("N").expression_variable
    MAX = jani_model.get_constant("MAX").expression_variable

    constant_vals = [
        {N: mgr.create_integer(100), MAX: mgr.create_integer(100)}
    ]

    for constant_val in constant_vals:
        print(constant_val)
        property_str = "P=? [ F s=5 ]"
        property = sp.parse_properties_for_jani_model(property_str, jani_model)
        jani_model_const_def = jani_model.define_constants(constant_val)
        model = sp.build_model(jani_model_const_def, property)
        result = sp.model_checking(model, property[0])
        initial_state = model.initial_states[0]
        print("number of states: {}".format(len(model.states)))
        print("number of transitions: {}".format(transitions_count(model)))
        print(result.at(initial_state))



    # model = sp.build_model(prism_program, prism_props)
    # result = sp.model_checking(model, prism_props[0])
    # initial_state = model.initial_states[0]
    # print("number of states: {}".format(len(model.states)))
    # print(result.at(initial_state))

if __name__ == "__main__":
    brp_manual_simplification()
